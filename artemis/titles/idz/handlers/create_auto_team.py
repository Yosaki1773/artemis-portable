import struct
from operator import indexOf
from random import choice

from core.config import CoreConfig

from ..config import IDZConfig
from .base import IDZHandlerBase

AUTO_TEAM_NAMES = ["スピードスターズ", "レッドサンズ", "ナイトキッズ"]
FULL_WIDTH_NUMS = [
    "\uff10",
    "\uff11",
    "\uff12",
    "\uff13",
    "\uff14",
    "\uff15",
    "\uff16",
    "\uff17",
    "\uff18",
    "\uff19",
]


class IDZHandlerCreateAutoTeam(IDZHandlerBase):
    cmd_codes = [0x007B, 0x007B, 0x0077, 0x0077]
    rsp_codes = [0x007C, 0x007C, 0x0078, 0x0078]
    name = "create_auto_team"

    def __init__(self, core_cfg: CoreConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(core_cfg, game_cfg, version)
        self.size = 0x0CA0

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        aime_id = struct.unpack_from("<I", data, 0x04)[0]
        name = choice(AUTO_TEAM_NAMES)
        bg = indexOf(AUTO_TEAM_NAMES, name)
        number = (
            choice(FULL_WIDTH_NUMS) + choice(FULL_WIDTH_NUMS) + choice(FULL_WIDTH_NUMS)
        )

        tdata = {
            "id": aime_id,
            "bg": bg,
            "fx": 0,
        }

        tdata = {
            "id": aime_id,
            "name": (name + number),
            "bg": bg,
            "fx": 0,
        }
        tname = tdata["name"].encode("shift-jis")

        struct.pack_into("<I", ret, 0x0C, tdata["id"])
        struct.pack_into(f"{len(tname)}s", ret, 0x24, tname)
        struct.pack_into("<I", ret, 0x80, tdata["id"])
        struct.pack_into(f"<I", ret, 0xD8, tdata["bg"])
        struct.pack_into(f"<I", ret, 0xDC, tdata["fx"])

        return ret
