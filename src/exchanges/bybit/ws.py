import asyncio
from typing import List

import pybotters


async def start_bybit_ws_inverse(api_key: str, secret: str, symbols: List[str], testnet: bool):
    client = pybotters.Client(
        apis={'bybit': [api_key, secret],
              'bybit_testnet': [api_key, secret]},
        base_url=_rest_endpoint(testnet)
    )
    store = pybotters.BybitInverseDataStore()

    channels = []
    for symbol in symbols:
        channels.append(f'trade.{symbol}')
        channels.append(f'orderBookL2_25.{symbol}')
    channels.append('position')

    await client.ws_connect(
        url=_ws_endpoint_inverse(testnet),
        send_json={'op': 'subscribe', 'args': channels},
        hdlr_json=store.onmessage,
    )

    await asyncio.sleep(2)

    return client, store


async def start_bybit_ws_linear(api_key: str, secret: str, symbols: List[str], testnet: bool):
    client = pybotters.Client(
        apis={'bybit': [api_key, secret],
              'bybit_testnet': [api_key, secret]},
        base_url=_rest_endpoint(testnet)
    )
    store = pybotters.BybitUSDTDataStore()

    public_channels = []
    for symbol in symbols:
        public_channels.append(f'trade.{symbol}')
        public_channels.append(f'orderBookL2_25.{symbol}')

    private_channels = ['position']

    await client.ws_connect(
        url=_ws_endpoint_linear_public(testnet),
        send_json={'op': 'subscribe', 'args': public_channels},
        hdlr_json=store.onmessage,
    )
    await client.ws_connect(
        url=_ws_endpoint_linear_private(testnet),
        send_json={'op': 'subscribe', 'args': private_channels},
        hdlr_json=store.onmessage,
    )

    await asyncio.sleep(2)

    return client, store


async def initialize_position(
        client: pybotters.Client,
        store: pybotters.BybitInverseDataStore or pybotters.BybitUSDTDataStore,
        symbol: str):
    if 'USDT' in symbol:  # linear
        await store.initialize(
            client.get('/v2/private/position/list', params={'symbol': symbol}),
        )
    elif 'USD' in symbol:  # inverse
        await store.initialize(
            client.get('/v2/private/position/list', params={'symbol': symbol}),
        )


def _rest_endpoint(testnet: bool):
    if testnet:
        return 'https://api-testnet.bybit.com'
    return 'https://api.bybit.com'


def _ws_endpoint_inverse(testnet: bool):
    if testnet:
        return 'wss://stream-testnet.bybit.com/realtime'
    return 'wss://stream.bybit.com/realtime'


def _ws_endpoint_linear_public(testnet: bool):
    if testnet:
        return 'wss://stream-testnet.bybit.com/realtime_public'
    return 'wss://stream.bybit.com/realtime_public'


def _ws_endpoint_linear_private(testnet: bool):
    if testnet:
        return 'wss://stream-testnet.bybit.com/realtime_private'
    return 'wss://stream.bybit.com/realtime_private'
