from src.resolver import create_perpdex_binance_arbitrager
from src.arbitrager import Arbitrager


def test_create_perpdex_binance_arbitrager_smoke(monkeypatch):
    monkeypatch.setenv('BINANCE_API_KEY', 'dummy')
    monkeypatch.setenv('BINANCE_SECRET', 'dummy')
    arb = create_perpdex_binance_arbitrager()
    assert type(arb) is Arbitrager
