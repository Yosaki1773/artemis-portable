from core.config import CoreConfig

from ..config import IDZConfig
from .base import IDZHandlerBase


class IDZHandleUpdateTeamPoints(IDZHandlerBase):
    cmd_codes = [0x0081, 0x0081, 0x007B, 0x007B]
    name = "unlock_profile"

    def __init__(self, core_cfg: CoreConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(core_cfg, game_cfg, version)

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        return ret
