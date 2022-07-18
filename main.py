import time
from logging import getLogger

from src import resolver


def main():
    logger = getLogger(__name__)
    while True:
        arb = resolver.create_perpdex_binance_arbitrager()

        arb.start()
        while arb.health_check():
            time.sleep(30)
        logger.warning('Restarting Arb bot')
