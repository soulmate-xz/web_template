#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Union
from uuid import UUID

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, ConfigDict

# 注意这里的类型顺序
JSONValue = Union[int, float, bool, str, None, Dict[str, Any], List[Any]]
JSONType = Union[JSONValue, List[JSONValue], Dict[str, JSONValue]]
UUIDType = Union[str, UUID]


class RWModel(BaseModel):

    model_config = ConfigDict(populate_by_name=True)


class PublicSortColumns(str, Enum):
    CREATED_ON = "created_on"
    UPDATED_ON = "updated_on"


class UnixDateTime(datetime):
    @classmethod
    def __get_validators__(cls) -> Iterable[Callable]:
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, datetime]) -> datetime:
        return datetime.fromisoformat(v).replace(tzinfo=None) if isinstance(v, str) else v


def days_ago(days: int = 30) -> date:
    return datetime.now().date() - timedelta(days=days)


def months_ago(months: int = 3) -> date:
    return datetime.now().date() - relativedelta(months=months)


def default_date() -> date:
    return datetime.now().date()


def current_month() -> date:
    return datetime(datetime.now().year, datetime.now().month, 1)
