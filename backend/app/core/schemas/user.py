from typing import List, Optional

from pydantic import ConfigDict, Field, field_validator

from backend.app.core.schemas import PublicSortColumns, RWModel
from backend.app.core.schemas.api.filter import BoolOption, MatchFilter, TextFilters
from backend.app.core.schemas.api.request import OrderBy, PageListRequest
from backend.app.core.schemas.api.response import PageListResponse


class ActivatedOptionsFilter(MatchFilter[bool]):
    options: List[BoolOption] = [
        BoolOption(value=True, display="启用"),
        BoolOption(value=False, display="禁用"),
    ]

    @field_validator("value", mode="before")
    def value_(cls, v: bool) -> bool:
        if not isinstance(v, bool):
            raise ValueError("用户启用状态搜索仅支持布尔型的值 True/False")
        return v


class UserPageListRequest(PageListRequest):
    username: Optional[TextFilters] = Field(None, title="用户名")
    realname: Optional[TextFilters] = Field(None, title="姓名")
    activated: Optional[ActivatedOptionsFilter] = Field(None, title="启用状态")

    sort: OrderBy = OrderBy.DESC
    sort_k: PublicSortColumns = PublicSortColumns.CREATED_ON

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 15,
                "realname": [{"op": "==", "value": "姓名"}],
                "username": [{"op": "contains", "value": "miko"}],
                "created_on": [{"op": "==", "value": "2021-08-24"}],
                "updated_on": [{"op": "==", "value": "2021-08-24"}],
                "activated": [{"op": "==", "value": True}],
            }
        }
    )


class User(RWModel):
    username: str = Field(description="用户名")
    realname: str = Field(description="姓名")
    activated: bool = Field(description="是否启用")


class UserPageListResponse(PageListResponse):
    data: List[User]
