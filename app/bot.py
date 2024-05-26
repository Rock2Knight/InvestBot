# Сам бот
import sys
import os
from dotenv import load_dotenv
import logging
import asyncio
import math
import multiprocessing as mp
import csv
import time
from datetime import datetime, timedelta, timezone

from tinkoff.invest import RequestError
from tinkoff.invest.schemas import (
    CandleInterval,
    OrderDirection,
    OrderType,
    PriceType,
    PostOrderResponse,
    TechAnalysisItem
)

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)
sys.path.append(main_path+'app/')

#import app.technical_indicators
# Для исторических свечей
import stream_client

from app.StopMarketQueue import StopMarketQueue
from api import crud, models
from api.database import *
from technical_indicators import *

from config import program_config
from utils_funcs import utils_funcs

from instruments_loader import InstrumentsLoader
from candles_loader import CandlesLoader
from StopMarketQueue import StopMarketQueue

logging.basicConfig(level=logging.INFO, filename='test_bot_log.log', filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")
UTC_OFFSET = "Europe/Moscow"

__all__ = ['InvestBot']


class InvestBot(CandlesLoader, InstrumentsLoader):
    """
    Класс, реализующий логику торгового робота в песочнице
    """

    def __init__(self, account_id: str, correct_sum=False, cor_sum_value=0, filename='../settings.ini', autofill=True):
        # Ожидаемая доходность, риск, СТОП-ЛОСС, ТЕЙК-ПРОФИТ
        config = program_config.ProgramConfiguration(filename)
        self.__token = os.getenv('TINKOFF_TOKEN')

        self._user_return = config.user_return
        self._user_risk = config.user_risk

        InstrumentsLoader.__init__(self, autofill)     # Инициализируем базу и загружаем инструменты
        CandlesLoader.__init__(self, filename)

        self.market_queue = StopMarketQueue()
        self.account_id = account_id
        
        self.direct_trade = dict()    # Направление сделки (купить/продать)
        self.profit = 0                                # Прибыль портфеля в процентах
        self.trades_list = dict()                      # Журнал сделок
        self.buy_cast_list = list([])                  # Список пар "цена покупки"-"количество лотов"
        self.__cor_sum = correct_sum
        self.__cor_sum_val = cor_sum_value             # Сумма для пополнения
        self.__last_prices = list([])                  # Список последних цен покупки
        self.__sl_queue = StopMarketQueue()            # Очередь стоп-лосс заявок
        self.__tp_queue = StopMarketQueue()            # Очередь тейк-профит заявок
        self.file_path = filename
        self.timeframe = config.timeframe
        self.__stream_process = mp.Process(target=stream_client.setup_stream, args=[config])  # Процесс загрузки данных через Stream
        self._init_delay()

    def __correct_sum(self):
        balance = None
        with SandboxClient(self.__token) as client:
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            free_money = utils_funcs.cast_money(balance.total_amount_currencies)
            while free_money < 20000:
                self.pay_in(5000)
                balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
                free_money = utils_funcs.cast_money(balance.total_amount_currencies)


    def is_trade_available(self, uid: str) -> bool:
        """
        Проверяет, доступен интсрумент с UID = uid для торговли
        :param uid: UID торгового инструмента
        :return: True - доступен, False - нет
        """

        resp = None
        with SandboxClient(self.__token) as client:
            resp = client.market_data.get_trading_status(instrument_id=uid)
            market_access = resp.market_order_available_flag
            api_access = resp.api_trade_available_flag
            if market_access and api_access:
                return True
            else:
                return False


    def pay_in(self, sum_rub: float):
        """ Пополнение счета в песочнице """
        with SandboxClient(self.__token) as client:
            sum_trade = utils_funcs.reverse_money_mv(sum_rub)
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
        sma_prev_value = utils_funcs.cast_money(sma_prev.signal)
        sma_cur_value = utils_funcs.cast_money(sma_cur.signal)

        print(f'\nSMA prev time = {time_prev},  SMA prev value = {sma_prev_value:.2f}')
        print(f'SMA cur time = {time_cur},  SMA cur value = {sma_cur_value:.2f}\n')


    @utils_funcs.invest_api_retry()
    def check_signal(self, uid: str, ma_interval: int, rsi_interval: int, max_inter: int):
        """
        Метод, проверяющий наличие торговых сигналов
        """
        tf_id = crud.get_timeframe_id(self._db, self.timeframe)
        last_candles = crud.get_candles_list(self._db, uid, tf_id)

        if not last_candles:
            raise ValueError
        t2 = last_candles[0].time_m
        t1 = None
        tf = utils_funcs.get_timeframe_by_name(self.timeframe)
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

        valuesEMA = getEMA(uid, t1, t2, tf, interval=ma_interval)  # Получаем значения MA
        valuesRSI = getRSI(uid, t1, t2, tf, interval=rsi_interval)  # Получаем значения RSI

        # Выводим значения последних свечей и SMA в консоль для отладки
        self.__print_candle(last_candles[1])
        self.__print_candle(last_candles[0])
        self.__print_sma(valuesEMA[0], valuesEMA[1])
 
        last_price = last_candles[1].close
        with SandboxClient(self.__token) as client:
            last_prices_resp = client.market_data.get_last_prices(instrument_id=[uid])  # Получаем цены по рынку
            trade_price = last_prices_resp.last_prices[0].price
            last_price = utils_funcs.cast_money(trade_price)

        sma_prev, sma_cur = utils_funcs.cast_money(valuesEMA[0].signal), utils_funcs.cast_money(valuesEMA[1].signal)
        rsiVal = utils_funcs.cast_money(valuesRSI[1].signal)

        if last_candles[1].close < sma_prev and last_price > sma_cur:
            self.direct_trade[uid] = OrderDirection.ORDER_DIRECTION_BUY
        elif last_candles[1].close > sma_prev and last_price < sma_cur:
            self.direct_trade[uid] = OrderDirection.ORDER_DIRECTION_SELL
        else:
            self.direct_trade[uid] = OrderDirection.ORDER_DIRECTION_UNSPECIFIED
            return False

        print('\nSIGNAL 1 TAKEN\n')
        valuesSMA = valuesEMA[-10:]
        size = len(valuesSMA)
        last_candles = last_candles[:-1]
        last_candles.reverse()
        if len(last_candles) > size:
            last_candles = last_candles[-size:]
        cntInter = 0
        valuesSMA[0] = utils_funcs.cast_money(valuesSMA[0].signal)
        for i in range(1, size):
            print(f"ITERATION = {i}")
            try:
                valuesSMA[i] = utils_funcs.cast_money(valuesSMA[i].signal)
                if last_candles[i-1].close < valuesSMA[i-1] and last_candles[i].close > valuesSMA[i]:
                    cntInter += 1
                elif last_candles[i-1].close > valuesSMA[i-1] and last_candles[i].close < valuesSMA[i]:
                    cntInter += 1
            except IndexError:
                break

        if cntInter > max_inter:
            return False

        print('\nSIGNAL 2 TAKEN\n')

        if self.direct_trade == OrderDirection.ORDER_DIRECTION_BUY and rsiVal > 70:
            return False
        elif self.direct_trade == OrderDirection.ORDER_DIRECTION_SELL and rsiVal < 30:
            return False

        print('\nSIGNAL 3 TAKEN\n')

        return True


    def get_free_money(self):
        balance, free_money = None, None
        with SandboxClient(self.__token) as client:
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
        free_money = utils_funcs.cast_money(balance.total_amount_currencies)
        return free_money


    async def make_trade(self, ticker: str, info: dict):
        """
        Совершение сделки
        """

        balance = None
        with SandboxClient(self.__token) as client:
            print("BEGIN OF TRADE\n")
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id) # Инфа о портфеле
            free_money = utils_funcs.cast_money(balance.total_amount_currencies)  # Сумма свободных денег в портфеле
            positionSize = free_money * self._user_risk / info['stop_loss']  # Расчитываем размер позиции (сделки)

            # Определяем рыночную цену (полагая, что последняя котировка в базе является рыночным значением)
            my_timeframe_id = crud.get_timeframe_id(self._db, self.timeframe)

            last_prices_resp = client.market_data.get_last_prices(instrument_id=[info['uid']])  # Получаем цены по рынку
            trade_price = last_prices_resp.last_prices[0].price
            last_price = utils_funcs.cast_money(trade_price)

            if last_price != 0:
                print(f"{ticker} Last price = {last_price}")
                logging.info(f"{ticker} Last price = {last_price}")
            else:
                print(f"{ticker} No last price!\n")
                logging.info(f"{ticker} No last price!\n")
                exit(1)
            print(f"\n{ticker} LAST PRICE = {last_price} rub/item\n")
            logging.info(f"\n{ticker} LAST PRICE = {last_price} rub/item\n")

            if last_price == 0:
                exit(1)

            lot = self.get_lot(self.db, info['uid'])
            print(f"\n{ticker} LOT = {lot}\n")
            last_price = float(last_price)
            trade_price = utils_funcs.reverse_money(last_price)  # Перевод цены из float в MoneyValue
            lot_cast = last_price * lot         # Цена за лот = цена * лотность
            print(f"\n{ticker} LOT CAST = {lot_cast:.3f} rub/lot\n")
            lot_count = int(positionSize / lot_cast)  # Количество лотов за ордер
            direct = None                             # Направление сделки (купля/продажа)

            # Полчаем сведения о портфеле
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            total_amount_shares = utils_funcs.cast_money(balance.total_amount_shares)
            total_amount_bonds = utils_funcs.cast_money(balance.total_amount_bonds)
            total_amount_etf = utils_funcs.cast_money(balance.total_amount_etf)
            free_money = utils_funcs.cast_money(balance.total_amount_currencies)
            total_amount_portfolio = utils_funcs.cast_money(balance.total_amount_portfolio)
            self.profit = utils_funcs.cast_money(balance.expected_yield)
            weight_sum = info['weight'] * free_money # Максимальная доля актива в портфеле в рублях

            if self.direct_trade[info['uid']] == OrderDirection.ORDER_DIRECTION_BUY:
                direct = OrderDirection.ORDER_DIRECTION_BUY
                if free_money < positionSize:  # Если свободных денег меньше размера сделки
                    while lot_count != 0 or free_money < positionSize or weight_sum - positionSize <= 0:
                        # Уменьшаем количество лотов либо пока размер позиции не станет посильным, 
                        # либо пока количество лотов не будет равным 0
                        lot_count -= 1
                        positionSize = lot_cast * lot_count
                    if free_money < positionSize:
                        # Информируем о недостатке средств (возможно вынести в отдельный метод для телеграм-бота)
                        print('\n-----------------------------\nNOT ENOUGH MONEY FOR BUY\n\n')
                        logging.info('\n-----------------------------\nNOT ENOUGH MONEY FOR BUY\n\n')
                        return
                    if lot_count <= 0:
                        lot_count = 1
            else:
                direct = OrderDirection.ORDER_DIRECTION_SELL
                if lot_cast * lot_count > total_amount_shares:
                    while lot_cast * lot_count > total_amount_shares:
                        lot_count -= 1
                while free_money + (lot_count * lot_cast) * 0.97 > weight_sum:
                    lot_count -= 1
                if lot_count <= 0:
                    print('\n-----------------------------\nNOT ENOUGH MONEY FOR SELL\n\n')
                    logging.info('\n-----------------------------\nNOT ENOUGH MONEY FOR SELL\n\n')
                    return
                '''
                lot_count = self.__check_buy(self.uid, lot_count, last_price) # Корректируем количество лотов на продажу, чтобы была прибыль, а не убыток
                if lot_count <= 0: # Если по итогам корректировки количество лотов на продажу = 0, отменяем сделку
                    return
                '''

            '''
            if lot_count < 0:
                lot_count = -lot_count
            if lot_count == 0:
                lot_count = 1
            '''

            if lot_count >= 0:
                sl_cast = last_price * (1 - info['stop_loss']) # Расчет стоп-лосс цены
                tp_cast = last_price * (1 + info['take_profit']) # Расчет тейк-профит цены
                task1 = asyncio.create_task(self.__sl_queue.push(sl_cast, lot_count))
                task2 = asyncio.create_task(self.__tp_queue.push(tp_cast, lot_count))
                tasks = [task1, task2]
                asyncio.gather(*tasks)
                done, pending = await asyncio.wait(tasks)
                if pending:
                    raise Exception('Markets were not detected')

            if not self.is_trade_available(info['uid']):
                return      # Если инструмент не доступен для торгов, отменяем сделку
            if lot_count <= 0:
                return

            # Совершаем сделку
            POResponse = self.real_trade(info['uid'], trade_price, direct, self.account_id,
                                         OrderType.ORDER_TYPE_MARKET, PriceType.PRICE_TYPE_CURRENCY, lot_count)
            print("END OF TRADE\n")

            await self.printPostOrderResponse(POResponse)  # Выводим информацию о сделке
            self.__save_trade(POResponse)            # Сохраняем информацию о сделке в журнал сделок


    async def async_trade(self, ticker: str, info: dict):
        """
        Проверка сигнала и совершение сделки
        """
        if self.check_signal(info['uid'], info['ma_interval'], info['rsi_interval'], info['max_inter']):
            await self.make_trade(ticker, info)


    def real_trade(self, *args):
        with SandboxClient(self.__token) as client:
            try:
                POResponse = client.sandbox.post_sandbox_order(instrument_id=args[0], price=args[1], direction=args[2],
                                                       account_id=args[3],
                                                       order_type=args[4],
                                                       price_type=args[5], quantity=args[6])
            except Exception as e:
                if args[6] <= 0:
                    print(f"Quantity = {args[6]}")
                    print('lol')
                    raise e
            return POResponse


    def get_instrument_by_uid(self, uid: str, assets):
        for asset in assets:
            if asset.instrument_uid == uid:
                return asset


    async def stop_market_complete(self, uid: str) -> bool:
        """
        Метод, проверяющий стоп-маркет заявку для торгового инструмента, и исполняющий ее при необходимости
        :param uid: UID инструмента
        :return: True, если заявка исполнена, иначе False
        """

        flag = False
        sl = self.__sl_queue.get() # Получаем данные о стоп-лосс заявке
        tp = self.__tp_queue.get() # Получаем данные о тейк-профит заявке
        if not sl or not tp:
            print("NO ORDERS IN QUEUE")
            return False

        sl_stop_market, sl_lot_count = sl[0], sl[1]
        tp_stop_market, tp_lot_count = tp[0], tp[1]
        max_lot_count = None
        last_price, trade_price = None, None

        with SandboxClient(self.__token) as client:
            last_prices_resp = client.market_data.get_last_prices(instrument_id=[uid]) # Получаем цены по рынку
            trade_price = last_prices_resp.last_prices[0].price
            last_price = utils_funcs.cast_money(trade_price)
            positions = client.operations.get_positions(account_id=self.account_id)
            target_position = self.get_instrument_by_uid(uid, positions.securities)
            try:
                max_lot_count = target_position.balance
            except Exception as e:
                return False

        lot_count = 1

        if last_price <= sl_stop_market:
            # Совершаем сделку STOP-LOSS
            flag = True
            if sl_lot_count <= 0 or sl_lot_count >= max_lot_count:
                print("LOT COUNT MORE THAN YOU HAVE")
                return False
            sl_stop_market, sl_lot_count = self.__sl_queue.pop() # Получаем данные о стоп-лосс заявке
            lot_count = sl_lot_count
            print("BEGIN OF STOP-LOSS TRADE\n")
            logging.info("BEGIN OF STOP-LOSS TRADE\n")
        elif last_price >= tp_stop_market:
            # Совершаем сделку TAKE-PROFIT
            flag = True
            if tp_lot_count <= 0 or tp_lot_count >= max_lot_count:
                return False
            tp_stop_market, tp_lot_count = self.__tp_queue.pop() # Получаем данные о стоп-лосс заявке
            lot_count = tp_lot_count
            print("BEGIN OF TAKE-PROFIT TRADE\n")
            logging.info("BEGIN OF TAKE-PROFIT TRADE\n")

        if not flag:
            print("LAST PRICE NOT EQUAL STOP-MARKET")
            return False
        if not self.is_trade_available(uid):
            return False      # Если инструмент не доступен для торгов, отменяем сделку
        if lot_count <= 0:
            return False
        direct = OrderDirection.ORDER_DIRECTION_SELL
        POResponse = self.real_trade(uid, trade_price, direct, self.account_id,
                                     OrderType.ORDER_TYPE_MARKET, PriceType.PRICE_TYPE_CURRENCY, lot_count)
        await self.printPostOrderResponse(POResponse)  # Выводим информацию о сделке
        return True

    def check_loss(self):
        """
        Критическое завершение программы при значительном убытке
        """
        if math.fabs(self.profit / 100) > self._user_risk and self.profit < 0:
            print("CRITCAL LOSS. EXIT")
            logging.info("CRITCAL LOSS. EXIT")
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
        self.trades_list[POResponse.instrument_uid][-1]['cast_order'] = utils_funcs.cast_money(POResponse.executed_order_price)
        self.trades_list[POResponse.instrument_uid][-1]['count'] = POResponse.lots_executed
        self.trades_list[POResponse.instrument_uid][-1]['commision'] = utils_funcs.cast_money(POResponse.executed_commission)


    def __check_buy(self, uid, lot_count, last_price):
        """
        Метод, проверяющий потенциальную прибыль/риск от сделки
        :param uid: UID инструмента
        :param lot_count: Запрашиваемое количество лотов на продажу
        :param last_price: Цена по рынку
        """

        portfolio = None
        pos = None
        with SandboxClient(self.__token) as client:
            portfolio = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
        for position in portfolio.positions:
            if position.instrument_uid == uid:
                pos = position
        lot_pos = int(utils_funcs.cast_money(pos.quantity) / self._lot)   # Количество лотов актива X
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
                request_sum += self.buy_cast_list[i][0] * self._lot
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
        

    async def printPostOrderResponse(self, POResponse: PostOrderResponse):
        print('\nINFO ABOUT TRADE\n-----------------------------------------------------\n')
        logging.info('\nINFO ABOUT TRADE\n-----------------------------------------------------\n')
        direct_str = ''
        order_type = ''
        match POResponse.direction:
            case OrderDirection.ORDER_DIRECTION_BUY:
                print("Direct of trade = BUY")
                logging.info("Direct of trade = BUY")
                direct_str = 'BUY'
            case OrderDirection.ORDER_DIRECTION_SELL:
                print("Direct of trade = SELL")
                logging.info("Direct of trade = SELL")
                direct_str = 'SELL'
        print(f"Executed order price = {POResponse.executed_order_price}")
        logging.info(f"Executed order price = {POResponse.executed_order_price}")
        print(f"Executed commission = {POResponse.executed_commission}")
        logging.info(f"Executed commission = {POResponse.executed_commission}")
        print(f"UID instrument = {POResponse.instrument_uid}")
        logging.info(f"UID instrument = {POResponse.instrument_uid}")
        print(f"Requested lots = {POResponse.lots_requested}")
        logging.info(f"Requested lots = {POResponse.lots_requested}")
        print(f"Executed lots = {POResponse.lots_executed}")
        logging.info(f"Executed lots = {POResponse.lots_executed}")
        match POResponse.order_type:
            case OrderType.ORDER_TYPE_MARKET:
                print(f"Order type = MARKET")
                logging.info(f"Order type = MARKET")
                order_type = 'MARKET'
            case OrderType.ORDER_TYPE_LIMIT:
                print(f"Order type = LIMIT")
                order_type = 'LIMIT'
            case OrderType.ORDER_TYPE_BESTPRICE:
                print(f"Order type = BESTPRICE")
                order_type = 'BESTPRICE'
        print(f"Total order amount = {POResponse.total_order_amount}\n\n")
        logging.info(f"Total order amount = {POResponse.total_order_amount}\n\n")
        print(f"Tracking id = {POResponse.response_metadata.tracking_id}")
        logging.info(f"Tracking id = {POResponse.response_metadata.tracking_id}")
        server_time = POResponse.response_metadata.server_time.strftime('%Y-%m-%d_%H:%M:%S')
        print(f"Time of trade = {server_time}")
        logging.info(f"Time of trade = {server_time}")
        data_csv = list([POResponse.instrument_uid, str(utils_funcs.cast_money(POResponse.executed_order_price)),
                         str(utils_funcs.cast_money(POResponse.executed_commission)),
                         str(POResponse.instrument_uid), str(POResponse.lots_requested),
                         str(POResponse.lots_executed), order_type, direct_str,
                         str(utils_funcs.cast_money(POResponse.total_order_amount)),
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


    async def printPortfolio(self):
        print("MY PORTFOLIO\n-----------------------------------\n")
        with SandboxClient(self.__token) as client:
            balance = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            total_amount_shares = utils_funcs.cast_money(balance.total_amount_shares)
            total_amount_bonds = utils_funcs.cast_money(balance.total_amount_bonds)
            total_amount_etf = utils_funcs.cast_money(balance.total_amount_etf)
            free_money = utils_funcs.cast_money(balance.total_amount_currencies)
            total_amount_portfolio = utils_funcs.cast_money(balance.total_amount_portfolio)
            self.profit = utils_funcs.cast_money(balance.expected_yield)
            server_time = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H:%M:%S')
            data_csv = list([str(total_amount_portfolio), str(free_money),
                             str(self.profit), str(total_amount_shares),
                             str(total_amount_bonds), str(total_amount_etf), server_time])

            print(f"Free money = {free_money} RUB")
            logging.info(f"Free money = {free_money} RUB")
            print(f"Total amount shares = {total_amount_shares} RUB")
            logging.info(f"Total amount shares = {total_amount_shares} RUB")
            print(f"Total amount portfolio = {total_amount_portfolio} RUB")
            logging.info(f"Total amount portfolio = {total_amount_portfolio} RUB")
            print(f"Profit/Unprofit = {self.profit} %\n")
            logging.info(f"Profit/Unprofit = {self.profit} %\n")
            print(f"Time = {server_time}")
            logging.info(f"Time = {server_time}")
            print("Positions\n-----------------------------------")
            logging.info("Positions\n-----------------------------------")
            
            for position in balance.positions:
                instrument_uid = position.instrument_uid
                position_uid = position.position_uid
                figi = position.figi
                instrument_type = position.instrument_type
                ticker = ''
                count = utils_funcs.cast_money(position.quantity)
                cur_price = utils_funcs.cast_money(position.current_price)
                count_lots = utils_funcs.cast_money(position.quantity_lots)
                profit = utils_funcs.cast_money(position.expected_yield)

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
                logging.info(f"Instrument UID = {instrument_uid}")
                print(f"Position UID = {position_uid}")
                logging.info(f"Position UID = {position_uid}")
                print(f"FIGI = {figi}")
                logging.info(f"FIGI = {figi}")
                if ticker:
                    print(f"TICKER = {ticker}")
                    logging.info(f"TICKER = {ticker}")
                if name:
                    print(f"Name = {name}")
                    logging.info(f"Name = {name}")  
                print(f"Instrument type = {instrument_type}")
                logging.info(f"Instrument type = {instrument_type}")
                print(f"Quantity = {count}")
                logging.info(f"Quantity = {count}")
                print(f"Current price = {cur_price:.2f}")
                logging.info(f"Current price = {cur_price:.2f}")
                print(f"Count of lots = {count_lots}")
                logging.info(f"Count of lots = {count_lots}")
                print(f"Profit/Unprofit = {profit} %\n")
                logging.info(f"Profit/Unprofit = {profit} %\n")
            print('\n---------------------------------------------------\n---------------------------------------------\n')
            logging.info('\n---------------------------------------------------\n---------------------------------------------\n')

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

    async def pre_run(self) -> bool:
        event_loop = asyncio.new_event_loop()
        last_time_dict = self._check_last_candles(self._db)
        tasks = list([])
        if last_time_dict:
            for uid, param in last_time_dict.items():
                task = asyncio.create_task(self._load_candles(self._db, uid, param))
                tasks.append(task)
            done, pending = await asyncio.wait(tasks)
            if not pending:
                return True
            else:
                raise ValueError
        return True

    @utils_funcs.invest_api_retry(retry_count=10)
    async def run(self):
        """ Главный цикл торгового робота """
        is_loaded = await self.pre_run()
        while not is_loaded:
            continue

        if self.__cor_sum:      # Если не стоит флаг коррекции суммы
            self.__correct_sum()

        self.__stream_process.start()   # (**) Запускаем процесс загрузки данных через Stream

        while True:
            await self.printPortfolio()
            if self.check_loss():                     # Если у нас потери превысили риск
                self.__stream_process.terminate()     # Завершаем процесс стрима
                print('\nStream process terminated')
                print('Session was exited')
                return                                # Выходим из функции
            for ticker, info in self.strategies.items():
                await self.async_trade(ticker, info)
                await self.stop_market_complete(info['uid'])
            time.sleep(30)