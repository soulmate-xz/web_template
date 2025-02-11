from typing import Optional

from sqlalchemy import and_, select

from backend.app.core.models import Base
from backend.app.core.models.user import User as UserORM
from backend.app.core.pagination import generate_orm_clauses, paginate
from backend.app.core.schemas.api.request import OrderBy
from backend.app.core.schemas.api.response import PageListResponse
from backend.app.core.schemas.user import User, UserPageListRequest


class UserService:

    @classmethod
    async def init_admin(cls) -> None:
        user: Optional[Base] = await UserORM.get_by(username="admin")
        if not user:
            await UserORM.create(username="admin", realname="管理员", password="admin", activated=True)

    @classmethod
    async def list_user(cls, request: UserPageListRequest) -> PageListResponse:
        clauses = []
        clauses += generate_orm_clauses(
            {"username": UserORM.username, "realname": UserORM.realname, "activated": UserORM.activated},
            request=request,
        )

        query = select(UserORM).where(and_(True, *clauses))
        order_by = (
            getattr(UserORM, request.sort_k).desc()
            if request.sort == OrderBy.DESC
            else getattr(query.c, request.sort_k).asc()
        )
        # 处理排序
        return await paginate(
            query=query, schema=User, page=request.page, page_size=request.page_size, order_by=order_by
        )
