from core.config import CoreConfig

from ..config import IDZConfig
from .base import IDZHandlerBase


class IDZHandlerSaveTopic(IDZHandlerBase):
    cmd_codes = [0x009A, 0x009A, 0x0091, 0x0091]
    rsp_codes = [0x009B, 0x009B, 0x0092, 0x0092]
    name = "save_topic"

    def __init__(self, core_cfg: CoreConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(core_cfg, game_cfg, version)
        self.size = 0x05D0

    def handle(self, data: bytes) -> bytearray:
        return super().handle(data)
