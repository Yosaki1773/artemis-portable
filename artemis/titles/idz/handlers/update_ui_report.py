from core.config import CoreConfig

from ..config import IDZConfig
from .base import IDZHandlerBase


class IDZHandleUpdateUIReport(IDZHandlerBase):
    cmd_codes = [0x0084, 0x0084, 0x007E, 0x007E]
    name = "update_ui_report"

    def __init__(self, core_cfg: CoreConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(core_cfg, game_cfg, version)

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        return ret
