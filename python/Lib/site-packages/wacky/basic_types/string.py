from dataclasses import dataclass
from typing import Optional

from construct import Adapter, CString, If, IfThenElse
from construct_typed import DataclassMixin, DataclassStruct, csfield

from wacky.basic_types.integers import i32


@dataclass
class RawString(DataclassMixin):
    signed_length: int = csfield(i32)
    value: Optional[str] = csfield(
        If(
            lambda this: this.signed_length != 0,
            IfThenElse(
                lambda this: this.signed_length < 0,
                CString("utf-16-le"),
                CString("ascii"),
            ),
        )
    )


class StringAdapter(Adapter):
    def _decode(self, obj: RawString, context, path: str) -> str:
        return obj.value or ""

    def _encode(self, obj: str, context, path) -> RawString:
        if not obj:
            return RawString(signed_length=0, value=obj)
        elif obj.isascii():
            return RawString(signed_length=len(obj) + 1, value=obj)
        else:
            return RawString(signed_length=-(len(obj) + 1), value=obj)


String = StringAdapter(DataclassStruct(RawString))
