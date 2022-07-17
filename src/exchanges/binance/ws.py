import asyncio
from typing import List

import pybotters


async def start_binance_ws_spot(api_key: str, secret: str, symbols: List[str], testnet: bool):
    pass


async def start_binance_ws_inverse(api_key: str, secret: str, symbols: List[str], testnet: bool):
    client = pybotters.Client(
        apis={'binance': [api_key, secret],
              'binance_testnet': [api_key, secret]},
        base_url=_rest_endpoint_inverse(testnet)
    )
    store = pybotters.BinanceDataStore()

    # pybotters doesn't supprot COIN-M, so initialize bymyself
    # https://github.com/MtkN1/pybotters/issues/172
    aws = [
        client.post('/dapi/v1/listenKey'),
        client.get('/dapi/v1/positionRisk'),
    ]
    for f in asyncio.as_completed(aws):
        resp = await f
        data = await resp.json()
        if resp.url.path in ('/dapi/v1/listenKey'):
            store.listenkey = data["listenKey"]
            asyncio.create_task(
                store._listenkey(resp.url, resp.__dict__["_raw_session"])
            )
        elif resp.url.path in ("/dapi/v1/positionRisk"):
            store.position._onresponse(data)

    channels = [store.listenkey]
    for symbol in symbols:
        s = symbol.replace('/', '').lower()
        channels.append(f'{s}@aggTrade')
        channels.append(f'{s}@bookTicker')
        channels.append(f'{s}@depth5@100ms')

    streams = "/".join(channels)
    await client.ws_connect(
        f"{_ws_endpoint_inverse(testnet)}/stream?streams={streams}",
        hdlr_json=store.onmessage,
    )

    await asyncio.sleep(2)

    return client, store


async def start_binance_ws_linear(api_key: str, secret: str, symbols: List[str], testnet: bool):
    client = pybotters.Client(
        apis={'binance': [api_key, secret],
              'binance_testnet': [api_key, secret]},
        base_url=_rest_endpoint_linear(testnet)
    )
    store = pybotters.BinanceDataStore()
    await store.initialize(
        client.get('/fapi/v2/positionRisk'),
        client.post('/fapi/v1/listenKey')
    )

    channels = [store.listenkey]
    for symbol in symbols:
        s = symbol.replace('/', '').lower()
        channels.append(f'{s}@aggTrade')
        channels.append(f'{s}@bookTicker')
        channels.append(f'{s}@depth5@100ms')

    streams = "/".join(channels)
    await client.ws_connect(
        f"{_ws_endpoint_linear(testnet)}/stream?streams={streams}",
        hdlr_json=store.onmessage,
    )

    await asyncio.sleep(2)

    return client, store


# spot
def _rest_endpoint_spot(testnet: bool):
    if testnet:
        # https://testnet.binance.vision/
        return 'https://testnet.binance.vision'
    # https://binance-docs.github.io/apidocs/spot/en/#general-api-information
    return 'https://api.binance.com'


def _ws_endpoint_spot(testnet: bool):
    if testnet:
        # https://testnet.binance.vision/
        return 'wss://testnet.binance.vision'
    # https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams
    return 'wss://stream.binance.com:9443'


# linear(USD M)
def _rest_endpoint_linear(testnet: bool):
    if testnet:
        # https://binance-docs.github.io/apidocs/futures/en/#testnet
        return 'https://testnet.binancefuture.com'
    # https://binance-docs.github.io/apidocs/futures/en/#general-api-information
    return 'https://fapi.binance.com'


def _ws_endpoint_linear(testnet: bool):
    if testnet:
        # https://binance-docs.github.io/apidocs/futures/en/#testnet
        # e.g. 'wss://stream.binancefuture.com/stream?streams=btcusdt@depth5'
        return 'wss://stream.binancefuture.com'
    # https://binance-docs.github.io/apidocs/futures/en/#websocket-market-streams
    return 'wss://fstream.binance.com'


# inverse(COIN M perpetual)
def _rest_endpoint_inverse(testnet: bool):
    if testnet:
        # https://binance-docs.github.io/apidocs/delivery/en/#general-info
        return 'https://testnet.binancefuture.com'
    # https://binance-docs.github.io/apidocs/delivery/en/#general-api-information
    return 'https://dapi.binance.com'


def _ws_endpoint_inverse(testnet: bool):
    if testnet:
        # https://binance-docs.github.io/apidocs/delivery/en/#general-info
        return 'wss://dstream.binancefuture.com'
    # https://binance-docs.github.io/apidocs/delivery/en/#websocket-market-streams
    return 'wss://dstream.binance.com'
