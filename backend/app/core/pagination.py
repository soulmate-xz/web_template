#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
from collections.abc import Sequence as CSequence
from typing import (
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
)

from fastapi import FastAPI
from sqlalchemy import BinaryExpression, Column, Select, UnaryExpression, func, select
from sqlalchemy.sql import nullslast

from backend.app.core.models import db
from backend.app.core.schemas import RWModel
from backend.app.core.schemas.api.filter import BaseFilter
from backend.app.core.schemas.api.request import FilterRequest
from backend.app.core.schemas.api.response import PageListResponse

APP_FILTERS_REQUESTS = {}


def register_app_filters(app: FastAPI) -> None:
    for route in app.routes:
        path = route.path  # type: ignore
        requests = route.endpoint.__annotations__  # type: ignore
        for var, req in requests.items():
            if isinstance(req, type) and issubclass(req, FilterRequest):
                for field in req.model_fields.values():  # type: ignore
                    # if field.sub_fields and issubclass(field.sub_fields[0].type_, BaseFilter):
                    if hasattr(field, "annotation") and isinstance(field.annotation, type):
                        if issubclass(field.annotation, BaseFilter):
                            APP_FILTERS_REQUESTS[path] = req
                        if get_origin(field.annotation) is CSequence or get_origin(field.annotation) is Sequence:
                            for _ in get_origin(field.annotation):  # type: ignore[union-attr]
                                if issubclass(_, BaseFilter):
                                    APP_FILTERS_REQUESTS[path] = req
                                    break


def generate_orm_clauses(
    orm: Union[Dict[str, Column], Column, BinaryExpression],
    request: Optional[FilterRequest] = None,
    filters: Optional[Sequence[BaseFilter]] = None,
) -> List:
    clauses = []
    if request and isinstance(orm, dict) and not filters:
        for field_name, field_value in request.model_fields.items():
            annotation = (
                get_args(field_value.annotation)[0]
                if get_origin(field_value.annotation) is CSequence
                else field_value.annotation
            )
            if field_value.annotation and issubclass(annotation, BaseFilter):  # type: ignore[arg-type]
                filters = request.__getattribute__(field_name)
                if filters and orm.get(field_name) is not None:
                    clauses += [f.generate_orm_clause(orm[field_name]) for f in filters]
    elif filters:
        clauses += [f.generate_orm_clause(orm) for f in filters]  # type: ignore
    return clauses


async def paginate(
    query: Select,
    schema: Type[RWModel],
    order_by: Optional[Tuple[UnaryExpression, ...]] = None,
    null_last: bool = False,
    count: Optional[Select] = None,
    page: int = 1,
    page_size: int = 15,
) -> PageListResponse:
    query = query.execution_options(synchronize_session="evaluate")

    if count is None:
        count = query

    async with db.async_session() as session:
        amount = await session.scalar(select(func.count()).select_from(count.alias("_q")))
        if order_by is not None:
            if not isinstance(order_by, tuple):
                order_by = (order_by,)

            if null_last:
                order_by = tuple(nullslast(c) for c in order_by)
            query = query.order_by(*order_by)
        data = []
        total_pages = math.ceil(amount / page_size)
        if page <= total_pages:
            offset_value = (0 + (page - 1)) * page_size
            remain = amount - offset_value
            limit_value = min(remain, page_size)
            query = query.offset(offset_value).limit(limit_value)
            # 由于query是一个查询语句，所以直接返回了值，当为数据库对象时，返回数据库对象
            res = (await session.scalars(query)).all()
            data = [schema(**_.to_dict()) for _ in res]

        return PageListResponse(
            **{
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "amount": amount,
                "data": data,
            }
        )
