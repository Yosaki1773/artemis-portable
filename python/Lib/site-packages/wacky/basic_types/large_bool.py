from construct import Adapter

from wacky.basic_types.integers import i32


class LargeBoolAdapter(Adapter):
    def _decode(self, obj: int, context, path: str) -> bool:
        return obj != 0

    def _encode(self, obj: bool, context, path) -> int:
        return int(obj)


LargeBool = LargeBoolAdapter(i32)
