from datetime import timedelta
from typing import Dict

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import ChuniConstants, MapAreaConditionLogicalOperator, MapAreaConditionType
from titles.chuni.luminous import ChuniLuminous


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

    async def handle_get_game_map_area_condition_api_request(self, data: Dict) -> Dict:
        # There is no game data for this, everything is server side.
        # However, we can selectively show/hide events as data is imported into the server.
        events = await self.data.static.get_enabled_events(self.version)
        event_by_id = {evt["eventId"]: evt for evt in events}
        conditions = []

        # LUMINOUS ep. Ascension
        if ep_ascension := event_by_id.get(15512):
            start_date = ep_ascension["startDate"].replace(hour=0, minute=0, second=0)

            # Finish LUMINOUS ep. VII to unlock LUMINOUS ep. Ascension.
            task_track_map_conditions = [
                {
                    "type": MapAreaConditionType.MAP_CLEARED.value,
                    "conditionId": 3020707,
                    "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                    "startDate": start_date.strftime(self.date_time_format),
                    "endDate": "2099-12-31 00:00:00",
                }
            ]

            # You also need to reach a specific rank on Acid God MASTER.
            # This condition lowers every 7 days.
            # After the first 4 weeks, you only need to finish ep. VII.
            for i, typ in enumerate([
                MapAreaConditionType.RANK_SSSP.value,
                MapAreaConditionType.RANK_SSS.value,
                MapAreaConditionType.RANK_SS.value,
                MapAreaConditionType.RANK_S.value,
            ]):
                start = start_date + timedelta(days=7 * i)
                end = start_date + timedelta(days=7 * (i + 1)) - timedelta(seconds=1)

                task_track_map_conditions.append(
                    {
                        "type": typ,
                        "conditionId": 265103,
                        "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                        "startDate": start.strftime(self.date_time_format),
                        "endDate": end.strftime(self.date_time_format),
                    }
                )

            conditions.extend(
                [
                    {
                        "mapAreaId": map_area_id,
                        "length": len(task_track_map_conditions),
                        "mapAreaConditionList": task_track_map_conditions,
                    }
                    for map_area_id in {3220801, 3220802, 3220803, 3220804}
                ]
            )

            # To unlock the final map area (Forsaken Tale), achieve a specific rank
            # on the 4 task tracks in the previous map areas. This condition also lowers
            # every 7 days, similar to Acid God.
            # After 28 days, you only need to finish the other 4 areas in ep. Ascension.
            forsaken_tale_conditions = []

            for i, typ in enumerate([
                MapAreaConditionType.RANK_SSSP.value,
                MapAreaConditionType.RANK_SSS.value,
                MapAreaConditionType.RANK_SS.value,
                MapAreaConditionType.RANK_S.value,
            ]):
                start = start_date + timedelta(days=7 * i)
                end = start_date + timedelta(days=7 * (i + 1)) - timedelta(seconds=1)

                forsaken_tale_conditions.extend(
                    [
                        {
                            "type": typ,
                            "conditionId": condition_id,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start.strftime(self.date_time_format),
                            "endDate": end.strftime(self.date_time_format),
                        }
                        for condition_id in {98203, 108603, 247503, 233903}
                    ]
                )

            forsaken_tale_conditions.extend(
                [
                    {
                        "type": MapAreaConditionType.MAP_AREA_CLEARED.value,
                        "conditionId": map_area_id,
                        "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                        "startDate": (start_date + timedelta(days=28)).strftime(self.date_time_format),
                        "endDate": "2099-12-31 00:00:00",
                    }
                    for map_area_id in {3220801, 3220802, 3220803, 3220804}
                ]
            )

            conditions.append(
                {
                    "mapAreaId": 3220805,
                    "length": len(forsaken_tale_conditions),
                    "mapAreaConditionList": forsaken_tale_conditions,
                }
            )

        return {
            "length": len(conditions),
            "gameMapAreaConditionList": conditions,
        }
