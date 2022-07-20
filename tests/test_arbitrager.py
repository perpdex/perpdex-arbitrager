import asyncio

import pytest
from src.arbitrager import Arbitrager, ArbitragerConfig


@pytest.mark.asyncio
async def test_arbitrager(mocker):
    target_pos = 10

    mocked_pos_calculator1 = mocker.MagicMock()
    mocked_pos_calculator1.target_pos.return_value = target_pos

    mocked_pos_calculator2 = mocker.MagicMock()
    mocked_pos_calculator2.target_pos2.return_value = target_pos * -1

    mocked_chaser1 = mocker.MagicMock()
    future1 = asyncio.Future()
    future1.set_result(None)
    mocked_chaser1.execute.return_value = future1

    mocked_chaser2 = mocker.MagicMock()
    future2 = asyncio.Future()
    future2.set_result(None)
    mocked_chaser2.execute.return_value = future2

    arb = Arbitrager(
        pos_calculator1=mocked_pos_calculator1,
        pos_calculator2=mocked_pos_calculator2,
        position_chaser1=mocked_chaser1,
        position_chaser2=mocked_chaser2,
        config=ArbitragerConfig(trade_loop_sec=1, inverse=False),
    )

    # assert health check ok
    arb.start()
    assert arb.health_check() is True

    # wait 1 sec to make sure trade loop executed
    await asyncio.sleep(1)

    # force revert the running task
    arb._task.cancel()
    try:
        await arb._task
    except asyncio.CancelledError:
        pass

    # assert health check ng
    assert arb.health_check() is False
