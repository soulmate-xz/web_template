from typing import List

from pydantic import Field

from backend.app.core.schemas import RWModel
from backend.app.core.schemas.api.filter import OperatorType, Option
from backend.app.core.schemas.api.response import DataListResponse


class Filter(RWModel):
    name: str = Field(..., title="参数名称")
    op_type: OperatorType = Field(..., title="操作符类型")
    category: str = Field(..., title="中文名称")
    ops: List[str] = Field(..., title="运算符")
    options: List[Option] = Field(default_factory=list, title="选择型可选项")


class FilterResponse(DataListResponse):
    data: List[Filter]
