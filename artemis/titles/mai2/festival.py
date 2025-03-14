from typing import Dict

from core.config import CoreConfig
from titles.mai2.config import Mai2Config
from titles.mai2.const import Mai2Constants
from titles.mai2.universeplus import Mai2UniversePlus


class Mai2Festival(Mai2UniversePlus):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_FESTIVAL

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker
        user_data["lastDataVersion"] = "1.30.00"
        return user_data

    async def handle_user_login_api_request(self, data: Dict) -> Dict:
        user_login = await super().handle_user_login_api_request(data)
        # useless?
        user_login["Bearer"] = "ARTEMiSTOKEN"
        return user_login

    async def handle_get_user_recommend_rate_music_api_request(
        self, data: Dict
    ) -> Dict:
        """
        userRecommendRateMusicIdList: list[int]
        """
        return {"userId": data["userId"], "userRecommendRateMusicIdList": []}

    async def handle_get_user_recommend_select_music_api_request(
        self, data: Dict
    ) -> Dict:
        """
        userRecommendSelectionMusicIdList: list[int]
        """
        return {"userId": data["userId"], "userRecommendSelectionMusicIdList": []}
