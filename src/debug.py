import os
from .contracts.utils import get_w3, get_contract_from_abi_json


def printAccountInfo(account):
    w3 = _create_w3()
    exchange_contract = _create_exchange_contract(w3)

    if account is None:
        account = w3.eth.default_account

    # TODO: use multicall and print more infos
    native_token_balance = w3.eth.get_balance(account) / 10**18
    total_account_value = exchange_contract.functions.getTotalAccountValue(account).call() / 10**18
    collateral_balance = exchange_contract.functions.accountInfos(account).call()[0] / 10**18
    print('native_token_balance {}'.format(native_token_balance))
    print('total_account_value {}'.format(total_account_value))
    print('collateral_balance {}'.format(collateral_balance))


def setCollateralBalance(balance, account):
    w3 = _create_w3()
    exchange_contract = _create_exchange_contract(w3)

    if account is None:
        account = w3.eth.default_account

    tx_hash = exchange_contract.functions.setCollateralBalance(
        account,
        balance * 10**18,
    ).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)


def _create_w3():
    web3_network_name = os.environ['WEB3_NETWORK_NAME']
    return get_w3(
        network_name=web3_network_name,
        web3_provider_uri=os.environ['WEB3_PROVIDER_URI'],
        user_private_key=os.environ['USER_PRIVATE_KEY'],
    )

def _create_exchange_contract(w3):
    web3_network_name = os.environ['WEB3_NETWORK_NAME']
    abi_json_dirpath = os.getenv('PERPDEX_CONTRACT_ABI_JSON_DIRPATH', '/app/deps/perpdex-contract/deployments/' + web3_network_name)
    exchange_contract_filepath = os.path.join(abi_json_dirpath, 'PerpdexExchange.json')

    return get_contract_from_abi_json(
        w3,
        exchange_contract_filepath
    )
