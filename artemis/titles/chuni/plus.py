from typing import Dict

from core.config import CoreConfig
from titles.chuni.base import ChuniBase
from titles.chuni.config import ChuniConfig
from titles.chuni.const import ChuniConstants


class ChuniPlus(ChuniBase):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_PLUS

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.05.00"
        return ret
