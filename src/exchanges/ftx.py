import os
import time

import ccxt


class FtxRestTickerConfig:
    symbol: str
    update_limit_sec: float = 0.5


class FtxRestTicker:
    def __init__(self, config: FtxRestTickerConfig):
        self._config = config

        self._ftx = init_ccxt_ftx()

        self._last_ts = 0.0
        self._ticker = dict()

    def bid_price(self) -> float:
        t = self._get_ticker()
        return t['bid']

    def ask_price(self) -> float:
        t = self._get_ticker()
        return t['ask']

    def last_price(self) -> float:
        t = self._get_ticker()
        return t['last']

    def _get_ticker(self) -> dict:
        """
        ref:
          - https://github.com/ccxt/ccxt/blob/master/python/ccxt/ftx.py#L756
          - https://docs.ccxt.com/en/latest/manual.html#ticker-structure
        """
        if time.time() - self._last_ts < self._config.update_limit_sec:
            return self._ticker

        self._ticker = self._ftx.fetch_ticker(symbol=self._config.symbol)
        self._last_ts = time.time()
        return self._ticker


class FtxOrderer:
    """
    ref:
      - https://github.com/ccxt/ccxt/blob/master/python/ccxt/ftx.py
      - https://docs.ccxt.com/en/latest/manual.html#order-structure
    """
    def __init__(self):
        self._ftx = init_ccxt_ftx()

    def post_market_order(self, symbol: str, side_int: int, size: float) -> dict:
        return self._ftx.create_order(symbol, 'market', _to_side_str(side_int), size)

    def post_limit_order(self, symbol: str, side_int: int, size: float, price: float) -> dict:
        return self._ftx.create_order(symbol, 'limit', _to_side_str(side_int), size, price)

    def cancel_limit_order(self, symbol: str, order_id: str) -> dict:
        return self._ftx.cancel_order(order_id)


class FtxRestPositionGetterConfig:
    symbol: str


class FtxRestPositionGetter:
    def __init__(self, config: FtxRestPositionGetterConfig):
        self._ftx = init_ccxt_ftx()
        self._config = config

    def current_position(self) -> float:
        """
        ref:
          - https://github.com/ccxt/ccxt/blob/master/python/ccxt/ftx.py
          - https://docs.ccxt.com/en/latest/manual.html#position-structure
        """
        positions = self._ftx.fetch_positions(symbols=[self._config.symbol])
        if len(positions) == 0:
            return 0.0
        
        total = 0.0
        for pos in positions:
            base_size = pos['contract']
            side_sign = 1 if pos['side'] == 'long' else -1
            total += base_size * side_sign
        return total


def _to_side_str(side_int: int):
    if side_int > 0:
        return 'buy'
    if side_int < 0:
        return 'sell'
    raise ValueError
    

def init_ccxt_ftx(api_key: str, secret: str):
    return ccxt.ftx({
        'apiKey': os.environ['FTX_PUBLIC_API_KEY'],
        'secret': os.environ['SECRET_PRIVATE_KEY'],
    })
