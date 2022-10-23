import os
import signal
from datetime import datetime
from random import random
from time import mktime, sleep
from types import FrameType, TracebackType
from typing import Type

import psycopg2
from loguru import logger


TICKERS_NUMBER = 100
SLEEP_TIME = 1


class Ticker:

    def __init__(self, ticker_id: int) -> None:
        self.ticker_id = ticker_id
        self.price = 0

    def update_price(self) -> int:
        self.price += self.generate_movement()

    @staticmethod
    def generate_movement() -> int:
        movement = -1 if random() < 0.5 else 1
        return movement


class Connection:
    database = os.environ['DB_NAME']
    host = os.environ['DB_HOST']
    password = os.environ['DB_PASSWORD']
    port = int(os.environ['DB_PORT'])
    user = os.environ['DB_USER']

    @classmethod
    def _get_connection(cls) -> psycopg2.extensions.connection:
        while True:
            try:
                return psycopg2.connect(
                    database=cls.database,
                    user=cls.user,
                    password=cls.password,
                    host=cls.host,
                    port=cls.port
                )
            except psycopg2.OperationalError:
                logger.warning('Postgres is not ready yet')
                sleep(1)

    def __enter__(self) -> psycopg2.extensions.cursor:
        self._connection = self._get_connection()
        self._connection.autocommit = True
        return self._connection.cursor()

    def __exit__(
        self,
        exc_type: Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None
    ) -> None:
        self._connection.close()


class Main:
    table_name = os.environ['DB_TABLE']
    query = f'INSERT INTO {table_name} (updated_at, ticker_id, price) VALUES (%s, %s, %s)'

    def __init__(self, cursor: psycopg2.extensions.cursor) -> None:
        self.cursor = cursor
        self._tickers = tuple(Ticker(i) for i in range(TICKERS_NUMBER))
        self._shutdown_flag = False
        signal.signal(signal.SIGINT, self._set_stop_flag)
        signal.signal(signal.SIGTERM, self._set_stop_flag)

    def run(self) -> None:
        logger.info('Starting main loop')
        while not self._shutdown_flag:
            self._update_prices()
            sleep(SLEEP_TIME)
        logger.info('Main loop stopped')

    def _set_stop_flag(self, signum: int, frame: FrameType) -> None:
        logger.info('Got shutdown signal')
        self._shutdown_flag = True

    def _update_prices(self) -> None:
        now = datetime.utcnow()
        updated_at = int(mktime(now.timetuple()))
        new_values = []
        for ticker in self._tickers:
            ticker.update_price()
            new_values.append((updated_at, ticker.ticker_id, ticker.price))
        self.cursor.executemany(self.query, new_values)


def main() -> None:
    with Connection() as cursor:
        Main(cursor).run()


if __name__ == '__main__':
    main()
