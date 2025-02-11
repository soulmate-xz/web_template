#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
res = await session.execute(delete(cls).where(and_(*clauses)).execution_options(synchronize_session="evaluate"))
synchronize_session可选参数
false 表示完全不更新 Python 中的对象
fetch 表示重新从数据库中加载一份对象
evaluate 表示在更新数据库的同时，也尽量在 Python 中的对象上使用同样的操作

https://docs.sqlalchemy.org/en/14/changelog/migration_20.html
https://ahmed-nafies.medium.com/tutorial-fastapi-with-sqlalchemy-async-orm-and-alembic-2fa68102f82d
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Sequence, Type, Union

import sqlalchemy as sa
from pydantic import BaseModel, Json, create_model
from sqlalchemy import URL, MetaData, Row, RowMapping, TextClause
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from backend.app.core.config import settings


class DatabaseValidationError(Exception):
    def __init__(self, message: str, field_value: Optional[tuple] = None) -> None:
        self.message = message
        self.field_value = field_value


class AsyncSessionMaker(async_sessionmaker):
    def __init__(self, *args: Any, commit: bool = True, **kwargs: Any) -> None:
        super(AsyncSessionMaker, self).__init__(*args, **kwargs)
        self._is_commit = commit

    async def __aenter__(self, *args: Any, **kwargs: Any) -> None:
        return super(AsyncSessionMaker, self).__aenter__(*args, **kwargs)  # type: ignore

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._is_commit:
            await self.commit()  # type: ignore
        return super(AsyncSessionMaker, self).__aexit__(exc_type, exc_val, exc_tb)  # type: ignore


class AsyncDatabase:
    def __init__(self) -> None:
        self.model = declarative_base(metadata=MetaData())
        self.logger = logging.getLogger("AsyncDatabase")
        if not settings.DATABASE_CONFIG.url:
            raise ValueError("缺失数据库配置信息")
        dsn = settings.DATABASE_CONFIG.url.render_as_string(hide_password=False)
        if isinstance(dsn, URL):
            dsn = dsn.render_as_string(hide_password=False)
        self.async_engine = create_async_engine(dsn, echo=settings.DB_ECHO_LOG)
        self.async_session: AsyncSessionMaker = AsyncSessionMaker(self.async_engine, expire_on_commit=False)

    async def execute(self, sql: str | TextClause) -> None:
        async with self.async_session() as session:
            await session.execute(sql)
            await session.commit()


db: AsyncDatabase = AsyncDatabase()


class Base(db.model):  # type: ignore
    """建议一个服务函数结束过后使用await db.close()关闭会话"""

    __abstract__ = True

    id = sa.Column(sa.BigInteger(), primary_key=True, autoincrement=True, comment="主键ID")
    created_on = sa.Column(
        sa.DateTime, default=datetime.now, server_default=sa.func.now(), index=True, comment="创建时间"
    )
    updated_on = sa.Column(
        sa.DateTime,
        default=datetime.now,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        index=True,
        comment="更新时间",
    )

    def to_dict(self) -> Dict[str, Union[str, None]]:
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    @classmethod
    async def create(cls, **kwargs: Any) -> "Base":
        data = cls(**kwargs)
        async with db.async_session() as session:
            session.add(data)
            await session.commit()
            return data

    @classmethod
    async def get_by(cls, **kwargs: Any) -> Optional["Base"]:
        clauses = [getattr(cls, k) == v for k, v in kwargs.items()]
        async with db.async_session() as session:
            res = await session.execute(
                sa.select(cls).where(sa.and_(*clauses)).execution_options(synchronize_session="evaluate")
            )
            return res.scalars().first()

    @classmethod
    async def get_all(cls, **kwargs: Any) -> Sequence[Union[Union[Row, RowMapping], Any]]:
        clauses = [getattr(cls, k) == v for k, v in kwargs.items()]
        async with db.async_session() as session:
            res = await session.execute(
                sa.select(cls).where(sa.and_(*clauses)).execution_options(synchronize_session="evaluate")
            )
            return res.scalars().all()

    async def update(self, **kwargs: Any) -> Optional["Base"]:
        async with db.async_session() as session:
            for k, v in kwargs.items():
                setattr(self, k, v)
            session.add(self)
            await session.commit()
        return self


def model_to_schema(db_model: Base) -> Type[BaseModel]:
    fields = {}
    for column in db_model.__table__.columns:
        python_type: Any
        name = str(column.name)
        if column.type.__visit_name__ == "UUID":
            python_type = uuid.UUID
        elif column.type.__visit_name__ in ["JSON", "JSONB"]:
            python_type = Json
        else:
            python_type = column.type.python_type
        assert python_type, f"Could not infer python_type for {column}"
        default = None
        if column.default is None and not column.nullable:
            default = ...
        fields[name] = (python_type, default)

    return create_model(db_model.__name__, **fields)  # type: ignore
