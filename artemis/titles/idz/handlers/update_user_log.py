from core.config import CoreConfig

from ..config import IDZConfig
from .base import IDZHandlerBase


class IDZHandleUpdateUserLog(IDZHandlerBase):
    cmd_codes = [0x00BD, 0x00BD, 0x00AB, 0x00B3]
    name = "update_user_log"

    def __init__(self, core_cfg: CoreConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(core_cfg, game_cfg, version)

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        return ret
