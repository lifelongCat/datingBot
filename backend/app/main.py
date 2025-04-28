import logging
from contextlib import asynccontextmanager
from datetime import datetime

import pytz
from fastapi import FastAPI, HTTPException, Request, status
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.repositories import PostgresRepository
from app.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    instrumentator.expose(app, tags=['metrics'])
    yield


app = FastAPI(
    root_path='/api',
    lifespan=lifespan
)
app.include_router(router)

instrumentator = Instrumentator(
    should_group_status_codes=True,
    excluded_handlers=['/metrics', '/docs', '/openapi.json']
).instrument(app, latency_lowr_buckets=(0.1, 0.25, 0.5, 0.75, 1))


@app.middleware('http')
async def last_activity_middleware(request: Request, call_next):
    # healthcheck and metrice endpoints
    if request.url.path in (
            '/test', '/api/test',
            '/metrics', '/api/metrics',
            '/docs', '/api/openapi.json'
    ):
        return await call_next(request)
    if 'X-Telegram-ID' not in request.headers:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Не указан заголовок X-Telegram-ID")
    request.state.telegram_id = int(request.headers['X-Telegram-ID'])

    not_authenticated_routes = (
        ('POST', '/users'),
        ('GET', '/check_is_registered'),
    )
    if (request.method, request.url.path) not in not_authenticated_routes:
        await PostgresRepository.update_user(
            telegram_id=request.state.telegram_id,
            last_activity=datetime.now(pytz.UTC).replace(tzinfo=None)
        )
    return await call_next(request)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc) -> JSONResponse:
    logging.getLogger().error((
        f'{request.method} {request.url.path} - {exc.status_code} - "{exc.detail}"\n'
        f'headers: {", ".join(f"{key} = {value}" for key, value in request.headers.items())}\n'
        f'path params: {", ".join(f"{key} = {value}" for key, value in request.path_params.items())}\n'
        f'query params: {", ".join(f"{key} = {value}" for key, value in request.query_params.items())}'
    ))
    return JSONResponse(
        content={'detail': exc.detail},
        status_code=exc.status_code
    )


@app.get('/test', status_code=status.HTTP_204_NO_CONTENT)
async def test_is_started() -> None:
    return
