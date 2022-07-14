import os
from src.exchanges import perpdex
from src.contracts import utils
import pytest


@pytest.fixture
def w3():
    if os.environ['WEB3_NETWORK_NAME'] not in ('localhost'):
        raise ValueError("Warning: probably wrong environment variables")

    return utils.get_w3(
        network_name=os.environ['WEB3_NETWORK_NAME'],
        web3_provider_uri=os.environ['WEB3_PROVIDER_URI'],
        user_private_key=os.environ['USER_PRIVATE_KEY'],
    )


@pytest.fixture
def market_filepath():
    return os.path.join(
        os.environ['PERPDEX_CONTRACT_ABI_JSON_DIRPATH'], 'PerpdexMarketBTC.json')


@pytest.fixture
def market_contract(w3, market_filepath):
    return perpdex._get_contract_from_abi_json(w3, market_filepath)


@pytest.fixture
def exchange_filepath():
    return os.path.join(
        os.environ['PERPDEX_CONTRACT_ABI_JSON_DIRPATH'], 'PerpdexExchange.json')


@pytest.fixture
def exchange_contract(w3, exchange_filepath):
    return perpdex._get_contract_from_abi_json(w3, exchange_filepath)


@pytest.fixture(autouse=True, scope='function')
def before_after(w3, market_contract, exchange_contract):
    yield

    # teardown

    # reset pool info
    tx = market_contract.functions.setPoolInfo(dict(
        base=0,
        quote=0,
        totalLiquidity=0,
        cumBasePerLiquidityX96=0,
        cumQuotePerLiquidityX96=0,
        baseBalancePerShareX96=0,
    )).transact()
    w3.eth.wait_for_transaction_receipt(tx)

    # reset account info
    tx = exchange_contract.functions.setAccountInfo(
        w3.eth.default_account,     # trader
        dict(collateralBalance=0),  # vaultInfo
        [],                         # markets
    ).transact()
    w3.eth.wait_for_transaction_receipt(tx)

    # reset taker info
    tx = exchange_contract.functions.setTakerInfo(
        w3.eth.default_account,                    # trader
        market_contract.address,                   # market
        dict(baseBalanceShare=0, quoteBalance=0),  # takerInfo
    ).transact()
    w3.eth.wait_for_transaction_receipt(tx)

    # reset maker info
    tx = exchange_contract.functions.setMakerInfo(
        w3.eth.default_account,                    # trader
        market_contract.address,                   # market
        dict(liquidity=0, cumBaseSharePerLiquidityX96=0, cumQuotePerLiquidityX96=0),  # makerInfo
    ).transact()
    w3.eth.wait_for_transaction_receipt(tx)

    # reset insurance fund info
    tx = exchange_contract.functions.setInsuranceFundInfo(
        dict(balance=0, liquidationRewardBalance=0)  # InsuranceFundInfo
    ).transact()
    w3.eth.wait_for_transaction_receipt(tx)

    # reset protocol info
    tx = exchange_contract.functions.setProtocolInfo(
        dict(protocolFee=0)  # ProtocolInfo
    ).transact()
    w3.eth.wait_for_transaction_receipt(tx)


def test_perpdex_contract_ticker(w3):
    contfact_filepath = os.path.join(
        os.environ['PERPDEX_CONTRACT_ABI_JSON_DIRPATH'], 'PerpdexMarketBTC.json')
    ticker = perpdex.PerpdexContractTicker(
        w3=w3,
        config=perpdex.PerpdexContractTickerConfig(
            market_contract_abi_json_filepath=contfact_filepath,
            update_limit_sec=0.00001,
        )
    )

    # change mark price to 100.0 (quote/base*baseBalancePerShare)
    tx_hash = ticker._market_contract.functions.setPoolInfo(dict(
        base=10,
        quote=1000,
        totalLiquidity=1000,
        cumBasePerLiquidityX96=0,
        cumQuotePerLiquidityX96=0,
        baseBalancePerShareX96=1 * perpdex.Q96,
    )).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)

    assert ticker.bid_price() == 100.0
    assert ticker.ask_price() == 100.0
    assert ticker.last_price() == 100.0

    # change mark price to 200.0 (quote/base*baseBalancePerShare)
    tx_hash = ticker._market_contract.functions.setPoolInfo(dict(
        base=10,
        quote=2000,
        totalLiquidity=1000,
        cumBasePerLiquidityX96=0,
        cumQuotePerLiquidityX96=0,
        baseBalancePerShareX96=1 * perpdex.Q96,
    )).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)

    assert ticker.bid_price() == 200.0
    assert ticker.ask_price() == 200.0
    assert ticker.last_price() == 200.0


def test_perpdex_position_getter(w3, market_filepath, exchange_filepath):
    getter = perpdex.PerpdexPositionGetter(
        w3=w3,
        config=perpdex.PerpdexPositionGetterConfig(
            market_contract_abi_json_filepath=market_filepath,
            exchange_contract_abi_json_filepath=exchange_filepath,
        )
    )
    assert getter.current_position() == 0.0


def test_perpdex_orderer(w3, market_filepath, exchange_filepath, market_contract, exchange_contract):
    orderer = perpdex.PerpdexOrderer(
        w3=w3,
        config=perpdex.PerpdexOrdererConfig(
            market_contract_abi_json_filepaths=[market_filepath],
            exchange_contract_abi_json_filepath=exchange_filepath,
        )
    )

    getter = perpdex.PerpdexPositionGetter(
        w3=w3,
        config=perpdex.PerpdexPositionGetterConfig(
            market_contract_abi_json_filepath=market_filepath,
            exchange_contract_abi_json_filepath=exchange_filepath,
        )
    )

    # mock pool info
    tx_hash = market_contract.functions.setPoolInfo(dict(
        base=10 * (10 ** perpdex.DECIMALS),
        quote=1000 * (10 ** perpdex.DECIMALS),
        totalLiquidity=1000,
        cumBasePerLiquidityX96=0,
        cumQuotePerLiquidityX96=0,
        baseBalancePerShareX96=1 * perpdex.Q96,
    )).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)

    # mock collateral
    tx_hash = exchange_contract.functions.setAccountInfo(
        w3.eth.default_account,                                 # trader
        dict(collateralBalance=10 * (10 ** perpdex.DECIMALS)),  # vaultInfo
        [],                                                     # markets
    ).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)

    # long BTC 0.01
    orderer.post_market_order(symbol='BTC', side_int=1, size=0.01)

    assert getter.current_position() == 0.01

    # short BTC 0.02
    orderer.post_market_order(symbol='BTC', side_int=-1, size=0.03)

    assert getter.current_position() == -0.02
