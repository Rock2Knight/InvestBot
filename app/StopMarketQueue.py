class StopMarketQueue:

    def __init__(self):
        self.stop_market = list([])
        self.count = list([])
        self.size = 0

    def push(self, cast: float, cnt: int):
        self.stop_market.append(cast)
        self.count.append(cnt)
        self.size += 1

    def pop(self):
        stop_market = self.stop_market.pop(0)
        cnt_lots = self.count.pop(0)
        self.size -= 1
        return stop_market, cnt_lots

    def get_cast(self, index: int):
        return self.stop_market[index]

    def remove(self, index: int):
        stop_market = self.stop_market[index]
        cnt_lots = self.count[index]
        self.stop_market.pop(index)
        self.count.pop(index)
        self.size -= 1
        return stop_market, cnt_lots