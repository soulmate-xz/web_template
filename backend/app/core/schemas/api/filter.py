from datetime import date, datetime
from enum import Enum
from typing import Any, Generic, List, Optional, Sequence, TypeVar, Union
from typing import cast as t_cast

from pydantic import BaseModel, field_validator
from pydantic.fields import Field
from sqlalchemy import Column, Date, cast
from sqlalchemy.sql.elements import BinaryExpression

from backend.app.core.models import Base, db
from backend.app.utils.misc import escape_sql_symbols

OpType = TypeVar("OpType")
ValueType = TypeVar("ValueType")
NoneType = TypeVar("NoneType", bound=None)


class OperatorType(str, Enum):
    text = "text"
    number = "number"
    date = "date"
    match = "match"


class EqualOperator(str, Enum):
    eq = "=="


class MatchOperator(str, Enum):
    eq = "=="
    ne = "!="


class TextOperator(str, Enum):
    contains = "contains"
    not_contains = "!contains"
    eq = "=="
    ne = "!="


class NumberOperator(str, Enum):
    ne = "!="  # not equal
    eq = "=="  # equal
    le = "<="  # less than or equal
    lt = "<"  # less than
    ge = ">="  # greater than or equal
    gt = ">"  # greater than


class DateOperator(str, Enum):
    ne = "!="  # not equal
    eq = "=="  # equal
    le = "<="  # less than or equal
    lt = "<"  # less than
    ge = ">="  # greater than or equal
    gt = ">"  # greater than


class Option(BaseModel, Generic[ValueType]):
    value: ValueType
    display: Union[int, str]


StrOption = Option[str]
BoolOption = Option[bool]
NoneOption = Option[NoneType]
IntegerNumberOption = Option[int]
FloatNumberOption = Option[float]


class BaseFilter(BaseModel, Generic[OpType, ValueType]):
    op: OpType
    value: ValueType
    op_type: OperatorType
    options: Optional[List[Option]] = Field(None)

    def generate_orm_clause(self, orm: Union[Base, Column]) -> BinaryExpression:
        raise NotImplementedError  # pragma: no cover

    @classmethod
    async def get_options(cls) -> Optional[List[Any]]:
        ops = []
        options = cls.model_fields.get("options")
        if options and options.default:
            ops += options.default

        return ops if ops else None


class ArrayFilter(BaseFilter[MatchOperator, Any], Generic[ValueType]):
    op_type: OperatorType = OperatorType.match

    def generate_orm_clause(self, orm: Column) -> BinaryExpression:  # pragma: no cover
        if self.op == MatchOperator.eq:
            return orm.any(self.value)
        else:
            # elif self.op == MatchOperator.ne:
            return db.model.func.not_(orm.any(self.value))


class MatchFilter(BaseFilter[MatchOperator, Any], Generic[ValueType]):
    op_type: OperatorType = OperatorType.match

    def generate_orm_clause(self, orm: Column) -> BinaryExpression:  # pragma: no cover
        if self.op == MatchOperator.eq:
            return orm == self.value
        else:
            # elif self.op == MatchOperator.ne:
            return orm != self.value


class EqualFilter(BaseFilter[EqualOperator, Any], Generic[ValueType]):
    op_type: OperatorType = OperatorType.match

    def generate_orm_clause(self, orm: Column) -> BinaryExpression:
        return orm == self.value


class NoneFilter(MatchFilter[NoneType]):
    """
    请注意，如果需要空值筛选，请加上NoneFilter，其他Filter的value不应该是Optional的，否则会和NoneFilter产生歧义，
    如果用户上传的filter有空值，必须要保证该Filter进入NoneFilter里进行校验。
    """

    options: List[NoneOption] = [
        NoneOption(value=None, display="None"),
    ]


class TextFilter(BaseFilter[TextOperator, str]):
    op_type: OperatorType = OperatorType.text

    def generate_orm_clause(self, orm: Column) -> BinaryExpression:  # pragma: no cover
        if self.op == TextOperator.contains:
            return orm.like(f"%{escape_sql_symbols(self.value)}%")
        elif self.op == TextOperator.not_contains:
            return orm.notlike(f"%{escape_sql_symbols(self.value)}%")
        elif self.op == TextOperator.eq:
            return t_cast(BinaryExpression, orm == self.value)
        else:
            # elif self.op == TextOperator.ne:
            return t_cast(BinaryExpression, orm != self.value)


class IntegerNumberFilter(BaseFilter[NumberOperator, int]):
    op_type: OperatorType = OperatorType.number

    def generate_orm_clause(self, orm: Column) -> BinaryExpression:  # pragma: no cover
        if self.op == NumberOperator.ne:
            return t_cast(BinaryExpression, orm != self.value)
        elif self.op == NumberOperator.eq:
            return t_cast(BinaryExpression, orm == self.value)
        elif self.op == NumberOperator.le:
            return t_cast(BinaryExpression, orm <= self.value)
        elif self.op == NumberOperator.lt:
            return t_cast(BinaryExpression, orm < self.value)
        elif self.op == NumberOperator.ge:
            return t_cast(BinaryExpression, orm >= self.value)
        else:
            # elif self.op == NumberOperator.gt:
            return t_cast(BinaryExpression, orm > self.value)


class FloatNumberFilter(BaseFilter[NumberOperator, float]):
    op_type: OperatorType = OperatorType.number

    def generate_orm_clause(self, orm: Column) -> BinaryExpression:  # pragma: no cover
        if self.op == NumberOperator.ne:
            return t_cast(BinaryExpression, orm != self.value)
        elif self.op == NumberOperator.eq:
            return t_cast(BinaryExpression, orm == self.value)
        elif self.op == NumberOperator.gt:
            return t_cast(BinaryExpression, orm > self.value)
        elif self.op == NumberOperator.lt:
            return t_cast(BinaryExpression, orm < self.value)
        elif self.op == NumberOperator.ge:
            return t_cast(BinaryExpression, orm >= self.value)
        else:
            # elif self.op == NumberOperator.le:
            return t_cast(BinaryExpression, orm <= self.value)


class DateFilter(BaseFilter[DateOperator, datetime]):
    op_type: OperatorType = OperatorType.date

    @field_validator("value", mode="before")
    def format_date(cls, v: str) -> date:
        return datetime.strptime(v, "%Y-%m-%d")

    def generate_orm_clause(self, orm: Column) -> BinaryExpression:  # pragma: no cover
        if self.op == DateOperator.ne:
            return t_cast(BinaryExpression, cast(orm, Date) != self.value)
        elif self.op == DateOperator.eq:
            return t_cast(BinaryExpression, cast(orm, Date) == self.value)
        elif self.op == DateOperator.le:
            return t_cast(BinaryExpression, cast(orm, Date) <= self.value)
        elif self.op == DateOperator.lt:
            return t_cast(BinaryExpression, cast(orm, Date) < self.value)
        elif self.op == DateOperator.ge:
            return t_cast(BinaryExpression, cast(orm, Date) >= self.value)
        else:
            # elif self.op == DateOperator.gt:
            return t_cast(BinaryExpression, cast(orm, Date) > self.value)


# 当schemas中使用到Union[List[TextFilter],List[NoneFilter]]时，建议使用Union[TextFilters,NoneFilters]
NoneFilters = Sequence[NoneFilter]
TextFilters = Sequence[TextFilter]
IntegerNumberFilters = Sequence[IntegerNumberFilter]
FloatNumberFilters = Sequence[FloatNumberFilter]
DateFilters = Sequence[DateFilter]
