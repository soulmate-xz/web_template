from typing import Any

import sqlalchemy as sa
from passlib.context import CryptContext

from backend.app.core.config import settings
from backend.app.core.models import Base, db


class User(Base):
    __tablename__ = f"{settings.PROJECT_NAME}_user"

    username = sa.Column(sa.String(255), index=True, comment="用户名")
    realname = sa.Column(sa.String(255), index=True, comment="姓名")
    password = sa.Column(sa.String(255), comment="密码")
    activated = sa.Column(sa.BOOLEAN, comment="是否启用")

    __table_args__ = {"comment": "用户信息表"}

    @classmethod
    async def create(cls, **kwargs: Any) -> "Base":
        PasswordContext = CryptContext(schemes=[settings.CRYPT_SCHEMA], deprecated="auto")
        kwargs["password"] = PasswordContext.hash(kwargs.get("password", "123456"))
        data = cls(**kwargs)
        async with db.async_session() as session:
            session.add(data)
            await session.commit()
            return data
