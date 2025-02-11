import inspect
import json
import os
import random
import string

import anyio
import pytest
from mock import MagicMock

from backend.app.utils.misc import import_submodules


def random_string(length=8):
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])


def var(prefix=None, length=8):
    if not prefix:
        prefix = ""
    return prefix + random_string(length=length)


async def import_test_data():
    models = import_submodules("backend.app.core.models")
    schemas = {}

    from backend.app.core.models import Base, model_to_schema

    for name, module in models.items():
        for _, item in inspect.getmembers(module):
            item: Base  # type: ignore[annotation-unchecked]
            if not isinstance(item, type(Base)) or item == Base:
                continue

            schemas[item.__tablename__] = item
    # async with db.transaction():
    for filepath in os.listdir("tests/data/"):
        if not filepath.endswith(".json"):
            continue

        table_name, _ = filepath.split(".")
        table = schemas.get(table_name)
        if not table:
            continue
        schema = model_to_schema(table)

        ids = []
        async with await anyio.open_file(f"tests/data/{filepath}", "r", encoding="utf-8") as inf:
            lines = json.loads(await inf.read())
            for data in lines:
                ids.append(data["id"])
                row = schema(**data).dict()
                await table(**row).create()  # noqa

        assert ids == list(range(1, len(lines) + 1))


def skip_if_not_testing(func):
    from backend.app.core.config import settings

    return pytest.mark.skipif(not settings.TESTING, reason="未确保导入测试数据的情况下，不会进行该用例测试。")(func)


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class Patches:
    def __init__(self, patches):
        self.patches = patches

    def __enter__(self):
        for patch in self.patches:
            patch.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch in self.patches:
            patch.__exit__(exc_type, exc_val, exc_tb)
