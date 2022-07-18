import asyncio
import fire
import yaml
from logging import getLogger, config

from src import resolver
from src.debug import setCollateralBalance, printAccountInfo

async def main():
    with open("main_logger_config.yml", encoding='UTF-8') as f:
        y = yaml.safe_load(f.read())
        config.dictConfig(y)

    logger = getLogger(__name__)
    logger.info('start')

    while True:
        arb = resolver.create_perpdex_binance_arbitrager()

        arb.start()
        while arb.health_check():
            logger.debug('health check ok')
            await asyncio.sleep(30)
        logger.warning('Restarting Arb bot')


class Cli:
    """arbitrage bot for perpdex"""

    def run(self):
        """run arbitrage bot"""
        asyncio.run(main())

    def setCollateralBalance(self, balance, account=None):
        """call setCollateralBalance (for testnet)"""
        setCollateralBalance(balance, account)
        logger = getLogger(__name__)
        logger.info('finished')

    def accountInfo(self, account=None):
        printAccountInfo(account)

if __name__ == '__main__':
    fire.Fire(Cli)
