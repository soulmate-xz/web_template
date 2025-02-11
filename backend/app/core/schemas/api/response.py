#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
from typing import Dict, Optional, Union
from uuid import UUID

from pydantic import Field

from backend.app.core.schemas import RWModel


class ResponseCode(int, Enum):
    # API接口返回状态码
    SUCCESS = 200
    ERROR = 500
    UNKNOWN_REQUEST = 400
    # 无权限
    PERMISSION_DENIED = 403
    # 未找到
    NOT_FOUND = 404


class BoolResponse(RWModel):
    code: ResponseCode = ResponseCode.SUCCESS
    message: str


class DataResponse(RWModel):
    code: ResponseCode = ResponseCode.SUCCESS
    message: str = "操作成功"
    data: Optional[Union[Dict, RWModel]] = Field(None)


class StringDataResponse(RWModel):
    code: ResponseCode = ResponseCode.SUCCESS
    message: str = "操作成功"
    data: Optional[Union[UUID, str]] = Field(None)


class DataListResponse(RWModel):
    code: ResponseCode = ResponseCode.SUCCESS
    message: str = "操作成功"
    data: Optional[list] = Field(None)


class PageListResponse(RWModel):
    code: ResponseCode = ResponseCode.SUCCESS
    message: str = "操作成功"
    page: int
    page_size: int
    total_pages: int = 1
    amount: int = 0
    data: Optional[list] = Field(None)


class OffsetLimitResponse(RWModel):
    code: ResponseCode = ResponseCode.SUCCESS
    message: str = "操作成功"
    offset: int
    limit: int
    amount: int = 0
    data: Optional[list] = Field(None)
