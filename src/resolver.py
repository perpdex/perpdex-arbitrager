import os

from .arbitrager import Arbitrager, ArbitragerConfig
from .contracts.utils import get_w3
from .exchanges import binance, perpdex
from .position_chaser import TakePositionChaser, TakePositionChaserConfig
from .spread_calculator import TakeTakeSpreadCalculator
from .target_pos_calculator import (TargetPosCalculator,
                                    TargetPosCalculatorConfig)


def binance_perpdex_arbitrager() -> Arbitrager:
    _w3 = get_w3(
        network_name=os.environ['WEB3_NETWORK_NAME'],
        web3_provider_uri=os.environ['WEB3_PROVIDER_URI'],
        user_private_key=os.environ['USER_PRIVATE_KEY'],
    )
    _market_contract_filepath = os.path.join(
        os.environ['PERPDEX_CONTRACT_ABI_JSON_DIRPATH'], 'PerpdexMarketBTC.json')

    _exchange_contract_filepath = os.path.join(
        os.environ['PERPDEX_CONTRACT_ABI_JSON_DIRPATH'], 'PerpdexExchange.json')

    # position getter

    _binance_position_getter = binance.BinanceLinearRestPositionGetter(
        config=binance.BinanceLinearRestPositionGetterConfig(
            api_key=os.environ["BINANCE_API_KEY"],
            secret=os.environ["BINANCE_SECRET"],
            symbol='BTC/USDT',
        )
    )

    _perpdex_position_getter = perpdex.PerpdexPositionGetter(
        w3=_w3,
        config=perpdex.PerpdexPositionGetterConfig(
            market_contract_abi_json_filepath=_market_contract_filepath,
            exchange_contract_abi_json_filepath=_exchange_contract_filepath,
        )
    )

    # ticker

    _binance_ticker = binance.BinanceLinearRestTicker(
        config=binance.BinanceLinearRestTickerConfig(
            symbol='BTC/USDT',
            update_limit_sec=0.5,
        )
    )

    _perpdex_ticker = perpdex.PerpdexContractTicker(
        w3=_w3,
        config=perpdex.PerpdexContractTickerConfig(
            market_contract_abi_json_filepath=_market_contract_filepath,
            update_limit_sec=0.5,
        )
    )

    # orderer

    _binance_orderer = binance.BinanceLinearOrderer(
        config=binance.BinanceLinearOrdererConfig(
            api_key=os.environ['BINANCE_API_KEY'],
            secret=os.environ['BINANCE_SECRET'],
        )
    )

    _perpdex_orderer = perpdex.PerpdexOrderer(
        w3=_w3,
        config=perpdex.PerpdexOrdererConfig(
            market_contract_abi_json_filepaths=[_market_contract_filepath],
            exchange_contract_abi_json_filepath=_exchange_contract_filepath,
        )
    )

    # 1: binance, 2: perpdex
    target_pos_calculator = TargetPosCalculator(
        spread_getter=TakeTakeSpreadCalculator(
            price_getter1=_binance_ticker,
            price_getter2=_perpdex_ticker,
        ),
        position_getter=_binance_position_getter,
        config=TargetPosCalculatorConfig(
            open_threshold=0.0010,   # 0.10%
            close_threshold=0.0005,  # 0.05%
            threshold_step=0.0001,   # 0.01%
            lot_size=0.001,          # 0.001 [base]
        ),
    )

    # 1: binance, 2: perpdex
    binance_position_chaser = TakePositionChaser(
        position_getter=_binance_position_getter,
        taker=_binance_orderer,
        config=TakePositionChaserConfig(
            symbol='BTC/USDT',
        ),
    )

    perpdex_position_chaser = TakePositionChaser(
        position_getter=_perpdex_position_getter,
        taker=_perpdex_orderer,
        config=TakePositionChaserConfig(
            symbol='BTC',
        ),
    )

    return Arbitrager(
        target_pos_calculator=target_pos_calculator,
        position_chaser1=binance_position_chaser,
        position_chaser2=perpdex_position_chaser,
        config=ArbitragerConfig(
            trade_loop_sec=1.0
        ),
    )
