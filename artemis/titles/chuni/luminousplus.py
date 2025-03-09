from datetime import timedelta
from typing import Dict

from core.config import CoreConfig
from titles.chuni.luminous import ChuniLuminous
from titles.chuni.const import ChuniConstants
from titles.chuni.config import ChuniConfig


class ChuniLuminousPlus(ChuniLuminous):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_LUMINOUS_PLUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # Does CARD MAKER 1.35 work this far up?
        user_data["lastDataVersion"] = "2.25.00"
        return user_data

    async def handle_get_user_c_mission_list_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        user_mission_list_request = data["userCMissionList"]
        
        user_mission_list = []

        for request in user_mission_list_request:
            user_id = int(request["userId"])
            mission_id = int(request["missionId"])
            point = int(request["point"])

            mission_data = await self.data.item.get_cmission(user_id, mission_id)
            progress_data = await self.data.item.get_cmission_progress(user_id, mission_id)

            if mission_data is None or progress_data is None:
                continue

            point = mission_data.point
            user_mission_progress_list = [
                {
                    "order": progress.order,
                    "stage": progress.stage,
                    "progress": progress.progress,
                }
                for progress in progress_data
            ]

            user_mission_list.append(
                {
                    "userId": user_id,
                    "missionId": mission_id,
                    "point": point,
                    "userCMissionProgressList": user_mission_progress_list,
                },
            )

        return {
            "userId": user_id,
            "userCMissionList": user_mission_list,
        }

