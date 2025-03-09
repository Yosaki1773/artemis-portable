from functools import reduce
from typing import List
from uuid import UUID

from construct import Adapter, Array

from wacky.basic_types.integers import u32

RawGUID = Array(4, u32)


class GUIDAdapter(Adapter):
    def _decode(self, obj: List[int], context, path: str) -> UUID:
        value = reduce(lambda x, y: (x << 32) + y, obj)
        return UUID(int=value)

    def _encode(self, obj: UUID, context, path) -> List[int]:
        return [
            int(obj.hex[:8], 16),
            int(obj.hex[8:16], 16),
            int(obj.hex[16:24], 16),
            int(obj.hex[24:], 16),
        ]


GUIDStruct = GUIDAdapter(RawGUID)
