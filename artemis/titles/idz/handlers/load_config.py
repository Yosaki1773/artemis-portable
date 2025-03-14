import struct

from core.config import CoreConfig

from ..config import IDZConfig
from ..const import IDZConstants
from .base import IDZHandlerBase


class IDZHandlerLoadConfigA(IDZHandlerBase):
    cmd_codes = [0x0004] * IDZConstants.NUM_VERS
    rsp_codes = [0x0005] * IDZConstants.NUM_VERS
    name = "load_config_a"

    def __init__(self, core_cfg: CoreConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(core_cfg, game_cfg, version)
        self.size = 0x01A0

        if self.version > 1:
            self.size = 0x05E0

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        struct.pack_into("<H", ret, 0x02, 1)
        struct.pack_into("<I", ret, 0x16, 230)
        return ret


class IDZHandlerLoadConfigB(IDZHandlerBase):
    cmd_codes = [0x00AB, 0x00AB, 0x00A0, 0x00A0]
    rsp_codes = [0x00AC, 0x00AC, 0x00A1, 0x00A1]
    name = "load_config_b"

    def __init__(self, core_cfg: CoreConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(core_cfg, game_cfg, version)
        self.size = 0x0230

        if self.version > 1:
            self.size = 0x0240

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        struct.pack_into("<H", ret, 0x02, 1)
        return ret
