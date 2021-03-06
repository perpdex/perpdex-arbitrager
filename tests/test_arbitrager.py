import asyncio

import pytest
from src.arbitrager import Arbitrager, ArbitragerConfig


@pytest.mark.asyncio
async def test_arbitrager(mocker):
    target_pos = 10

    mocked_target_pos_calculator = mocker.MagicMock()
    mocked_target_pos_calculator.target_pos.return_value = target_pos

    mocked_chaser1 = mocker.MagicMock()
    future1 = asyncio.Future()
    future1.set_result(None)
    mocked_chaser1.execute.return_value = future1

    mocked_chaser2 = mocker.MagicMock()
    future2 = asyncio.Future()
    future2.set_result(None)
    mocked_chaser2.execute.return_value = future2

    mocked_rebalancer = mocker.MagicMock()
    future3 = asyncio.Future()
    future3.set_result(None)
    mocked_rebalancer.rebalance.return_value = future3
 
    arb = Arbitrager(
        target_pos_calculator=mocked_target_pos_calculator,
        position_chaser1=mocked_chaser1,
        position_chaser2=mocked_chaser2,
        liquidity_rebalancer=mocked_rebalancer,
        config=ArbitragerConfig(trade_loop_sec=1, rebalance_loop_sec=1, inverse=False),
    )

    # assert health check ok
    arb.start()
    assert arb.health_check() is True

    # wait 1 sec to make sure trade loop executed
    await asyncio.sleep(1)

    # force revert the running _trade task
    arb._task_t.cancel()
    try:
        await arb._task_t
    except asyncio.CancelledError:
        pass

    # assert health check ng
    assert arb.health_check() is False

    # restart arb
    arb.start()
    assert arb.health_check() is True
    await asyncio.sleep(1)

    # force revert the running _rebalace task
    arb._task_m.cancel()
    try:
        await arb._task_m
    except asyncio.CancelledError:
        pass

    # assert health check ng
    assert arb.health_check() is False
