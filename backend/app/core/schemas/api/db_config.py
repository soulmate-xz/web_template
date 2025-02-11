#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.fields import Field
from pydantic_core.core_schema import ValidationInfo
from sqlalchemy import URL
from starlette.datastructures import Secret


class DatabaseURL(BaseModel):
    drivername: str = Field(..., alias="driver", description="The database driver.")
    host: str = Field("localhost", description="Server host.")
    port: Optional[Union[str, int]] = Field(None, description="Server access port.")
    username: Optional[str] = Field(None, alias="user", description="Username")
    password: Optional[Union[str, Secret]] = Field(None, description="Password")
    database: str = Field(..., description="Database name.")
    url: Optional[URL] = None

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @field_validator("url", mode="after")
    def build_url(cls, v: Any, values: ValidationInfo) -> URL:
        if isinstance(v, URL):  # pragma: no cover
            return v
        args = {k: v for k, v in values.data.items() if v is not None}
        return URL.create(**args)
