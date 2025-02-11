#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum

from pydantic import ConfigDict, Field

from backend.app.core.schemas import RWModel


class OrderBy(str, Enum):
    DESC = "desc"
    ASC = "asc"


class DateTypes(str, Enum):
    minute = "minute"
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    year = "year"


class LoginRequest(RWModel):
    username: str
    password: str

    model_config = ConfigDict(json_schema_extra={"example": {"username": "admin", "password": "admin"}})


class FilterRequest(RWModel):
    # 条件筛选器Request
    pass


class OffsetLimitRequest(FilterRequest):
    offset: int = Field(default=0, title="页码", ge=0)
    limit: int = Field(default=15, title="每页条数", gt=0, le=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "offset": 0,
                "limit": 15,
            }
        }
    )


class PageListRequest(FilterRequest):
    page: int = Field(default=1, title="页码", gt=0)
    page_size: int = Field(default=15, title="每页条数", gt=0, le=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 15,
            }
        }
    )
