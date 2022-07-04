import pytest

from src.position_chaser import TakePositionChaser, TakePositionChaserConfig


@pytest.mark.parametrize(
    ids=[
        "do nothing 1",
        "do nothing 2",
        "open long",
        "add long",
        "doten long",
        "open short",
        "add short",
        "doten short",
    ],
    argnames="symbol, current_position, target_size, expected",
    argvalues=[
        ('BTC', 10, 10, None),
        ('BTC', -10, -10, None),
        ('BTC', 0, 20, ['BTC', 1, 20]),
        ('BTC', 10, 20, ['BTC', 1, 10]),
        ('BTC', -10, 20, ['BTC', 1, 30]),
        ('BTC', 0, -20, ['BTC', -1, 20]),
        ('BTC', -10, -20, ['BTC', -1, 10]),
        ('BTC', 10, -20, ['BTC', -1, 30]),
    ],
)
@pytest.mark.asyncio
async def test_take_position_chaser(symbol, current_position, target_size, expected, mocker):
    mocked_position_getter = mocker.MagicMock()
    mocked_position_getter.current_position.return_value = current_position

    mocked_taker = mocker.MagicMock()

    chaser = TakePositionChaser(
        config=TakePositionChaserConfig(symbol=symbol),
        position_getter=mocked_position_getter,
        taker=mocked_taker,
    )

    await chaser.execute(target_size=target_size)

    # assert
    if expected is None:
        chaser._taker.post_market_order.assert_not_called()
    else:
        chaser._taker.post_market_order.assert_called_with(
            symbol=expected[0],
            side_int=expected[1],
            size=expected[2],
        )
