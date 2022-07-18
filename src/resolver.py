from dataclasses import dataclass
import os

import ccxt

from .arbitrager import Arbitrager, ArbitragerConfig, IPositionChaser
from .contracts.utils import get_w3
from .exchanges import binance, perpdex
from .position_chaser import (
    TakePositionChaser, TakePositionChaserConfig,
    IPositionGetter
)
from .spread_calculator import TakeTakeSpreadCalculator, IPriceGetter
from .target_pos_calculator import (TargetPosCalculator,
                                    TargetPosCalculatorConfig)

@dataclass
class ExchangeClientSet:
    position_chaser: IPositionChaser
    position_getter: IPositionGetter
    price_getter: IPriceGetter

def create_binance_client_set(one_side: bool=False):
    binance_symbol = os.getenv('BINANCE_SYMBOL', 'BTCUSDT')
    default_type = binance.ccxt_default_type(symbol=binance_symbol)
    ccxt_binance = ccxt.binance({
        'apiKey': None if one_side else os.environ['BINANCE_API_KEY'],
        'secret': None if one_side else os.environ['BINANCE_SECRET'],
        'options': {'defaultType': default_type},
    })

    if one_side:
        position_getter = None
        position_chaser = None
    else:
        position_getter = binance.BinanceRestPositionGetter(
            ccxt_exchange=ccxt_binance,
            symbol=binance_symbol,
        )
        orderer = binance.BinanceOrderer(ccxt_exchange=ccxt_binance)
        position_chaser = TakePositionChaser(
            position_getter=position_getter,
            taker=orderer,
            config=TakePositionChaserConfig(
                symbol=binance_symbol,
            )
        )

    ticker = binance.BinanceRestTicker(
        ccxt_exchange=ccxt_binance,
        symbol=binance_symbol,
        update_limit_sec=0.5,
        use_mid_price=one_side,
    )

    return ExchangeClientSet(
        position_chaser=position_chaser,
        position_getter=position_getter,
        price_getter=ticker,
    )

def create_perpdex_client_set():
    web3_network_name = os.environ['WEB3_NETWORK_NAME']
    _w3 = get_w3(
        network_name=web3_network_name,
        web3_provider_uri=os.environ['WEB3_PROVIDER_URI'],
        user_private_key=os.environ['USER_PRIVATE_KEY'],
    )
    market_name = os.getenv('PERPDEX_MARKET', 'USD')
    inverse = market_name == 'USD'
    abi_json_dirpath = os.getenv('PERPDEX_CONTRACT_ABI_JSON_DIRPATH', '/app/deps/perpdex-contract/deployments/' + web3_network_name)
    _market_contract_filepath = os.path.join(abi_json_dirpath, 'PerpdexMarket{}.json'.format(market_name))
    _exchange_contract_filepath = os.path.join(abi_json_dirpath, 'PerpdexExchange.json')

    position_getter = perpdex.PerpdexPositionGetter(
        w3=_w3,
        config=perpdex.PerpdexPositionGetterConfig(
            market_contract_abi_json_filepath=_market_contract_filepath,
            exchange_contract_abi_json_filepath=_exchange_contract_filepath,
        )
    )

    ticker = perpdex.PerpdexContractTicker(
        w3=_w3,
        config=perpdex.PerpdexContractTickerConfig(
            market_contract_abi_json_filepath=_market_contract_filepath,
            update_limit_sec=0.5,
            inverse=inverse,
        ),
    )

    orderer = perpdex.PerpdexOrderer(
        w3=_w3,
        config=perpdex.PerpdexOrdererConfig(
            market_contract_abi_json_filepaths=[_market_contract_filepath],
            exchange_contract_abi_json_filepath=_exchange_contract_filepath,
        )
    )

    position_chaser = TakePositionChaser(
        position_getter=position_getter,
        taker=orderer,
        config=TakePositionChaserConfig(
            symbol=market_name,
            inverse=inverse,
        ),
    )

    return ExchangeClientSet(
        position_chaser=position_chaser,
        position_getter=position_getter,
        price_getter=ticker,
    )

def create_arbitrager(client_set1: ExchangeClientSet, client_set2: ExchangeClientSet) -> Arbitrager:
    target_pos_calculator = TargetPosCalculator(
        spread_getter=TakeTakeSpreadCalculator(
            price_getter1=client_set1.price_getter,
            price_getter2=client_set2.price_getter,
        ),
        position_getter=client_set1.position_getter,
        config=TargetPosCalculatorConfig(
            open_threshold=0.0010,   # 0.10%
            close_threshold=0.0005,  # 0.05%
            threshold_step=0.0001,   # 0.01%
            lot_size=0.001,          # 0.001 [base]
        ),
    )

    return Arbitrager(
        target_pos_calculator=target_pos_calculator,
        position_chaser1=client_set1.position_chaser,
        position_chaser2=client_set2.position_chaser,
        config=ArbitragerConfig(
            trade_loop_sec=1.0
        ),
    )

def create_perpdex_binance_arbitrager():
    one_side_arb = bool(int(os.getenv('ONE_SIDE_ARB', '0')))
    perpdex_client_set = create_perpdex_client_set()
    binance_client_set = create_binance_client_set(one_side=one_side_arb)
    return create_arbitrager(perpdex_client_set, binance_client_set)
