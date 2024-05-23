from typing import Optional

class StopMarketQueue:
    """
    Очередь стоп-маркет ордеров
    """

    def __init__(self):
        self.stop_market = list([]) # список стоп маркет цен
        self.count = list([])  # список количества лотов по заявкам
        self.size = 0 # количество заявок

    async def push(self, cast: float, cnt: int):
        """
        Создать стоп-маркет ордер

        :param cast: цена заявки
        :param cnt: количество лотов
        """
        self.stop_market.append(cast)
        self.count.append(cnt)
        self.size += 1
    

    def pop(self) -> Optional[tuple]:
        """
        Получить данные для самого раннего стоп-ордера
        """
        if not self.stop_market or not self.count:
            return None
        stop_market = self.stop_market.pop(0)
        cnt_lots = self.count.pop(0)
        self.size -= 1
        return stop_market, cnt_lots


    def get(self) -> Optional[tuple]:
        """
        Получение данных о первой заявке
        :return: (цена заявки, количество лотов)
        """
        if not self.stop_market or not self.count:
            return None
        return self.stop_market[0], self.count[0]

    def get_last(self) -> Optional[tuple]:
        """
        Получение данных о первой заявке
        (1) отладочный метод
        :return: (цена заявки, количество лотов)
        """
        if not self.stop_market or not self.count:
            return None
        return self.stop_market[-1], self.count[-1]