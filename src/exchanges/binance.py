import os
import time
from dataclasses import dataclass

import ccxt


@dataclass
class BinanceRestTickerConfig:
    symbol: str
    update_limit_sec: float = 0.5


class BinanceRestTicker:
    def __init__(self, config: BinanceRestTickerConfig):
        self._config = config

        self._binance = ccxt.binance({'options': {'defaultType': 'delivery'}})

        self._last_ts1 = 0.0
        self._last_ts2 = 0.0
        self._last_price = 0.0
        self._last_bid_ask = dict()

    def bid_price(self) -> float:
        ba = self._get_bid_ask()
        return ba['bid']

    def ask_price(self) -> float:
        ba = self._get_bid_ask()
        return ba['ask']

    def last_price(self) -> float:
        """
        https://binance-docs.github.io/apidocs/delivery/en/#recent-trades-list
        """
        if time.time() - self._last_ts1 >= self._config.update_limit_sec:
            trades = self._binance.fetch_trades(symbol=self._config.symbol, limit=1)
            self._last_price = trades[0]['price']
        self._last_ts1 = time.time()
        return self._last_price

    def _get_bid_ask(self) -> dict:
        """
        https://binance-docs.github.io/apidocs/delivery/en/#symbol-order-book-ticker
        """
        if time.time() - self._last_ts2 >= self._config.update_limit_sec:
            ret = self._binance.fetch_bids_asks(symbols=[self._config.symbol])
            self._last_bid_ask = ret[self._config.symbol]
        self._last_ts2 = time.time()
        return self._last_bid_ask

