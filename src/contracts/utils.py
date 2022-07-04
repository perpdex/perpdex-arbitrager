from eth_account import Account
from web3 import Web3
from web3.middleware import (construct_sign_and_send_raw_middleware,
                             geth_poa_middleware)


def get_w3(network_name: str, web3_provider_uri: str, user_private_key: str = None):
    w3 = Web3(Web3.HTTPProvider(web3_provider_uri))

    if network_name in ['mumbai']:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if user_private_key is not None:
        user_account = Account().from_key(user_private_key)
        w3.middleware_onion.add(construct_sign_and_send_raw_middleware(user_account))
    return w3
