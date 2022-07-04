import os
import time
from logging import getLogger

from src.arbitrager import Arbitrager, ArbitragerConfig
from src.contracts.utils import get_w3
from src.exchanges.ftx import (FtxOrderer, FtxPositionGetter,
                               FtxPositionGetterConfig, FtxRestTicker,
                               FtxRestTickerConfig)
from src.exchanges.perpdex import (PerpdexOrderer, PerpdexPositionGetter,
                                   PerpdexPositionGetterConfig, PerpdexTicker,
                                   PerpdexTickerConfig)
from src.spread_calculator import TakeTakeSpreadCalculator
from src.target_pos_calculator import (TargetPosCalculator,
                                       TargetPosCalculatorConfig)
from position_chaser import TakePositionChaser, TakePositionChaserConfig


# resolve dependencies
def _init_ftx_perpdex_arb_bot() -> Arbitrager:
    _ftx_symbol = 'BTC/USD'
    _perpdex_symbol = 'BTC'

    _ftx_position_getter = FtxPositionGetter(
        config=FtxPositionGetterConfig(symbol=_ftx_symbol),
    )

    _w3 = get_w3(
        network_name=os.environ['WEB3_NETWORK_NAME'],
        web3_provider_uri=os.environ['WEB3_PROVIDER_URI'],
        user_private_key=os.environ['USER_PRIVATE_KEY'],
    )

    # 1: ftx, 2: perpdex
    target_pos_calculator = TargetPosCalculator(
        spread_getter=TakeTakeSpreadCalculator(
            price_getter1=FtxRestTicker(
                config=FtxRestTickerConfig(symbol=_ftx_symbol),
            ),
            price_getter2=PerpdexTicker(
                w3=_w3,
                config=PerpdexTickerConfig(symbol=_perpdex_symbol),
            ),
        ),
        position_getter=_ftx_position_getter,
        config=TargetPosCalculatorConfig(),
    )

    # 1: ftx, 2: perpdex
    position_chaser1 = TakePositionChaser(
        position_getter=_ftx_position_getter,
        taker=FtxOrderer(),
        config=TakePositionChaserConfig(symbol=_ftx_symbol),
    )

    position_chaser2 = TakePositionChaser(
        position_getter=PerpdexPositionGetter(
            w3=_w3,
            config=PerpdexPositionGetterConfig(symbol=_perpdex_symbol),
        ),
        taker=PerpdexOrderer(w3=_w3),
        config=TakePositionChaserConfig(symbol=_perpdex_symbol),
    )

    return Arbitrager(
        target_pos_calculator=target_pos_calculator,
        position_chaser1=position_chaser1,
        position_chaser2=position_chaser2,
        config=ArbitragerConfig(trade_loop_sec=1),
    )


def main():
    logger = getLogger(__name__)
    while True:
        arb = _init_ftx_perpdex_arb_bot()
        arb.start()
        while arb.health_check():
            time.sleep(30)
        logger.warning('Restarting Arb bot')
