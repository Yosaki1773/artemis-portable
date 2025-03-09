from typing import Dict

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import ChuniConstants
from titles.chuni.sunplus import ChuniSunPlus


class ChuniLuminous(ChuniSunPlus):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_LUMINOUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        user_data["lastDataVersion"] = "2.20.00"
        return user_data

    async def handle_get_game_map_area_condition_api_request(self, data: Dict) -> Dict:
        return {"length": 0, "gameMapAreaConditionList": []}

    async def handle_get_user_c_mission_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        mission_id = data["missionId"]

        progress_list = []
        point = 0

        mission_data = await self.data.item.get_cmission(user_id, mission_id)
        progress_data = await self.data.item.get_cmission_progress(user_id, mission_id)

        if mission_data and progress_data:
            point = mission_data["point"]

            for progress in progress_data:
                progress_list.append(
                    {
                        "order": progress["order"],
                        "stage": progress["stage"],
                        "progress": progress["progress"],
                    }
                )

        return {
            "userId": user_id,
            "missionId": mission_id,
            "point": point,
            "userCMissionProgressList": progress_list,
        }

    async def handle_get_user_net_battle_ranking_info_api_request(
        self, data: Dict
    ) -> Dict:
        user_id = data["userId"]

        net_battle = {}
        net_battle_data = await self.data.profile.get_net_battle(user_id)

        if net_battle_data:
            net_battle = {
                "isRankUpChallengeFailed": net_battle_data["isRankUpChallengeFailed"],
                "highestBattleRankId": net_battle_data["highestBattleRankId"],
                "battleIconId": net_battle_data["battleIconId"],
                "battleIconNum": net_battle_data["battleIconNum"],
                "avatarEffectPoint": net_battle_data["avatarEffectPoint"],
            }

        return {
            "userId": user_id,
            "userNetBattleData": net_battle,
        }
