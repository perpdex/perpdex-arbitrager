from src.resolver import binance_perpdex_arbitrager
from src.arbitrager import Arbitrager


def test_binance_perpdex_arbitrager_smock(monkeypatch):
    monkeypatch.setenv('BINANCE_API_KEY', 'dummy')
    monkeypatch.setenv('BINANCE_SECRET', 'dummy')
    arb = binance_perpdex_arbitrager()
    assert type(arb) is Arbitrager
