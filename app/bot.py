# Сам бот
import os
import logging
import asyncio
import math
from enum import Enum
import multiprocessing as mp
import csv

import time
from datetime import datetime, timedelta, timezone

from tinkoff.invest.schemas import (
    CandleInterval,
    OrderDirection,
    OrderType,
    PriceType,
    PostOrderResponse,
    TechAnalysisItem
)
from tinkoff.invest.exceptions import RequestError

import app.technical_indicators
# Для исторических свечей

import stream_client
import app_utils
from work import *
from work.functional import *
from work.exceptions import *
from work.functional import reverse_money, reverse_money_mv
from app.StopMarketQueue import StopMarketQueue
from api import crud, models
from api.database import *
from technical_indicators import *
from app import PROCESS_SWITCH

from instruments_loader import InstrumentsLoader
from candles_loader import CandlesLoader

logging.basicConfig(level=logging.WARNING, filename='logger.log', filemode='a',
                    format="%(asctime)s %(levelname)s %(message)s")
UTC_OFFSET = "Europe/Moscow"
MAXInter = 5

class DirectTrade(Enum):
    UNSPECIFIED = 0,
    BUY = 1,
    SELL = 2


class InvestBot(CandlesLoader, InstrumentsLoader):
    """
    Класс, реализующий логику торгового робота в песочнице
    """

    def __init__(self, account_id: str, correct_sum=False, cor_sum_value=0, filename='config.txt', autofill=True):
        InstrumentsLoader.__init__(self, autofill)     # Инициализируем базу и загружаем инструменты
        CandlesLoader.__init__(self, filename)

        self.market_queue = StopMarketQueue()
        self.account_id = account_id
        
        self.direct_trade = DirectTrade.UNSPECIFIED    # Направление сделки (купить/продать)
        self.profit = 0                                # Прибыль портфеля в процентах
        self.trades_list = dict()                      # Журнал сделок
        self.buy_cast_list = list([])                  # Список пар "цена покупки"-"количество лотов"
        self.__cor_sum = correct_sum
        self.__cor_sum_val = cor_sum_value             # Сумма для пополнения
        self.__last_prices = list([])                  # Список последних цен покупки
        #self.event_loop = asyncio.new_event_loop()
        self.file_path = filename
        tool_info = InvestBot.get_instrument_info(self._file_path)  # Получаем информацию об инструменте
        self.timeframe = tool_info[5]
        self.__stream_process = mp.Process(target=stream_client.setup_stream, args=[self.file_path])  # Процесс загрузки данных через Stream
        self._init_delay()

    
    def __correct_sum(self):
        balance = None
        with SandboxClient(TOKEN) as client:
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            free_money = cast_money(balance.total_amount_currencies)
            while free_money < 20000:
                self.pay_in(5000)
                balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
                free_money = cast_money(balance.total_amount_currencies)


    def pay_in(self, sum_rub: float):
        """ Пополнение счета в песочнице """
        with SandboxClient(TOKEN) as client:
            sum_trade = reverse_money_mv(sum_rub)
            client.sandbox.sandbox_pay_in(account_id=self.account_id, amount=sum_trade)  # Пополнение счета на сумму pay_sum
            print(f"\nПортфель пополнен на {sum_rub:.2f} RUB\n\n")


    def __print_candle(self, candle: models.Candle):
        """
         Метод для вывода свечи в консоль
        """
        time_m = candle.time_m.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\nOpen: {candle.open:.2f}, Close: {candle.close:.2f}, Low: {candle.low:.2f}, High: {candle.high:.2f}, Time: {time_m}\n")


    def __print_sma(self, sma_prev: TechAnalysisItem, sma_cur: TechAnalysisItem):
        """ Вывод данных о SMA в консоль """
        time_prev = sma_prev.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        time_cur = sma_cur.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        sma_prev_value = cast_money(sma_prev.signal)
        sma_cur_value = cast_money(sma_cur.signal)

        print(f'\nSMA prev time = {time_prev},  SMA prev value = {sma_prev_value:.2f}')
        print(f'SMA cur time = {time_cur},  SMA cur value = {sma_cur_value:.2f}\n')


    def check_signal(self):
        """
        Метод, проверяющий наличие торговых сигналов
        """
        tf_id = crud.get_timeframe_id(self._db, self.timeframe)
        last_candles = crud.get_candles_list(self._db, self.uid, tf_id)

        t2 = last_candles[0].time_m
        t1 = None
        tf = app_utils.get_timeframe_by_name(self.timeframe)
        #self.make_trade()
        match tf:
            case CandleInterval.CANDLE_INTERVAL_1_MIN:
                t1 = t2 - timedelta(minutes=60)
            case CandleInterval.CANDLE_INTERVAL_2_MIN:
                t1 = t2 - timedelta(minutes=120)
            case CandleInterval.CANDLE_INTERVAL_5_MIN:
                t1 = t2 - timedelta(hours=3)
            case CandleInterval.CANDLE_INTERVAL_10_MIN:
                t1 = t2 - timedelta(hours=3)
            case CandleInterval.CANDLE_INTERVAL_15_MIN:
                t1 = t2 - timedelta(hours=5)
            case CandleInterval.CANDLE_INTERVAL_30_MIN:
                t1 = t2 - timedelta(hours=12)
            case CandleInterval.CANDLE_INTERVAL_30_MIN:
                t1 = t2 - timedelta(hours=24)
            case CandleInterval.CANDLE_INTERVAL_HOUR:
                t1 = t2 - timedelta(hours=36)
            case CandleInterval.CANDLE_INTERVAL_2_HOUR:
                t1 = t2 - timedelta(days=7)
            case CandleInterval.CANDLE_INTERVAL_4_HOUR:
                t1 = t2 - timedelta(days=14)
            case CandleInterval.CANDLE_INTERVAL_DAY:
                t1 = t2 - timedelta(days=31)
            case CandleInterval.CANDLE_INTERVAL_WEEK:
                t1 = t2 - timedelta(days=31*4)
            case CandleInterval.CANDLE_INTERVAL_MONTH:
                t1 = t2 - timedelta(days=365*2)

        valuesEMA = getEMA(self.uid, t1, t2, tf, interval=SMA_INTERVAL)  # Получаем значения MA
        valuesRSI = getRSI(self.uid, t1, t2, tf, interval=RSI_INTERVAL)  # Получаем значения RSI

        # Выводим значения последних свечей и SMA в консоль для отладки
        self.__print_candle(last_candles[2])
        self.__print_candle(last_candles[1])
        self.__print_sma(valuesEMA[-2], valuesEMA[-1])
 
        sma_prev, sma_cur = cast_money(valuesEMA[-2].signal), cast_money(valuesEMA[-1].signal)
        rsiVal = cast_money(valuesRSI[-1].signal)

        if last_candles[2].close < sma_prev and last_candles[1].close > sma_cur:
            self.direct_trade = DirectTrade.BUY
        elif last_candles[2].close > sma_prev and last_candles[1].close < sma_cur:
            self.direct_trade = DirectTrade.SELL
        else:
            self.direct_trade = DirectTrade.UNSPECIFIED
            return False

        print('\nSIGNAL 1 TAKEN\n')
        valuesSMA = valuesEMA[-10:]
        size = len(valuesSMA)
        last_candles = last_candles[:-1]
        last_candles.reverse()
        if len(last_candles) > size:
            last_candles = last_candles[-size:]
        cntInter = 0
        valuesSMA[0] = cast_money(valuesSMA[0].signal)
        for i in range(1, size):
            print(f"ITERATION = {i}")
            try:
                valuesSMA[i] = cast_money(valuesSMA[i].signal)
                if last_candles[i-1].close < valuesSMA[i-1] and last_candles[i].close > valuesSMA[i]:
                    cntInter += 1
                elif last_candles[i-1].close > valuesSMA[i-1] and last_candles[i].close < valuesSMA[i]:
                    cntInter += 1
            except IndexError:
                break

        if cntInter > MAXInter:
            return False

        print('\nSIGNAL 2 TAKEN\n')

        if self.direct_trade == DirectTrade.BUY and rsiVal > 70:
            return False
        elif self.direct_trade == DirectTrade.SELL and rsiVal < 30:
            return False

        print('\nSIGNAL 3 TAKEN\n')

        return True


    def make_trade(self):
        """
        Совершение сделки
        """
        balance = None
        with SandboxClient(TOKEN) as client:
            print("BEGIN OF TRADE\n")
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id) # Инфа о портфеле
            free_money = cast_money(balance.total_amount_currencies)  # Сумма свободных денег в портфеле
            positionSize = free_money * STOP_ACCOUNT / STOP_LOSS  # Расчитываем размер позиции (сделки)

            # Определяем рыночную цену (полагая, что последняя котировка в базе является рыночным значением)
            my_timeframe_id = crud.get_timeframe_id(self._db, self.timeframe)
            last_price = crud.get_candles_list(self._db, self.uid, my_timeframe_id)
            last_price = last_price[0].close

            if last_price != 0:
                print(f"Last price = {last_price}")
            else:
                print("No last price!\n")
                exit(1)
            print(f"\nLAST PRICE = {last_price} rub/item\n")

            if last_price == 0:
                exit(1)

            print(f"\nLOT = {self._lot}\n")
            last_price = float(last_price)
            trade_price = reverse_money(last_price)  # Перевод цены из float в MoneyValue
            lot_cast = last_price * self.lot         # Цена за лот = цена * лотность
            print(f"\nLOT CAST = {lot_cast:.3f} rub/lot\n")
            lot_count = int(positionSize / lot_cast)  # Количество лотов за ордер
            direct = None                             # Направление сделки (купля/продажа)

            # Полчаем сведения о портфеле
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            total_amount_shares = cast_money(balance.total_amount_shares)
            total_amount_bonds = cast_money(balance.total_amount_bonds)
            total_amount_etf = cast_money(balance.total_amount_etf)
            free_money = cast_money(balance.total_amount_currencies)
            total_amount_portfolio = cast_money(balance.total_amount_portfolio)
            self.profit = cast_money(balance.expected_yield)

            if self.direct_trade == DirectTrade.BUY:
                direct = OrderDirection.ORDER_DIRECTION_BUY
                if free_money < positionSize:  # Если свободных денег меньше размера сделки
                    while lot_count != 0 or free_money < positionSize:
                        # Уменьшаем количество лотов либо пока размер позиции не станет посильным, 
                        # либо пока количество лотов не будет равным 0
                        lot_count -= 1
                        positionSize = lot_cast * lot_count
                    if free_money < positionSize:
                        # Информируем о недостатке средств (возможно вынести в отдельный метод для телеграм-бота)
                        print('\n-----------------------------\nNOT ENOUGH MONEY FOR BUY\n\n')
                        return
            else:
                direct = OrderDirection.ORDER_DIRECTION_SELL
                if lot_cast * lot_count > total_amount_shares:
                    print('\n-----------------------------\nNOT ENOUGH MONEY FOR SELL\n\n')
                    return
                lot_count = self.__check_buy(self.uid, lot_count, last_price) # Корректируем количество лотов на продажу, чтобы была прибыль, а не убыток
                if lot_count <= 0: # Если по итогам корректировки количество лотов на продажу = 0, отменяем сделку
                    return

            if lot_count < 0:
                lot_count = -lot_count
            if lot_count == 0:
                lot_count = 1

            # Совершаем сделку
            POResponse = client.sandbox.post_sandbox_order(instrument_id=self.uid, price=trade_price, direction=direct,
                                              account_id=self.account_id, order_type=OrderType.ORDER_TYPE_MARKET,
                                              price_type=PriceType.PRICE_TYPE_CURRENCY, quantity=lot_count)
            print("END OF TRADE\n")

            self.printPostOrderResponse(POResponse)  # Выводим информацию о сделке
            self.__save_trade(POResponse)            # Сохраняем информацию о сделке в журнал сделок

    def check_loss(self):
        """
        Критическое завершение программы при значительном убытке
        """
        if math.fabs(self.profit / 100) > STOP_ACCOUNT and self.profit < 0:
            print("CRITCAL LOSS. EXIT")
            return True
        return False


    def __save_trade(self, POResponse):
        """
        Сохранаяем данные о сделке в журнал сделок
        :param POResponse:  PostOrderResponse - ответ о статусе сделки и информацией о ней
        :return:
        """
        if POResponse.instrument_uid not in self.trades_list.keys():
            self.trades_list[POResponse.instrument_uid] = list([])

        self.trades_list[POResponse.instrument_uid].append(dict())
        self.trades_list[POResponse.instrument_uid][-1]['time'] = POResponse.response_metadata.server_time
        self.trades_list[POResponse.instrument_uid][-1]['direct'] = POResponse.direction
        self.trades_list[POResponse.instrument_uid][-1]['cast_order'] = cast_money(POResponse.executed_order_price)
        self.trades_list[POResponse.instrument_uid][-1]['count'] = POResponse.lots_executed
        self.trades_list[POResponse.instrument_uid][-1]['commision'] = cast_money(POResponse.executed_commission)


    def __check_buy(self, uid, lot_count, last_price):
        """
        Метод, проверяющий потенциальную прибыль/риск от сделки
        :param uid: UID инструмента
        :param lot_count: Запрашиваемое количество лотов на продажу
        :param last_price: Цена по рынку
        """

        portfolio = None
        pos = None
        with SandboxClient(TOKEN) as client:
            portfolio = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
        for position in portfolio.positions:
            if position.instrument_uid == uid:
                pos = position
        lot_pos = int(cast_money(pos.quantity) / self.lot)   # Количество лотов актива X
        if lot_pos < lot_count:
            lot_count = lot_pos
        if lot_count == 0:
            return lot_count

        # 5. Проверяем сделки от текущей k до 0 по этой акции. Заводим счетчик cntShares = K
        cntShares = lot_count             # Количество лотов на момент проверки сделки
        cur_trade = len(self.trades_list[uid]) - 1 # Стартуем с N-1 сделки
        while cntShares > 0 and cur_trade >= 0:
            if self.trades_list[uid][cur_trade]['direct'] == OrderDirection.ORDER_DIRECTION_BUY:
                cntShares -= self.trades_list[uid][cur_trade]['count']
                buy_pair = list([self.trades_list[uid][cur_trade]['cast_order'], self.trades_list[uid][cur_trade]['count']])
                buy_pair.append(self.trades_list[uid][cur_trade]['commision'])
                self.buy_cast_list.append(buy_pair)
            elif self.trades_list[uid][cur_trade]['direct'] == OrderDirection.ORDER_DIRECTION_SELL:
                cntShares += self.trades_list[uid][cur_trade]['count']


        request_lots, request_sum = 0, 0
        buy_com = 0
        if not self.buy_cast_list or not self.buy_cast_list[-1][2]:
            buy_com = 0
        else:
            buy_com = self.buy_cast_list[-1][2]
        size = len(self.buy_cast_list)
        for i in range(size-1, -1, -1):
            if i < 0:
                break
            lots = self.buy_cast_list[i][1]
            while lots != 0 and request_lots != lot_count:
                lots -= 1
                request_lots += 1
                request_sum += self.buy_cast_list[i][0] * self.lot
                self.__last_prices.append(self.buy_cast_list[i][0])
        
        # Рассчитываем потенциальную прибыль с учетом комиссии
        k = lot_count
        if lot_count > request_lots and request_lots != 0:
            k = request_lots
        profit = (k * last_price - request_sum) - (buy_com + 0.0005 * k * last_price)
        while profit <= 0 and k > 0:
            # Пока со сделки наблюдается убыток, уменьшаем возможное количество лотов
            k -= 1
            profit = (k * last_price - request_sum) - (buy_com + 0.0005 * k * last_price)

        return k    # Возвращаем итоговое количество лотов на продажу 
        

    def printPostOrderResponse(self, POResponse: PostOrderResponse):
        print('\nINFO ABOUT TRADE\n-----------------------------------------------------\n')
        direct_str = ''
        order_type = ''
        match POResponse.direction:
            case OrderDirection.ORDER_DIRECTION_BUY:
                print("Direct of trade = BUY")
                direct_str = 'BUY'
            case OrderDirection.ORDER_DIRECTION_SELL:
                print("Direct of trade = SELL")
                direct_str = 'SELL'
        print(f"Executed order price = {POResponse.executed_order_price}")
        print(f"Executed commission = {POResponse.executed_commission}")
        print(f"UID instrument = {POResponse.instrument_uid}")
        print(f"Requested lots = {POResponse.lots_requested}")
        print(f"Executed lots = {POResponse.lots_executed}")
        match POResponse.order_type:
            case OrderType.ORDER_TYPE_MARKET:
                print(f"Order type = MARKET")
                order_type = 'MARKET'
            case OrderType.ORDER_TYPE_LIMIT:
                print(f"Order type = LIMIT")
                order_type = 'LIMIT'
            case OrderType.ORDER_TYPE_BESTPRICE:
                print(f"Order type = BESTPRICE")
                order_type = 'BESTPRICE'
        print(f"Total order amount = {POResponse.total_order_amount}\n\n")
        print(f"Tracking id = {POResponse.response_metadata.tracking_id}")
        server_time = POResponse.response_metadata.server_time.strftime('%Y-%m-%d_%H:%M:%S')
        print(f"Time of trade = {server_time}")
        data_csv = list([POResponse.instrument_uid, str(cast_money(POResponse.executed_order_price)),
                         str(cast_money(POResponse.executed_commission)),
                         str(POResponse.instrument_uid), str(POResponse.lots_requested),
                         str(POResponse.lots_executed), order_type, direct_str,
                         str(cast_money(POResponse.total_order_amount)),
                         POResponse.response_metadata.tracking_id, server_time])

        instrument_uid = str(POResponse.instrument_uid)
        ticker = 'lol'
        instrument = crud.get_instrument(self._db, instrument_uid)
        ticker = instrument.ticker

        file_trades = "C:\\Users\\User\\PycharmProjects\\teleBotTest\\app\\trades_stat"
        filename = self.get_full_filename(file_trades, ticker)
        if os.path.exists(filename):
            with open(filename, 'a') as csv_file:
                writer = csv.writer(csv_file, delimiter=';')
                writer.writerow(data_csv)
        else:
            with open(filename, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=';')
                writer.writerow(data_csv)


    def printPortfolio(self):
        print("MY PORTFOLIO\n-----------------------------------\n")
        with SandboxClient(TOKEN) as client:
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            total_amount_shares = cast_money(balance.total_amount_shares)
            total_amount_bonds = cast_money(balance.total_amount_bonds)
            total_amount_etf = cast_money(balance.total_amount_etf)
            free_money = cast_money(balance.total_amount_currencies)
            total_amount_portfolio = cast_money(balance.total_amount_portfolio)
            self.profit = cast_money(balance.expected_yield)
            server_time = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H:%M:%S')
            data_csv = list([str(total_amount_portfolio), str(free_money),
                             str(self.profit), str(total_amount_shares),
                             str(total_amount_bonds), str(total_amount_etf), server_time])

            print(f"Free money = {free_money} RUB")
            print(f"Total amount shares = {total_amount_shares} RUB")
            print(f"Total amount portfolio = {total_amount_portfolio} RUB")
            print(f"Profit/Unprofit = {self.profit} %\n")
            print(f"Time = {server_time}")
            print("Positions\n-----------------------------------")
            
            for position in balance.positions:
                instrument_uid = position.instrument_uid
                position_uid = position.position_uid
                figi = position.figi
                instrument_type = position.instrument_type
                ticker = ''
                count = cast_money(position.quantity)
                cur_price = cast_money(position.current_price)
                count_lots = cast_money(position.quantity_lots)
                profit = cast_money(position.expected_yield)

                instrument = crud.get_instrument(self._db, instrument_uid)
                name = None
                if instrument:
                    name = instrument.name
                    ticker = instrument.ticker
                else:
                    currency = crud.get_currency_by_uid(self._db, instrument_uid)
                    if currency:
                        name = currency.name
                        ticker = currency.ticker

                print(f"Instrument UID = {instrument_uid}")
                print(f"Position UID = {position_uid}")
                print(f"FIGI = {figi}")
                if ticker:
                    print(f"TICKER = {ticker}")
                if name:
                    print(f"Name = {name}")
                print(f"Instrument type = {instrument_type}")
                print(f"Quantity = {count}")
                print(f"Current price = {cur_price:.2f}")
                print(f"Count of lots = {count_lots}")
                print(f"Profit/Unprofit = {profit} %\n")
            print('\n---------------------------------------------------\n---------------------------------------------\n')

            filename = "C:\\Users\\User\\PycharmProjects\\teleBotTest\\app\\porfolio_stat"
            filename = self.get_full_filename(filename, ticker)
            if os.path.exists(filename):
                with open(filename, 'a') as csv_file:
                    writer = csv.writer(csv_file, delimiter=';')
                    writer.writerow(data_csv)
            else:
                with open(filename, 'w') as csv_file:
                    writer = csv.writer(csv_file, delimiter=';')
                    writer.writerow(data_csv)


    def get_full_filename(self, filename: str, ticker: str):
        filename = filename + '_' + ticker + '_' + self.timeframe + '.csv'
        return filename

    def run(self):
        """ Главный цикл торгового робота """
        last_time = self._check_last_candles(self._db)
        if isinstance(last_time, datetime):
            # Если check_last_candles() вернул datetime-объект, значит у нас значительный разрыв по времени, требуется
            # еще подгрузка
            self._load_candles(self._db, last_time)

        if not self.__cor_sum:      # Если не стоит флаг коррекции суммы
            self.__correct_sum()
        else:
            self.pay_in(self.__cor_sum_val)
        #self.buy_shares()

        self.__stream_process.start()   # (**) Запускаем процесс загрузки данных через Stream

        while True:
            self.printPortfolio()
            if self.check_loss():                     # Если у нас потери превысили риск
                self.__stream_process.terminate()     # Завершаем процесс стрима
                print('\nStream process terminated')
                print('Session was exited')
                return                                # Выходим из функции
            if self.check_signal():
                self.make_trade()
            time.sleep(self._delay)