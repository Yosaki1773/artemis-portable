from typing import Dict

from core.config import CoreConfig
from titles.mai2.buddies import Mai2Buddies
from titles.mai2.const import Mai2Constants
from titles.mai2.config import Mai2Config


class Mai2BuddiesPlus(Mai2Buddies):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_BUDDIES_PLUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker
        user_data["lastDataVersion"] = "1.45.00"
        return user_data

    async def handle_get_game_weekly_data_api_request(self, data: Dict) -> Dict:
        return {
            "gameWeeklyData": {
                "missionCategory": 0,
                "updateDate": "2024-03-21 09:00:00",
                "beforeDate": "2099-12-31 00:00:00"
            }
        }

    async def handle_create_token_api_request(self, data: Dict) -> Dict:
        return {
            "Bearer": "ARTEMiSTOKEN" # duplicate of handle_user_login_api_request from Mai2Festival
        }

    async def handle_remove_token_api_request(self, data: Dict) -> Dict:
        return {}

    async def handle_get_user_friend_bonus_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "returnCode": 1,
            "getMiles": 0
        }
    
    async def handle_get_user_shop_stock_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "userShopStockList": []
        }

    async def handle_get_user_mission_data_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "userMissionDataList": [],
            "userWeeklyData": {
                "lastLoginWeek": "2024-03-21 09:00:00",
                "beforeLoginWeek": "2099-12-31 00:00:00",
                "friendBonusFlag": False
            }
        }
