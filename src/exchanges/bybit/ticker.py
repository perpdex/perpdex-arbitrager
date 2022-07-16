import time
from dataclasses import dataclass

import ccxt
import pybotters


@dataclass
class BybitRestTickerConfig:
    symbol: str
    update_limit_sec: float = 0.5


class BybitRestTicker:
    def __init__(self, config: BybitRestTickerConfig):
        self._config = config

        self._bybit = ccxt.bybit()

        self._last_ts1 = 0.0
        self._last_ts2 = 0.0
        self._last_price = 0.0
        self._last_bid = 0.0
        self._last_ask = 0.0

    def bid_price(self) -> float:
        bid, _ = self._get_bid_ask()
        return bid

    def ask_price(self) -> float:
        _, ask = self._get_bid_ask()
        return ask

    def last_price(self) -> float:
        if time.time() - self._last_ts1 >= self._config.update_limit_sec:
            trades = self._bybit.fetch_trades(symbol=self._config.symbol, limit=1)
            self._last_price = trades[0]['price']
        self._last_ts1 = time.time()
        return self._last_price

    def _get_bid_ask(self) -> tuple:
        if time.time() - self._last_ts2 >= self._config.update_limit_sec:
            ret = self._bybit.fetch_order_book(symbol=self._config.symbol, limit=1)
            self._last_bid = ret['bids'][0][0]
            self._last_ask = ret['asks'][0][0]
        self._last_ts2 = time.time()
        return self._last_bid, self._last_ask


@dataclass
class BybitWsTickerConfig:
    symbol: str


class BybitWsTicker:
    def __init__(
            self,
            store: pybotters.BybitInverseDataStore or pybotters.BybitUSDTDataStore,
            config: BybitWsTickerConfig):
        
        self._store = store
        self._config = config

    def bid_price(self) -> float:
        books = self._store.orderbook.sorted()
        return float(books['Buy'][0]['price'])
    
    def ask_price(self) -> float:
        books = self._store.orderbook.sorted()
        return float(books['Sell'][0]['price'])
    
    def last_price(self) -> float:
        trades = self._store.trade.find()
        return float(trades[0]['price'])
