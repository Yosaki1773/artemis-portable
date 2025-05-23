from typing import Dict

from core.config import CoreConfig
from titles.chuni.base import ChuniBase
from titles.chuni.config import ChuniConfig
from titles.chuni.const import ChuniConstants


class ChuniCrystal(ChuniBase):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_CRYSTAL

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.40.00"
        return ret
