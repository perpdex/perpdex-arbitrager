import time
from dataclasses import dataclass

import ccxt
import pybotters


@dataclass
class _BinanceRestTickerConfig:
    symbol: str
    update_limit_sec: float = 0.5


class BinanceRestTicker:
    def __init__(self, ccxt_exchange: ccxt.binance, symbol: str, update_limit_sec: float = 0.5):
        self._ccxt_exchange = ccxt_exchange
        self._config = _BinanceRestTickerConfig(symbol=symbol, update_limit_sec=update_limit_sec)

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
            trades = self._ccxt_exchange.fetch_trades(symbol=self._config.symbol, limit=1)
            self._last_price = trades[0]['price']
        self._last_ts1 = time.time()
        return self._last_price

    def _get_bid_ask(self) -> dict:
        """
        https://binance-docs.github.io/apidocs/delivery/en/#symbol-order-book-ticker
        """
        if time.time() - self._last_ts2 >= self._config.update_limit_sec:
            ret = self._ccxt_exchange.fetch_bids_asks(symbols=[self._config.symbol])

            # FIXME: https://github.com/ccxt/ccxt/issues/14384
            # When symbol is BTCUSD_PERP, it is converted to BTC/USD, and
            # when symbol is BTCUSDT, it is converted to BTC/USDT.
            # Monkey patching to match the symbol.
            _symbol = self._config.symbol.replace('USD_PERP', '/USD').replace('USDT', '/USDT')

            self._last_bid_ask = ret[_symbol]
        self._last_ts2 = time.time()
        return self._last_bid_ask


@dataclass
class _BinanceWsTickerConfig:
    symbol: str


class BinanceWsTicker:
    def __init__(
            self,
            store: pybotters.BinanceDataStore,
            symbol: str):
        
        self._store = store
        self._config = _BinanceWsTickerConfig(symbol=symbol)

    def bid_price(self) -> float:
        """
        books =
        { 'b': [['21312.30', '31.291'], ['21312.10', '1.938'], ...],
          'a': [['21313.60', '14.973'], ['21316.40', '2.892'], ...]}
        """
        books = self._store.orderbook.sorted()
        return float(books['b'][0][0])
    
    def ask_price(self) -> float:
        books = self._store.orderbook.sorted()
        return float(books['a'][0][0])
    
    def last_price(self) -> float:
        trades = self._store.trade.find()
        return float(trades[0]['p'])
