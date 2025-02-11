import asyncio
import datetime
from typing import AsyncGenerator, List

import alembic.config
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Headers

from backend.app.core.config import settings
from backend.app.core.models.user import User as UserORM
from tests.testing_helpers import import_test_data


@pytest.fixture(scope="session", autouse=True)
async def settings_constant():

    settings.TESTING = True
    settings.DEBUG = False

    settings.DB_NAME = f"{settings.PROJECT_NAME}_test"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def apply_migrations(settings_constant: None):
    alembic.config.main(argv=["downgrade", "base"])
    alembic.config.main(argv=["upgrade", "head"])
    yield
    alembic.config.main(argv=["downgrade", "base"])


@pytest.fixture(scope="session")
def load_app(apply_migrations: None) -> FastAPI:
    from backend.asgi import app

    return app


@pytest.fixture(scope="session")
async def initialized_app(load_app: FastAPI) -> AsyncGenerator[FastAPI, None]:
    async with LifespanManager(load_app):
        await import_test_data()
        yield load_app


@pytest.fixture(scope="session")
async def client(initialized_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=initialized_app), base_url="http://testserver") as client:
        yield client


@pytest.fixture(scope="session")
async def login(initialized_app: FastAPI):
    from backend.app.core.auth import create_access_token

    clients = []

    async def _login(args) -> AsyncClient | List[AsyncClient]:
        nonlocal initialized_app
        sessions = []
        if not isinstance(args, list):
            args = [args]
        for username in args:
            if isinstance(username, str):
                user = await UserORM.get_by(username=username)
            else:
                user = await UserORM.get_by(id=username)

            assert user is not None
            expired_at = datetime.datetime.now() + datetime.timedelta(days=7)
            client = AsyncClient(
                transport=ASGITransport(app=initialized_app),
                base_url="http://testserver",
                headers={"Content-Type": "application/json"},
            )
            token = create_access_token(data={"sub": user.username}, expire=expired_at)
            client.headers = Headers({"Authorization": f"Bearer {token}"})
            clients.append(client)
            sessions.append(client)
        if len(sessions) == 1:
            return sessions.pop()
        return sessions

    yield _login
    for c in clients:
        await c.__aexit__()


@pytest.fixture(scope="session")
async def create_sessions(login):

    async def _clients(users=None):
        client_sessions = {}

        admin_session = await login("admin")
        client_sessions["admin"] = admin_session

        if isinstance(users, list):  # todo: 用户权限及角色初始化
            for username in users:
                exists_user = await UserORM.get_by(username=username)
                if exists_user:
                    uid = exists_user.id
                else:
                    uid = (await UserORM.create(username=username, realname=username, activated=True)).id
                sessions = await login(uid)  # type: ignore
                client_sessions[username] = sessions

        return client_sessions

    return _clients
