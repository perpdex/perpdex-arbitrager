import asyncio
import fire
import yaml
from logging import getLogger, config

from src import resolver
from src.debug import setCollateralBalance, printAccountInfo
from src.debug_price_feed_reporter import create_debug_price_feed_reporter

async def main(restart):
    logger = getLogger(__name__)
    logger.info('start')

    while True:
        arb = resolver.create_perpdex_binance_arbitrager()

        arb.start()
        while arb.health_check():
            logger.debug('health check ok')
            await asyncio.sleep(30)

        if not restart:
            break
        logger.warning('Restarting Arb bot')

    logger.warning('exit')


async def main_debug_price_feed_reporter():
    logger = getLogger(__name__)
    logger.info('start')

    bot = create_debug_price_feed_reporter()

    bot.start()
    while bot.health_check():
        logger.debug('health check ok')
        await asyncio.sleep(30)

    logger.warning('exit')


class Cli:
    """arbitrage bot for perpdex"""

    def run(self, restart: bool=False):
        """run arbitrage bot"""
        asyncio.run(main(restart))

    def run_debug_price_feed_reporter(self):
        """run arbitrage bot"""
        asyncio.run(main_debug_price_feed_reporter())

    def setCollateralBalance(self, balance, account=None):
        """call setCollateralBalance (for testnet)"""
        setCollateralBalance(balance, account)
        logger = getLogger(__name__)
        logger.info('finished')

    def accountInfo(self, account=None):
        printAccountInfo(account)

if __name__ == '__main__':
    with open("main_logger_config.yml", encoding='UTF-8') as f:
        y = yaml.safe_load(f.read())
        config.dictConfig(y)

    fire.Fire(Cli)
