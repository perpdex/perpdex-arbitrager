import time
from dataclasses import dataclass

import ccxt


@dataclass
class BinanceLinearRestTickerConfig:
    symbol: str
    update_limit_sec: float = 0.5


class BinanceLinearRestTicker:
    def __init__(self, config: BinanceLinearRestTickerConfig):
        self._config = config

        self._binance = ccxt.binance({'options': {'defaultType': 'future'}})

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


@dataclass
class BinanceLinearRestPositionGetterConfig:
    api_key: str
    secret: str
    symbol: str


class BinanceLinearRestPositionGetter:
    """
    - https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py
    - https://docs.ccxt.com/en/latest/manual.html#position-structure
    """
    def __init__(self, config: BinanceLinearRestPositionGetterConfig):
        self._binance = ccxt.binance({
            'apiKey': config.api_key,
            'secret': config.secret,
            'options': {'defaultType': 'future'},
        })
        self._config = config

    def current_position(self) -> float:
        positions = self._binance.fetch_positions(symbols=[self._config.symbol])
        if len(positions) == 0:
            return 0.0
        
        total = 0.0
        for pos in positions:
            base_size = pos['contracts']
            side_sign = 1 if pos['side'] == 'long' else -1
            total += base_size * side_sign
        return total
   

