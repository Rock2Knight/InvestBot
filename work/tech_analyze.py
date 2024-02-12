# Модуль отладки инструментов тех. анализа
from math import floor
from datetime import datetime
import pandas as pd

from MA_indicator import SMA_indicator

def getDateNow():
    cur_time = datetime.now()
    print(cur_time)


# Цикл, моделирующий торговлю
def run_main():
    figi = 'BBG00475KKY8'  # Фиги торгуемого инструемента (Новатэк)
    active_cast = 0        # Текущая цена актива
    lot = 1  # лотность инструмента
    cnt_lots = 1000  # Количество лотов Новатэк в портфеле
    account_portfolio = 100000.00  # Размер портфеля в рублях
    start_sum = account_portfolio
    ma_interval = 5

    # Условия расчета позиции
    stopAccount = 0.01  # Риск для счета в процентах
    stopLoss = 0.05     # Точка аннулирования для торговой стратегии в процентах

    CandlesDF = pd.read_csv("../share_history.csv")       # 1. Получаем готовый датафрейм исторических свечей
    SMA_5 = SMA_indicator(MA_interval=ma_interval, CandlesDF=CandlesDF)
    MAXInter = 3                                          # Max количество пересечений на интервал
    CNT_timeframe = 10                                    # Длина проверяемого интервала
    cntInter = 0                                          # Количество пересечений
    lot_cast = CandlesDF.iloc[0]['close']  # Рыночная цена одного лота (типа)
    positionSize = 0.0                                    # Размер позиции
    totalSharePrice = lot_cast * cnt_lots                 # Общая стоимость акций Новатэк в портфеле
    cnt_tradeLots = 0

    print("INFO\n-------------\n\nStart sum on account: %.2f RUB " % start_sum +
          f"\nTime: {CandlesDF.iloc[0]['time']}" +
          "\nStart count of NOVATEK lots: " + str(cnt_lots) +
          "\nCast per NOVATEK lot: %.2f RUB" % lot_cast +
          "\nTotal instrument price: %.2f RUB" % floor(totalSharePrice) +
          "\nAccountant max loss: %.2f" % stopAccount +
          "\nStop loss: %.2f\n" % stopLoss +
          "--------------------------\n")

    # Анализируем свечи из выделенного интервала
    for i in range(CandlesDF.shape[0]):
        BUY_Signal = False
        SELL_Signal = False

        # Вывод информации об аккаунте
        print("INFO ABOUT ACCOUNT\n--------------------------\n" +
              f"\nTime: {CandlesDF.iloc[i]['time']}" +
              "\nStart sum on account: %.2f RUB " % start_sum +
              "\nCurrent sum on account: %.2f RUB " % account_portfolio +
              "\nCurrent count of NOVATEK lots: " + str(cnt_lots) +
              "\nCast per NOVATEK lot: %.2f RUB" % lot_cast +
              "\nTotal instrument price: %.2f RUB" % floor(totalSharePrice) +
              "--------------------------\n")

        # Если количество свеч для построения SMA недостаточно, продолжаем цикл
        if i < ma_interval - 1:                                         # Если номер свечи меньше периода SMA, то просто делаем итерацию без действий
            continue

        #SMA_Values = SMA_indicator.MA_build(MA_interval=ma_interval, cntOfCandles=i+1)

        if i < 0:
            raise IndexError

        sma_prev = SMA_5.get_SMA(i - 1)
        sma_cur = SMA_5.get_SMA(i)
        BUY_Signal = CandlesDF.iloc[i - 1]['close'] < sma_prev and CandlesDF.iloc[i]['close'] > sma_cur
        SELL_Signal = CandlesDF.iloc[i - 1]['close'] > sma_prev and CandlesDF.iloc[i]['close'] < sma_cur

        if BUY_Signal or SELL_Signal:
            # Торговый сигнал  сработал, проверяем
            start_frame = 0
            if i < CNT_timeframe:
                start_frame = 0
            else:
                start_frame = i - CNT_timeframe

            for j in range(start_frame + 1, i + 1):
                # Считаем количество персечений SMA в 10 предыдущих таймфреймах
                sma_prev = SMA_5.get_SMA(j - 1)
                sma_cur = SMA_5.get_SMA(j)
                if CandlesDF.iloc[j - 1]['close'] < sma_prev and CandlesDF.iloc[j]['close'] > sma_cur:
                    cntInter += 1

            # Если количество пересечений не очень большое, то совершаем сделку
            if cntInter < MAXInter:
                positionSize = account_portfolio * stopAccount / stopLoss   # Расчитываем размер позиции (сделки)

                if BUY_Signal:
                    account_portfolio -= positionSize             # Перечисляем деньги за сделку брокеру в случае покупки
                else:
                    account_portfolio += positionSize             # Получаем деньги за сделку от брокера в случае продажи

                active_cast = CandlesDF.iloc[j]['close']  # Рыночная цена актива (типа)
                lot_cast = lot * active_cast              # Рыночная цена одного лота актива (типа)
                cnt_tradeLots = floor(positionSize / lot_cast)  # Количество покупаемых/продаваемых лотов

                if BUY_Signal:
                    cnt_lots += cnt_tradeLots  # Получаем лоты инструмента (акции Тинькофф) на счет
                else:
                    cnt_lots -= cnt_tradeLots  # Продаем лоты инструмента (акции Тинькофф) брокеру

                totalSharePrice = lot_cast * cnt_lots                       # Общая стоимость акций Тинькофф в портфеле

                # Вывод информации о сделке
                if BUY_Signal:
                    print("INFO ABOUT TRANSACTION\n--------------------------\n" +
                          "\nBUY - %2.f RUB" % positionSize + "\n+ " + str(cnt_tradeLots) + " NOVATEK lots" +
                          "--------------------------\n")
                else:
                    print("INFO ABOUT TRANSACTION\n--------------------------\n" +
                          "\nSELL + %2.f RUB" % positionSize + "\n- " + str(cnt_tradeLots) + " NOVATEK lots" +
                          "--------------------------\n")


if __name__ == '__main__':
    run_main()