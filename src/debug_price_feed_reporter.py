import asyncio
from dataclasses import dataclass
from logging import getLogger
import os
import sys

import ccxt

from .contracts.utils import get_contract_from_abi_json, get_w3
from .exchanges import binance
from .types import IPriceGetter

@dataclass
class DebugPriceFeedReporterConfig:
    price_feed_contract_abi_json_filepath: str
    loop_sec: float


class DebugPriceFeedReporter:
    def __init__(
            self,
            config: DebugPriceFeedReporterConfig,
            w3,
            price_getter: IPriceGetter,
    ):
        self._config = config
        self._price_getter = price_getter
        self._logger = getLogger(__class__.__name__)
        self._contract = get_contract_from_abi_json(w3, config.price_feed_contract_abi_json_filepath)

        self._task: asyncio.Task = None

    def health_check(self) -> bool:
        return not self._task.done()

    def start(self):
        self._logger.debug('debug price feed reporter start')
        self._task = asyncio.create_task(self._report())

    async def _report(self):
        self._logger.debug('_report')
        try:
            while True:
                price = self._price_getter.ask_price()
                self._report_price(price)

                await asyncio.sleep(self._config.loop_sec)
        except BaseException:
            self._logger.error(sys.exc_info(), exc_info=True)

    def _report_price(self, price):
        self._logger.info('report price {}'.format(price))
        tx_hash = self._contract.functions.setPrice(int(price * 10**18)).transact()
        self._w3.eth.wait_for_transaction_receipt(tx_hash)


def create_debug_price_feed_reporter():
    w3 = get_w3(
        network_name=os.environ['WEB3_NETWORK_NAME'],
        web3_provider_uri=os.environ['WEB3_PROVIDER_URI'],
        user_private_key=os.environ['USER_PRIVATE_KEY'],
    )

    binance_symbol = os.getenv('BINANCE_SYMBOL', 'BTCUSDT')
    default_type = binance.ccxt_default_type(symbol=binance_symbol)
    ccxt_binance = ccxt.binance({
        'options': {'defaultType': default_type},
    })

    price_getter = binance.BinanceRestTicker(
        ccxt_exchange=ccxt_binance,
        symbol=binance_symbol,
        use_mid_price=True,
    )

    return DebugPriceFeedReporter(
        config=DebugPriceFeedReporterConfig(
            price_feed_contract_abi_json_filepath=os.getenv('PERPDEX_DEBUG_PRICE_FEED_PATH'),
            loop_sec=60 * 60
        ),
        w3=w3,
        price_getter=price_getter
    )

