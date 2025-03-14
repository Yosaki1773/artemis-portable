from datetime import timedelta
from typing import Dict

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import (
    ChuniConstants,
    MapAreaConditionLogicalOperator,
    MapAreaConditionType,
)
from titles.chuni.sunplus import ChuniSunPlus


class ChuniLuminous(ChuniSunPlus):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_LUMINOUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # Does CARD MAKER 1.35 work this far up?
        user_data["lastDataVersion"] = "2.20.00"
        return user_data

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

    async def handle_get_game_map_area_condition_api_request(self, data: Dict) -> Dict:
        # There is no game data for this, everything is server side.
        # However, we can selectively show/hide events as data is imported into the server.
        events = await self.data.static.get_enabled_events(self.version)
        event_by_id = {evt["eventId"]: evt for evt in events}
        conditions = []

        # The Mystic Rainbow of LUMINOUS map unlocks when any mainline LUMINOUS area
        # (ep. I, ep. II, ep. III) are completed.
        mystic_area_1_conditions = {
            "mapAreaId": 3229301,  # Mystic Rainbow of LUMINOUS Area 1
            "length": 0,
            "mapAreaConditionList": [],
        }
        mystic_area_1_added = False

        # Secret AREA: MUSIC GAME
        if 14029 in event_by_id:
            start_date = event_by_id[14029]["startDate"].strftime(self.date_time_format)
            mission_in_progress_end_date = "2099-12-31 00:00:00.0"

            # The "MISSION in progress" trophy required to trigger the secret area
            # is only available in the first CHUNITHM mission. If the second mission
            # (event ID 14214) was imported into ARTEMiS, we disable the requirement
            # for this trophy.
            if 14214 in event_by_id:
                mission_in_progress_end_date = (
                    event_by_id[14214]["startDate"] - timedelta(hours=2)
                ).strftime(self.date_time_format)

            conditions.extend(
                [
                    {
                        "mapAreaId": 2206201,  # BlythE ULTIMA
                        "length": 1,
                        # Obtain the trophy "MISSION in progress".
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                                "conditionId": 6832,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": mission_in_progress_end_date,
                            }
                        ],
                    },
                    {
                        "mapAreaId": 2206202,  # PRIVATE SERVICE ULTIMA
                        "length": 1,
                        # Obtain the trophy "MISSION in progress".
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                                "conditionId": 6832,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": mission_in_progress_end_date,
                            }
                        ],
                    },
                    {
                        "mapAreaId": 2206203,  # New York Back Raise
                        "length": 1,
                        # SS NightTheater's EXPERT chart and get the title
                        # "今宵、劇場に映し出される景色とは――――。"
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                                "conditionId": 6833,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00.0",
                            },
                        ],
                    },
                    {
                        "mapAreaId": 2206204,  # Spasmodic
                        "length": 2,
                        # - Get 1 miss on Random (any difficulty) and get the title "当たり待ち"
                        # - Get 1 miss on 花たちに希望を (any difficulty) and get the title "花たちに希望を"
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                                "conditionId": 6834,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00.0",
                            },
                            {
                                "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                                "conditionId": 6835,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00.0",
                            },
                        ],
                    },
                    {
                        "mapAreaId": 2206205,  # ΩΩPARTS
                        "length": 2,
                        # - S Sage EXPERT to get the title "ﾏﾀｰﾘ進行ｷﾎﾞﾝﾇ"
                        # - Equip this title and play cab-to-cab with another person with this title
                        # to get "ﾏﾀｰﾘしようよ". Disabled because it is difficult to play cab2cab
                        # on data setups. A network operator may consider re-enabling it by uncommenting
                        # the second condition.
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                                "conditionId": 6836,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00.0",
                            },
                            # {
                            #     "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                            #     "conditionId": 6837,
                            #     "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            #     "startDate": start_date,
                            #     "endDate": "2099-12-31 00:00:00.0",
                            # },
                        ],
                    },
                    {
                        "mapAreaId": 2206206,  # Blow My Mind
                        "length": 1,
                        # SS on CHAOS EXPERT, Hydra EXPERT, Surive EXPERT and Jakarta PROGRESSION EXPERT
                        # to get the title "Can you hear me?"
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                                "conditionId": 6838,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00.0",
                            },
                        ],
                    },
                    {
                        "mapAreaId": 2206207,  # VALLIS-NERIA
                        "length": 6,
                        # Finish the 6 other areas
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.MAP_AREA_CLEARED.value,
                                "conditionId": x,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00.0",
                            }
                            for x in range(2206201, 2206207)
                        ],
                    },
                ]
            )

        # LUMINOUS ep. I
        if 14005 in event_by_id:
            start_date = event_by_id[14005]["startDate"].strftime(self.date_time_format)

            if not mystic_area_1_added:
                conditions.append(mystic_area_1_conditions)
                mystic_area_1_added = True

            mystic_area_1_conditions["length"] += 1
            mystic_area_1_conditions["mapAreaConditionList"].append(
                {
                    "type": MapAreaConditionType.MAP_CLEARED.value,
                    "conditionId": 3020701,
                    "logicalOpe": MapAreaConditionLogicalOperator.OR.value,
                    "startDate": start_date,
                    "endDate": "2099-12-31 00:00:00.0",
                }
            )

            conditions.append(
                {
                    "mapAreaId": 3229302,  # Mystic Rainbow of LUMINOUS Area 2,
                    "length": 1,
                    # Unlocks when LUMINOUS ep. I is completed.
                    "mapAreaConditionList": [
                        {
                            "type": MapAreaConditionType.MAP_CLEARED.value,
                            "conditionId": 3020701,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00.0",
                        },
                    ],
                }
            )

        # LUMINOUS ep. II
        if 14251 in event_by_id:
            start_date = event_by_id[14251]["startDate"].strftime(self.date_time_format)

            if not mystic_area_1_added:
                conditions.append(mystic_area_1_conditions)
                mystic_area_1_added = True

            mystic_area_1_conditions["length"] += 1
            mystic_area_1_conditions["mapAreaConditionList"].append(
                {
                    "type": MapAreaConditionType.MAP_CLEARED.value,
                    "conditionId": 3020702,
                    "logicalOpe": MapAreaConditionLogicalOperator.OR.value,
                    "startDate": start_date,
                    "endDate": "2099-12-31 00:00:00.0",
                }
            )

            conditions.append(
                {
                    "mapAreaId": 3229303,  # Mystic Rainbow of LUMINOUS Area 3,
                    "length": 1,
                    # Unlocks when LUMINOUS ep. II is completed.
                    "mapAreaConditionList": [
                        {
                            "type": MapAreaConditionType.MAP_CLEARED.value,
                            "conditionId": 3020702,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00.0",
                        },
                    ],
                }
            )

        # LUMINOUS ep. III
        if 14481 in event_by_id:
            start_date = event_by_id[14481]["startDate"].strftime(self.date_time_format)

            if not mystic_area_1_added:
                conditions.append(mystic_area_1_conditions)
                mystic_area_1_added = True

            mystic_area_1_conditions["length"] += 1
            mystic_area_1_conditions["mapAreaConditionList"].append(
                {
                    "type": MapAreaConditionType.MAP_CLEARED.value,
                    "conditionId": 3020703,
                    "logicalOpe": MapAreaConditionLogicalOperator.OR.value,
                    "startDate": start_date,
                    "endDate": "2099-12-31 00:00:00.0",
                }
            )

            conditions.append(
                {
                    "mapAreaId": 3229304,  # Mystic Rainbow of LUMINOUS Area 4,
                    "length": 1,
                    # Unlocks when LUMINOUS ep. III is completed.
                    "mapAreaConditionList": [
                        {
                            "type": MapAreaConditionType.MAP_CLEARED.value,
                            "conditionId": 3020703,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00.0",
                        },
                    ],
                }
            )

        # 1UM1N0U5 ep. 111
        if 14483 in event_by_id:
            start_date = event_by_id[14483]["startDate"].replace(
                hour=0, minute=0, second=0
            )

            # conditions to unlock the 6 "Key of ..." area in the map
            # for the first 14 days: Defandour MASTER AJ, crazy (about you) MASTER AJ, Halcyon ULTIMA SSS
            title_conditions = [
                {
                    "type": MapAreaConditionType.ALL_JUSTICE.value,
                    "conditionId": 258103,  # Defandour MASTER
                    "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                    "startDate": start_date.strftime(self.date_time_format),
                    "endDate": (
                        start_date + timedelta(days=14) - timedelta(seconds=1)
                    ).strftime(self.date_time_format),
                },
                {
                    "type": MapAreaConditionType.ALL_JUSTICE.value,
                    "conditionId": 258003,  # crazy (about you) MASTER
                    "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                    "startDate": start_date.strftime(self.date_time_format),
                    "endDate": (
                        start_date + timedelta(days=14) - timedelta(seconds=1)
                    ).strftime(self.date_time_format),
                },
                {
                    "type": MapAreaConditionType.RANK_SSS.value,
                    "conditionId": 17304,  # Halcyon ULTIMA
                    "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                    "startDate": start_date.strftime(self.date_time_format),
                    "endDate": (
                        start_date + timedelta(days=14) - timedelta(seconds=1)
                    ).strftime(self.date_time_format),
                },
            ]

            # For each next 14 days, the conditions are lowered to SS+, S+, S, and then always unlocked
            for i, typ in enumerate(
                [
                    MapAreaConditionType.RANK_SSP.value,
                    MapAreaConditionType.RANK_SP.value,
                    MapAreaConditionType.RANK_S.value,
                    MapAreaConditionType.ALWAYS_UNLOCKED.value,
                ]
            ):
                start = (start_date + timedelta(days=14 * (i + 1))).strftime(
                    self.date_time_format
                )

                if typ != MapAreaConditionType.ALWAYS_UNLOCKED.value:
                    end = (
                        start_date + timedelta(days=14 * (i + 2)) - timedelta(seconds=1)
                    ).strftime(self.date_time_format)

                    title_conditions.extend(
                        [
                            {
                                "type": typ,
                                "conditionId": condition_id,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start,
                                "endDate": end,
                            }
                            for condition_id in {17304, 258003, 258103}
                        ]
                    )
                else:
                    end = "2099-12-31 00:00:00"
                    
                    title_conditions.append(
                        {
                            "type": typ,
                            "conditionId": 0,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start,
                            "endDate": end,
                        }
                    )

            # actually add all the conditions
            for map_area_id in range(3229201, 3229207):
                conditions.append(
                    {
                        "mapAreaId": map_area_id,
                        "length": len(title_conditions),
                        "mapAreaConditionList": title_conditions,
                    }
                )

            # Ultimate Force
            # For the first 14 days, the condition is to obtain all 9 "Key of ..." titles
            # Afterwards, the condition is the 6 "Key of ..." titles that you can obtain
            # by playing the 6 areas, as well as obtaining specific ranks on 
            # [CRYSTAL_ACCESS] / Strange Love / βlαnoir
            ultimate_force_conditions = []

            # Trophies obtained by playing the 6 areas
            for trophy_id in {6851, 6853, 6855, 6857, 6858, 6860}:
                ultimate_force_conditions.append(
                    {
                        "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                        "conditionId": trophy_id,
                        "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                        "startDate": start_date.strftime(self.date_time_format),
                        "endDate": "2099-12-31 00:00:00",
                    }
                )

            # βlαnoir MASTER SSS+ / Strange Love MASTER SSS+ / [CRYSTAL_ACCESS] MASTER SSS+
            for trophy_id in {6852, 6854, 6856}:
                ultimate_force_conditions.append(
                    {
                        "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                        "conditionId": trophy_id,
                        "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                        "startDate": start_date.strftime(self.date_time_format),
                        "endDate": (
                            start_date + timedelta(days=14) - timedelta(seconds=1)
                        ).strftime(self.date_time_format),
                    }
                )

            # For each next 14 days, the rank conditions for the 3 songs lowers
            # Finally, the Ultimate Force area is unlocked as soon as you finish the 6 other areas.
            for i, typ in enumerate(
                [
                    MapAreaConditionType.RANK_SSS.value,
                    MapAreaConditionType.RANK_SS.value,
                    MapAreaConditionType.RANK_S.value,
                ]
            ):
                start = (start_date + timedelta(days=14 * (i + 1))).strftime(
                    self.date_time_format
                )
                
                end = (
                    start_date + timedelta(days=14 * (i + 2)) - timedelta(seconds=1)
                ).strftime(self.date_time_format)

                ultimate_force_conditions.extend(
                    [
                        {
                            "type": typ,
                            "conditionId": condition_id,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start,
                            "endDate": end,
                        }
                            for condition_id in {109403, 212103, 244203}
                    ]
                )

            conditions.append(
                {
                    "mapAreaId": 3229207,
                    "length": len(ultimate_force_conditions),
                    "mapAreaConditionList": ultimate_force_conditions,
                }
            )

        return {
            "length": len(conditions),
            "gameMapAreaConditionList": conditions,
        }
