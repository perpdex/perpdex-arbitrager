import asyncio
import pybotters
import time
from dataclasses import dataclass

import ccxt


@dataclass
class BybitInverseRestTickerConfig:
    symbol: str
    update_limit_sec: float = 0.5


class BybitInverseRestTicker:
    def __init__(self, config: BybitInverseRestTickerConfig):
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
class BybitInverseWebsocketTickerConfig:
    symbol: str
    testnet: bool = False


class BybitInverseWebsocketTicker:
    def __init__(self, config: BybitInverseWebsocketTickerConfig):
        self._config = config

        self._bid_price: float = 0.0
        self._ask_price: float = 0.0
        self._last_price: float = 0.0

        self._tasks: list[asyncio.Task] = None
        self._ws_task: asyncio.Task = None
        self._store: pybotters.BybitInverseDataStore = pybotters.BybitInverseDataStore()
    
    def bid_price(self) -> float:
        return self._bid_price
    
    def ask_price(self) -> float:
        return self._ask_price
    
    def last_price(self) -> float:
        return self._last_price

    def start(self):
        asyncio.create_task(self._main())
        asyncio.create_task(self._watch_trade())
        asyncio.create_task(self._watch_orderbook())
    
    async def _main(self):
        async with pybotters.Client() as client:
            args = [
                f'trade.{self._config.symbol}',
                f'orderBookL2_25.{self._config.symbol}',
            ]
            self._ws_task = await client.ws_connect(
                url=_ws_endpoint(self._config.testnet),
                send_json={
                    'op': 'subscribe',
                    'args': args
                },
                hdlr_json=self._store.onmessage,
            )
            await self._ws_task

    async def _watch_trade(self):
        while self._ws_task is None:
            await asyncio.sleep(1)

        with self._store.trade.watch() as stream:
            async for change in stream:
                self._last_price = float(change.data['price'])

    async def _watch_orderbook(self):
        while self._ws_task is None:
            await asyncio.sleep(1)

        with self._store.orderbook.watch() as stream:
            async for _ in stream:
                books = self._store.orderbook.sorted()
                self._bid_price = float(books['Buy'][0]['price'])
                self._ask_price = float(books['Sell'][0]['price'])


@dataclass
class BybitInverseRestPositionGetterConfig:
    api_key: str
    secret: str
    symbol: str


class BybitInverseRestPositionGetter:
    """
    - https://github.com/ccxt/ccxt/blob/master/python/ccxt/bybit.py
    - https://docs.ccxt.com/en/latest/manual.html#position-structure
    """
    def __init__(self, config: BybitInverseRestPositionGetterConfig):
        self._bybit = ccxt.bybit({
            'apiKey': config.api_key,
            'secret': config.secret,
        })
        self._config = config

    def current_position(self) -> int:
        # this doesn't work
        # positions = self._bybit.fetch_positions(symbols=[self._config.symbol])
        ret = self._bybit.privateGetV2PrivatePositionList(dict(symbol=self._config.symbol))
        self._bybit.load_markets()
        market = self._bybit.market(self._config.symbol)
        raw_positions = [ret['result']]
        positions = []
        for raw_position in raw_positions:
            positions.append(self._bybit.parse_position(raw_position, market))

        if len(positions) == 0:
            return 0
        
        total = 0
        for pos in positions:
            base_size = pos['contracts']
            side_sign = 1 if pos['side'] == 'long' else -1
            total += base_size * side_sign
        return int(total)
   

@dataclass
class BybitInverseWebsocketPositionGetterConfig:
    api_key: str
    secret: str
    symbol: str
    testnet: bool = False


class BybitInverseWebsocketPositionGetter:
    def __init__(self, config: BybitInverseWebsocketPositionGetterConfig):
        self._config = config

        self._current_position: int = 0

        secret = {
            'bybit': [
                self._config.api_key,
                self._config.secret
            ],
            'bybit_testnet': [
                self._config.api_key,
                self._config.secret
            ]
        }
        self._client = pybotters.Client(
            apis=secret,
            base_url=_rest_endpoint(self._config.testnet)
        )
        self._store = pybotters.BybitInverseDataStore()
        self._task: asyncio.Task = None

        self.start()
    
    def start(self):
        self._task = asyncio.create_task(self._main())
    
    def finish(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._client.close())

    async def _main(self):
        await self._store.initialize(
            self._client.get('/v2/private/position/list',
                             params={'symbol': self._config.symbol}),
        )

        await self._client.ws_connect(
            url=_ws_endpoint(self._config.testnet),
            send_json={
                'op': 'subscribe',
                'args': ['position']
            },
            hdlr_json=self._store.onmessage,
        )

        with self._store.position.watch() as stream:
            self._update()
            async for _ in stream:
                self._update()

    def _update(self):
        pos_dict = self._store.position.one(self._config.symbol)
        if pos_dict['side'] is not None:
            side_int = 1 if pos_dict['side'] == 'Buy' else -1
            self._current_position = int(pos_dict['size']) * side_int

    def current_position(self) -> int:
        return self._current_position


@dataclass
class BybitInverseOrdererConfig:
    api_key: str
    secret: str


class BybitInverseOrderer:
    """
    - https://github.com/ccxt/ccxt/blob/master/python/ccxt/bybit.py
    - https://docs.ccxt.com/en/latest/manual.html#order-structure
    """
    def __init__(self, config: BybitInverseOrdererConfig):
        self._bybit = ccxt.bybit({
            'apiKey': config.api_key,
            'secret': config.secret,
        })

    def post_market_order(self, symbol: str, side_int: int, size: float) -> dict:
        return self._bybit.create_order(symbol, 'market', _to_side_str(side_int), int(size))

    def post_limit_order(self, symbol: str, side_int: int, size: float, price: float) -> dict:
        return self._bybit.create_order(symbol, 'limit', _to_side_str(side_int), int(size), price)

    def cancel_limit_order(self, symbol: str, order_id: str) -> dict:
        return self._bybit.cancel_order(order_id)


def _to_side_str(side_int: int):
    if side_int > 0:
        return 'buy'
    if side_int < 0:
        return 'sell'
    raise ValueError


def _ws_endpoint(testnet: bool):
    if testnet:
        return 'wss://stream-testnet.bybit.com/realtime'
    return 'wss://stream.bybit.com/realtime'


def _rest_endpoint(testnet: bool):
    if testnet:
        return 'https://api-testnet.bybit.com'
    return 'https://api.bybit.com'
