import pytest
from src.spread_calculator import TakeTakeSpreadCalculator


@pytest.mark.parametrize(
    ids=[
        "ask2 > bid2 > ask1 > bid1 -> return bid2/ask1-1",
        "ask2 > ask1 > bid2 > bid1 -> return 0.0",
        "ask2 > ask1 > bid1 > bid2 -> return 0.0",

        "ask1 > bid1 > ask2 > bid2 -> return bid1/ask2-1",
        "ask1 > ask2 > bid2 > bid1 -> return 0.0",
        "ask1 > ask2 > bid1 > bid2 -> return 0.0",
    ],
    argnames="ask1, bid1, ask2, bid2, expected",
    argvalues=[
        (120.0, 110.0, 140.0, 130.0, 130.0 / 120.0 - 1),
        (130.0, 110.0, 140.0, 120.0, 0.0),
        (130.0, 120.0, 140.0, 110.0, 0.0),

        (140.0, 130.0, 120.0, 110.0, (130.0 / 120.0 - 1) * -1),
        (140.0, 110.0, 130.0, 120.0, 0.0),
        (140.0, 120.0, 130.0, 110.0, 0.0),
    ],
)
def test_take_take_spread_calculator_spread(ask1, bid1, ask2, bid2, expected, mocker):
    mocked_price_getter1 = mocker.MagicMock()
    mocked_price_getter1.ask_price.return_value = ask1
    mocked_price_getter1.bid_price.return_value = bid1

    mocked_price_getter2 = mocker.MagicMock()
    mocked_price_getter2.ask_price.return_value = ask2
    mocked_price_getter2.bid_price.return_value = bid2
    spread_calculator = TakeTakeSpreadCalculator(
        price_getter1=mocked_price_getter1,
        price_getter2=mocked_price_getter2,
    )
    assert spread_calculator.spread() == pytest.approx(expected)
