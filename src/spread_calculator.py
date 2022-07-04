
class IPriceGetter:
    def bid_price(self) -> float:
        pass
    
    def ask_price(self) -> float:
        pass


class TakeTakeSpreadCalculator:
    def __init__(self, price_getter1: IPriceGetter, price_getter2: IPriceGetter):
        self._price_getter1 = price_getter1
        self._price_getter2 = price_getter2

    def spread(self) -> float:
        # short 2, long 1
        spread1 = self._get_bid2_ask1_spread_rate()
        # short 1, long 2
        spread2 = self._get_bid1_ask2_spread_rate()

        # choose larger one
        if spread1 > spread2:
            if spread1 > 0:
                return spread1
            return 0
        else:
            if spread2 > 0:
                return spread2 * -1
            return 0

    def _bid2_ask1_spread_rate(self):
        bid2 = self._price_getter2.bid_price()
        ask1 = self._price_getter1.ask_price()
        return bid2 / ask1 - 1

    def _bid1_ask2_spread_rate(self):
        bid1 = self._price_getter1.bid_price()
        ask2 = self._price_getter2.ask_price()
        return bid1 / ask2 - 1
