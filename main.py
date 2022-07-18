import asyncio
import time
import yaml
from logging import getLogger, config

from src import resolver


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
            await asyncio.sleep(30)
        logger.warning('Restarting Arb bot')


if __name__ == '__main__':
    asyncio.run(main())
