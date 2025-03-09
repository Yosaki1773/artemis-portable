from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from construct_typed import DataclassMixin, DataclassStruct, csfield

from wacky.basic_types.integers import i32


class IndexKind(Enum):
    NULL = auto()
    IMPORT = auto()
    EXPORT = auto()


@dataclass
class PackageIndex(DataclassMixin):
    signed_value: int = csfield(i32)

    @property
    def kind(self) -> IndexKind:
        if self.signed_value == 0:
            return IndexKind.NULL
        elif self.signed_value < 0:
            return IndexKind.IMPORT
        else:
            return IndexKind.EXPORT

    @property
    def value(self) -> Optional[int]:
        kind = self.kind
        if kind == IndexKind.NULL:
            return None
        elif kind == IndexKind.IMPORT:
            return -self.signed_value - 1
        else:
            return self.signed_value - 1

    def jsonify(self) -> int:
        return self.signed_value

    def update(self, new: int):
        self.signed_value = new


PackageIndexStruct = DataclassStruct(PackageIndex)
