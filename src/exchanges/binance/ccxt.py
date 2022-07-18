

def ccxt_default_type(symbol: str):
    if symbol in ['ASTRUSDT']:
        return 'spot'
    if 'USDT' in symbol:
        return 'future'  # linear, USD-M
    elif 'USD_PERP' in symbol or '/USD' in symbol:
        return 'delivery'  # inverse, COIN-M
    raise ValueError('symbol must be either linear or delivery')


# for test
def _set_leverageBrackets(ccxt_binance, symbol: str):
    """
    https://binance-docs.github.io/apidocs/delivery/en/#notional-bracket-for-pair-user_data
    """
    if symbol in ('BTCUSD_PERP', 'BTC/USD'):
        """
        >>> ccxt_exchange = ccxt.binance({...})
        >>> ccxt_exchange.load_leverage_brackets()
        >>> ccxt_exchange.options['leverageBrackets']['BTC/USD']
        """
        ccxt_binance.options['leverageBrackets'] = {
            'BTC/USD': [
                ['0', '0.004'],
                ['5', '0.005'],
                ['10', '0.01'],
                ['20', '0.025'],
                ['50', '0.05'],
                ['100', '0.1'],
                ['200', '0.125'],
                ['400', '0.15'],
                ['1000', '0.25'],
                ['1500', '0.5'],
            ],
        }
