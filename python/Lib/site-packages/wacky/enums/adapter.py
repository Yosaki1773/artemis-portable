from enum import IntEnum
from functools import partial
from typing import Type, TypeVar

from construct import Container, ExprAdapter, FormatField

T = TypeVar("T", bound=IntEnum)


def decode_int(enum_type: Type[T], obj: int, ctx: Container) -> T:
    return enum_type(obj)


def encode_enum(obj: T, ctx: Container) -> int:
    return obj.value


def enum_adapter(underlying_type: FormatField, enum_type: Type[IntEnum]) -> ExprAdapter:
    return ExprAdapter(
        subcon=underlying_type,
        decoder=partial(decode_int, enum_type),
        encoder=encode_enum,
    )
