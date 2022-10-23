import os
from time import sleep

import asyncpg
from loguru import logger
from sanic import HTTPResponse, Sanic
from sanic.request import Request
from sanic.response import html, json
from uvloop import Loop


sanic_app = Sanic('BackendAPI')


@sanic_app.listener('before_server_start')
async def create_pg_pool(app: Sanic, loop: Loop) -> None:
    DATABASE = os.environ['DB_NAME']
    HOST = os.environ['DB_HOST']
    PASSWORD = os.environ['DB_PASSWORD']
    PORT = int(os.environ['DB_PORT'])
    USER = os.environ['DB_USER']

    while True:
        try:
            connection = await asyncpg.connect(
                database=DATABASE,
                host=HOST,
                password=PASSWORD,
                port=PORT,
                user=USER,
            )
        except ConnectionRefusedError:
            logger.warning('Postgres is not ready yet')
            sleep(1)
        else:
            await connection.close()
            break

    app.ctx.pg_pool = await asyncpg.create_pool(
        database=DATABASE,
        host=HOST,
        loop=loop,
        password=PASSWORD,
        port=PORT,
        user=USER,
        min_size=2,
        max_size=5,
    )
    logger.info('The pool is ready')


@sanic_app.listener('after_server_stop')
async def close_connection(app: Sanic, loop: Loop) -> None:
    async with app.ctx.pg_pool.acquire() as connection:
        await connection.close()


@sanic_app.route('/')
def index_page(request: Request) -> HTTPResponse:
    with open('./index.html') as f:
        return html(f.read())


@sanic_app.get('/tickers')
async def tickers_list(request: Request) -> HTTPResponse:
    async with request.app.ctx.pg_pool.acquire() as connection:
        try:
            query = 'SELECT DISTINCT ticker_id FROM tickers ORDER BY ticker_id'
            result = await connection.fetch(query)
            return json([r['ticker_id'] for r in result])
        except Exception as e:
            logger.exception(e)
            return HTTPResponse(status=500)


@sanic_app.get('/tickers/<ticker_id>')
async def datapoints(request: Request, ticker_id: int) -> HTTPResponse:
    last_ts = request.args.get('last_timestamp', 0)
    try:
        last_ts = int(last_ts)
    except ValueError:
        last_ts = 0

    query = '''
        SELECT
            price,
            updated_at * 1000 AS updated_at
        FROM
            tickers
        WHERE
            ticker_id = $1::INTEGER
            AND updated_at * 1000 > $2::BIGINT
        ORDER BY
            updated_at
    '''
    async with request.app.ctx.pg_pool.acquire() as connection:
        try:
            result = await connection.fetch(query, ticker_id, last_ts)
            return json([
                {'x': r['updated_at'], 'y': r['price']}
                for r in result
            ])
        except Exception as e:
            logger.exception(e)
            return HTTPResponse(status=500)
