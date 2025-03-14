import itertools
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytz

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import ChuniConstants, FavoriteItemKind, ItemKind
from titles.chuni.database import ChuniData


class ChuniBase:
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        self.core_cfg = core_cfg
        self.game_cfg = game_cfg
        self.data = ChuniData(core_cfg)
        self.date_time_format = "%Y-%m-%d %H:%M:%S"
        self.logger = logging.getLogger("chuni")
        self.game = ChuniConstants.GAME_CODE
        self.version = ChuniConstants.VER_CHUNITHM

    async def handle_game_login_api_request(self, data: Dict) -> Dict:
        """
        Handles the login bonus and ticket stock logic, required for the game
        because getUserLoginBonus gets called after getUserItem; therefore the
        items needs to be inserted in the database before they get requested.

        - Adds a stock for each specified ticket (itemKind 5)
        - Adds a bonusCount after a user logged in after 24 hours, makes sure
          loginBonus 30 gets looped, only show the login banner every 24 hours,
          adds the bonus to items (itemKind 6)
        """

        user_id = data["userId"]

        # If we want to make certain tickets always available, stock them now
        if self.game_cfg.mods.stock_tickets:
            for ticket in self.game_cfg.mods.stock_tickets.split(","):
                await self.data.item.put_item(
                    user_id,
                    {
                        "itemId": ticket.strip(),
                        "itemKind": ItemKind.TICKET.value,
                        "stock": self.game_cfg.mods.stock_count,
                        "isValid": True,
                    },
                )

        # ignore the login bonus if disabled in config
        if not self.game_cfg.mods.use_login_bonus:
            return {"returnCode": 1}

        login_bonus_presets = await self.data.static.get_login_bonus_presets(self.version)

        for preset in login_bonus_presets:
            # check if a user already has some pogress and if not add the
            # login bonus entry
            user_login_bonus = await self.data.item.get_login_bonus(
                user_id, self.version, preset["presetId"]
            )
            if user_login_bonus is None:
                await self.data.item.put_login_bonus(
                    user_id, self.version, preset["presetId"]
                )
                # yeah i'm lazy
                user_login_bonus = await self.data.item.get_login_bonus(
                    user_id, self.version, preset["presetId"]
                )

            # skip the login bonus entirely if its already finished
            if user_login_bonus["isFinished"]:
                continue

            # make sure the last login is more than 24 hours ago
            if user_login_bonus["lastUpdateDate"] < datetime.now() - timedelta(
                hours=24
            ):
                # increase the login day counter and update the last login date
                bonus_count = user_login_bonus["bonusCount"] + 1
                last_update_date = datetime.now()

                all_login_boni = await self.data.static.get_login_bonus(
                    self.version, preset["presetId"]
                )

                # skip the current bonus preset if no boni were found
                if all_login_boni is None or len(all_login_boni) < 1:
                    self.logger.warning(
                        f"No bonus entries found for bonus preset {preset['presetId']}"
                    )
                    continue

                max_needed_days = all_login_boni[0]["needLoginDayCount"]

                # make sure to not show login boni after all days got redeemed
                is_finished = False
                if bonus_count > max_needed_days:
                    # assume that all login preset ids under 3000 needs to be
                    # looped, like 30 and 40 are looped, 40 does not work?
                    if preset["presetId"] < 3000:
                        bonus_count = 1
                    else:
                        is_finished = True

                # grab the item for the corresponding day
                login_item = await self.data.static.get_login_bonus_by_required_days(
                    self.version, preset["presetId"], bonus_count
                )
                if login_item is not None:
                    # now add the present to the database so the
                    # handle_get_user_item_api_request can grab them
                    await self.data.item.put_item(
                        user_id,
                        {
                            "itemId": login_item["presentId"],
                            "itemKind": ItemKind.PRESENT.value,
                            "stock": login_item["itemNum"],
                            "isValid": True,
                        },
                    )

                await self.data.item.put_login_bonus(
                    user_id,
                    self.version,
                    preset["presetId"],
                    bonusCount=bonus_count,
                    lastUpdateDate=last_update_date,
                    isWatched=False,
                    isFinished=is_finished,
                )

        return {"returnCode": 1}

    async def handle_game_logout_api_request(self, data: Dict) -> Dict:
        # self.data.base.log_event("chuni", "logout", logging.INFO, {"version": self.version, "user": data["userId"]})
        return {"returnCode": 1}

    async def handle_get_game_charge_api_request(self, data: Dict) -> Dict:
        game_charge_list = await self.data.static.get_enabled_charges(self.version)

        if game_charge_list is None or len(game_charge_list) == 0:
            return {"length": 0, "gameChargeList": []}

        charges = []
        for x in range(len(game_charge_list)):
            charges.append(
                {
                    "orderId": x,
                    "chargeId": game_charge_list[x]["chargeId"],
                    "price": 1,
                    "startDate": "2017-12-05 07:00:00.0",
                    "endDate": "2099-12-31 00:00:00.0",
                    "salePrice": 1,
                    "saleStartDate": "2017-12-05 07:00:00.0",
                    "saleEndDate": "2099-12-31 00:00:00.0",
                }
            )
        return {"length": len(charges), "gameChargeList": charges}

    async def handle_get_game_event_api_request(self, data: Dict) -> Dict:
        game_events = await self.data.static.get_enabled_events(self.version)

        if game_events is None or len(game_events) == 0:
            self.logger.warning("No enabled events, did you run the reader?")
            return {
                "type": data["type"],
                "length": 0,
                "gameEventList": [],
            }

        event_list = []
        for evt_row in game_events:
            event_list.append(
                {
                    "id": evt_row["eventId"],
                    "type": evt_row["type"],
                    # actually use the startDate from the import so it
                    # properly shows all the events when new ones are imported
                    "startDate": datetime.strftime(
                        evt_row["startDate"], "%Y-%m-%d %H:%M:%S"
                    ),
                    "endDate": "2099-12-31 00:00:00",
                }
            )

        return {
            "type": data["type"],
            "length": len(event_list),
            "gameEventList": event_list,
        }

    async def handle_get_game_idlist_api_request(self, data: Dict) -> Dict:
        return {"type": data["type"], "length": 0, "gameIdlistList": []}

    async def handle_get_game_message_api_request(self, data: Dict) -> Dict:
        return {
            "type": data["type"], 
            "length": 1, 
            "gameMessageList": [{ 
                "id": 1, 
                "type": 1,
                "message": f"Welcome to {self.core_cfg.server.name} network!" if not self.game_cfg.server.news_msg else self.game_cfg.server.news_msg,
                "startDate": "2017-12-05 07:00:00.0",
                "endDate": "2099-12-31 00:00:00.0"
            }]
        }

    async def handle_get_game_ranking_api_request(self, data: Dict) -> Dict:
        rankings = await self.data.score.get_rankings(self.version)
        return {"type": data["type"], "gameRankingList": rankings}

    async def handle_get_game_sale_api_request(self, data: Dict) -> Dict:
        return {"type": data["type"], "length": 0, "gameSaleList": []}

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        # if reboot start/end time is not defined use the default behavior of being a few hours ago
        if self.core_cfg.title.reboot_start_time == "" or self.core_cfg.title.reboot_end_time == "":
            reboot_start = datetime.strftime(
                datetime.utcnow() + timedelta(hours=6), self.date_time_format
            )
            reboot_end = datetime.strftime(
                datetime.utcnow() + timedelta(hours=7), self.date_time_format
            )
        else:
            # get current datetime in JST
            current_jst = datetime.now(pytz.timezone('Asia/Tokyo')).date()

            # parse config start/end times into datetime
            reboot_start_time = datetime.strptime(self.core_cfg.title.reboot_start_time, "%H:%M")
            reboot_end_time = datetime.strptime(self.core_cfg.title.reboot_end_time, "%H:%M")

            # offset datetimes with current date/time
            reboot_start_time = reboot_start_time.replace(year=current_jst.year, month=current_jst.month, day=current_jst.day, tzinfo=pytz.timezone('Asia/Tokyo'))
            reboot_end_time = reboot_end_time.replace(year=current_jst.year, month=current_jst.month, day=current_jst.day, tzinfo=pytz.timezone('Asia/Tokyo'))

            # create strings for use in gameSetting
            reboot_start = reboot_start_time.strftime(self.date_time_format)
            reboot_end = reboot_end_time.strftime(self.date_time_format)

        return {
            "gameSetting": {
                "dataVersion": "1.00.00",
                "isMaintenance": "false",
                "requestInterval": 10,
                "rebootStartTime": reboot_start,
                "rebootEndTime": reboot_end,
                "isBackgroundDistribute": "false",
                "maxCountCharacter": 300,
                "maxCountItem": 300,
                "maxCountMusic": 300,
            },
            "isDumpUpload": "false",
            "isAou": "false",
        }
    async def handle_get_user_activity_api_request(self, data: Dict) -> Dict:
        user_activity_list = await self.data.profile.get_profile_activity(
            data["userId"], data["kind"]
        )

        activity_list = []

        for activity in user_activity_list:
            tmp = activity._asdict()
            tmp.pop("user")
            tmp["id"] = tmp["activityId"]
            tmp.pop("activityId")
            activity_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(activity_list),
            "kind": int(data["kind"]),
            "userActivityList": activity_list,
        }

    async def handle_get_user_character_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        next_idx = int(data["nextIndex"])
        max_ct = int(data["maxCount"])

        # add one to the limit so we know if there's a next page of items
        rows = await self.data.item.get_characters(
            user_id, limit=max_ct + 1, offset=next_idx
        )
        
        if rows is None or len(rows) == 0:
            return {
                "userId": user_id,
                "length": 0,
                "nextIndex": -1,
                "userCharacterList": [],
            }

        character_list = []

        for row in rows[:max_ct]:
            tmp = row._asdict()
            tmp.pop("id")
            tmp.pop("user")

            character_list.append(tmp)

        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = -1

        return {
            "userId": user_id,
            "length": len(character_list),
            "nextIndex": next_idx,
            "userCharacterList": character_list,
        }

    async def handle_get_user_charge_api_request(self, data: Dict) -> Dict:
        user_charge_list = await self.data.profile.get_profile_charge(data["userId"])

        charge_list = []
        for charge in user_charge_list:
            tmp = charge._asdict()
            tmp.pop("id")
            tmp.pop("user")
            charge_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(charge_list),
            "userChargeList": charge_list,
        }

    async def handle_get_user_recent_player_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "length": 0,
            "userRecentPlayerList": [], # playUserId, playUserName, playDate, friendPoint
        }

    async def handle_get_user_course_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        next_idx = int(data["nextIndex"])
        max_ct = int(data["maxCount"])

        rows = await self.data.score.get_courses(
            user_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None or len(rows) == 0:
            return {
                "userId": user_id,
                "length": 0,
                "nextIndex": -1,
                "userCourseList": [],
            }

        course_list = []

        for row in rows[:max_ct]:
            tmp = row._asdict()
            tmp.pop("user")
            tmp.pop("id")
            course_list.append(tmp)

        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = -1

        return {
            "userId": data["userId"],
            "length": len(course_list),
            "nextIndex": next_idx,
            "userCourseList": course_list,
        }

    async def handle_get_user_data_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_data(data["userId"], self.version)
        if p is None:
            return {}

        profile = p._asdict()
        profile.pop("id")
        profile.pop("user")
        profile.pop("version")

        return {"userId": data["userId"], "userData": profile}

    async def handle_get_user_data_ex_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_data_ex(data["userId"], self.version)
        if p is None:
            return {}

        profile = p._asdict()
        profile.pop("id")
        profile.pop("user")
        profile.pop("version")

        return {"userId": data["userId"], "userDataEx": profile}

    async def handle_get_user_duel_api_request(self, data: Dict) -> Dict:
        user_duel_list = await self.data.item.get_duels(data["userId"])
        if user_duel_list is None:
            return {}

        duel_list = []
        for duel in user_duel_list:
            tmp = duel._asdict()
            tmp.pop("id")
            tmp.pop("user")
            duel_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(duel_list),
            "userDuelList": duel_list,
        }

    async def handle_get_user_rival_data_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_rival(data["rivalId"])
        if p is None:
            return {}
        userRivalData = {
            "rivalId": p.user,
            "rivalName": p.userName
        }
        return {
            "userId": data["userId"],
            "userRivalData": userRivalData
        }
    
    async def handle_get_user_rival_music_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        rival_id = int(data["rivalId"])
        next_idx = int(data["nextIndex"])
        max_ct = int(data["maxCount"])
        rival_levels = [int(x["level"]) for x in data["userRivalMusicLevelList"]]

        # Fetch all the rival music entries for the user
        rows = await self.data.score.get_scores(
            rival_id,
            levels=rival_levels,
            limit=max_ct + 1,
            offset=next_idx,
        )

        if rows is None or len(rows) == 0:
            return {
                "userId": user_id,
                "rivalId": rival_id,
                "nextIndex": -1,
                "userRivalMusicList": [],
            }

        music_details = [x._asdict() for x in rows]
        returned_music_details_count = 0
        music_list = []

        # note that itertools.groupby will only work on sorted keys, which is already sorted by
        # the query in get_scores
        for music_id, details_iter in itertools.groupby(music_details, key=lambda x: x["musicId"]):
            details: list[dict[Any, Any]] = [
                {"level": d["level"], "scoreMax": d["scoreMax"]}
                for d in details_iter
            ]

            music_list.append({"musicId": music_id, "length": len(details), "userRivalMusicDetailList": details})
            returned_music_details_count += len(details)

            if len(music_list) >= max_ct:
                break
        
        # if we returned fewer PBs than we originally asked for from the database, that means
        # we queried for the PBs of max_ct + 1 songs.
        if returned_music_details_count < len(rows):
            next_idx += max_ct
        else:
            next_idx = -1

        return {
            "userId": user_id,
            "rivalId": rival_id,
            "length": len(music_list),
            "nextIndex": next_idx,
            "userRivalMusicList": music_list,
        }
    
    async def handle_get_user_favorite_item_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        next_idx = int(data["nextIndex"])
        max_ct = int(data["maxCount"])
        kind = int(data["kind"])
        is_all_favorite_item = str(data["isAllFavoriteItem"]) == "true"

        user_fav_item_list = []

        # still needs to be implemented on WebUI
        # 1: Music, 2: User, 3: Character
        rows = await self.data.item.get_all_favorites(
            user_id,
            self.version,
            fav_kind=kind,
            limit=max_ct + 1,
            offset=next_idx,
        )

        if rows is not None:
            for fav in rows[:max_ct]:
                user_fav_item_list.append({"id": fav["favId"]})

        if rows is None or len(rows) <= max_ct:
            next_idx = -1
        else:
            next_idx += max_ct

        return {
            "userId": user_id,
            "length": len(user_fav_item_list),
            "kind": kind,
            "nextIndex": next_idx,
            "userFavoriteItemList": user_fav_item_list,
        }

    async def handle_get_user_favorite_music_api_request(self, data: Dict) -> Dict:
        """
        This is handled via the webui, which we don't have right now
        """

        return {"userId": data["userId"], "length": 0, "userFavoriteMusicList": []}

    async def handle_get_user_item_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        next_idx = int(data["nextIndex"])
        max_ct = int(data["maxCount"])

        kind = next_idx // 10000000000
        next_idx = next_idx % 10000000000
        rows = await self.data.item.get_items(
            user_id, kind, limit=max_ct + 1, offset=next_idx
        )

        if rows is None or len(rows) == 0:
            return {
                "userId": user_id,
                "nextIndex": -1,
                "itemKind": kind,
                "userItemList": [],
            }

        items: List[Dict[str, Any]] = []

        for row in rows[:max_ct]:
            tmp = row._asdict()
            tmp.pop("user")
            tmp.pop("id")
            items.append(tmp)

        if len(rows) > max_ct:
            next_idx = kind * 10000000000 + next_idx + max_ct
        else:
            next_idx = -1

        return {
            "userId": user_id,
            "nextIndex": next_idx,
            "itemKind": kind,
            "length": len(items),
            "userItemList": items,
        }

    async def handle_get_user_login_bonus_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        user_login_bonus = await self.data.item.get_all_login_bonus(user_id, self.version)
        # ignore the loginBonus request if its disabled in config
        if user_login_bonus is None or not self.game_cfg.mods.use_login_bonus:
            return {"userId": user_id, "length": 0, "userLoginBonusList": []}

        user_login_list = []
        for bonus in user_login_bonus:
            user_login_list.append(
                {
                    "presetId": bonus["presetId"],
                    "bonusCount": bonus["bonusCount"],
                    "lastUpdateDate": datetime.strftime(
                        bonus["lastUpdateDate"], "%Y-%m-%d %H:%M:%S"
                    ),
                    "isWatched": bonus["isWatched"],
                }
            )

        return {
            "userId": user_id,
            "length": len(user_login_list),
            "userLoginBonusList": user_login_list,
        }

    async def handle_get_user_map_api_request(self, data: Dict) -> Dict:
        user_map_list = await self.data.item.get_maps(data["userId"])
        if user_map_list is None:
            return {}

        map_list = []
        for map in user_map_list:
            tmp = map._asdict()
            tmp.pop("id")
            tmp.pop("user")
            map_list.append(tmp)

        return {
            "userId": data["userId"],
            "length": len(map_list),
            "userMapList": map_list,
        }

    async def handle_get_user_music_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        next_idx = int(data["nextIndex"])
        max_ct = int(data["maxCount"])

        rows = await self.data.score.get_scores(
            user_id, limit=max_ct + 1, offset=next_idx
        )
        
        if rows is None or len(rows) == 0:
            return {
                "userId": user_id,
                "length": 0,
                "nextIndex": -1,
                "userMusicList": [],  # 240
            }

        music_details = [x._asdict() for x in rows]
        returned_music_details_count = 0
        music_list = []

        # note that itertools.groupby will only work on sorted keys, which is already sorted by
        # the query in get_scores
        for _music_id, details_iter in itertools.groupby(music_details, key=lambda x: x["musicId"]):
            details: list[dict[Any, Any]] = []

            for d in details_iter:
                d.pop("id")
                d.pop("user")

                details.append(d)

            music_list.append({"length": len(details), "userMusicDetailList": details})
            returned_music_details_count += len(details)

            if len(music_list) >= max_ct:
                break
        
        # if we returned fewer PBs than we originally asked for from the database, that means
        # we queried for the PBs of max_ct + 1 songs.
        if returned_music_details_count < len(rows):
            next_idx += max_ct
        else:
            next_idx = -1
        
        return {
            "userId": user_id,
            "length": len(music_list),
            "nextIndex": next_idx,
            "userMusicList": music_list,
        }

    async def handle_get_user_option_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_option(data["userId"])

        option = p._asdict()
        option.pop("id")
        option.pop("user")

        return {"userId": data["userId"], "userGameOption": option}

    async def handle_get_user_option_ex_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_option_ex(data["userId"])

        option = p._asdict()
        option.pop("id")
        option.pop("user")

        return {"userId": data["userId"], "userGameOptionEx": option}

    def read_wtf8(self, src):
        return bytes([ord(c) for c in src]).decode("utf-8")

    async def handle_get_user_preview_api_request(self, data: Dict) -> Dict:
        profile = await self.data.profile.get_profile_preview(data["userId"], self.version)
        if profile is None:
            return None
        profile_character = await self.data.item.get_character(
            data["userId"], profile["characterId"]
        )

        if profile_character is None:
            chara = {}
        else:
            chara = profile_character._asdict()
            chara.pop("id")
            chara.pop("user")

        return {
            "userId": data["userId"],
            # Current Login State
            "isLogin": False,
            "lastLoginDate": profile["lastPlayDate"],
            # User Profile
            "userName": profile["userName"],
            "reincarnationNum": profile["reincarnationNum"],
            "level": profile["level"],
            "exp": profile["exp"],
            "playerRating": profile["playerRating"],
            "lastGameId": profile["lastGameId"],
            "lastRomVersion": profile["lastRomVersion"],
            "lastDataVersion": profile["lastDataVersion"],
            "lastPlayDate": profile["lastPlayDate"],
            "trophyId": profile["trophyId"],
            "nameplateId": profile["nameplateId"],
            # Current Selected Character
            "userCharacter": chara,
            # User Game Options
            "playerLevel": profile["playerLevel"],
            "rating": profile["rating"],
            "headphone": profile["headphone"],
            "chargeState": 1,
            "userNameEx": profile["userName"],
        }

    async def handle_get_user_recent_rating_api_request(self, data: Dict) -> Dict:
        recent_rating_list = await self.data.profile.get_profile_recent_rating(data["userId"])
        if recent_rating_list is None:
            return {
                "userId": data["userId"],
                "length": 0,
                "userRecentRatingList": [],
            }

        return {
            "userId": data["userId"],
            "length": len(recent_rating_list["recentRating"]),
            "userRecentRatingList": recent_rating_list["recentRating"],
        }

    async def handle_get_user_region_api_request(self, data: Dict) -> Dict:
        # TODO: Region
        return {
            "userId": data["userId"],
            "length": 0,
            "userRegionList": [],
        }

    async def handle_get_user_team_api_request(self, data: Dict) -> Dict:
        # Default values
        team_id = 65535
        team_name = self.game_cfg.team.team_name
        team_rank = 0
        team_user_point = 0

        # Get user profile
        profile = await self.data.profile.get_profile_data(data["userId"], self.version)

        if profile is None:
          return {"userId": data["userId"], "teamId": 0}

        if profile and profile["teamId"]:
            # Get team by id
            team = await self.data.profile.get_team_by_id(profile["teamId"])

            if team:
                team_id = team["id"]
                team_name = team["teamName"]
                team_rank = await self.data.profile.get_team_rank(team["id"])
                team_point = team["teamPoint"]
                if team["userTeamPoint"] is not None and team["userTeamPoint"] != "":
                    user_team_point_data = json.loads(team["userTeamPoint"])
                    for user_point_data in user_team_point_data:
                        if user_point_data["user"] == data["userId"]:
                            team_user_point = int(user_point_data["userPoint"])
        # Don't return anything if no team name has been defined for defaults and there is no team set for the player
        if not profile["teamId"] and team_name == "":
            return {"userId": data["userId"], "teamId": 0}

        return {
            "userId": data["userId"],
            "teamId": team_id,
            "teamRank": team_rank,
            "teamName": team_name,
            "assaultTimeRate": 1, # TODO: Figure out assaultTime, which might be team point boost?
            "userTeamPoint": {
                "userId": data["userId"],
                "teamId": team_id,
                "orderId": 0,
                "teamPoint": team_user_point,
                "aggrDate": data["playDate"],
            },
        }
    
    async def handle_get_team_course_setting_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "length": 0,
            "nextIndex": -1,
            "teamCourseSettingList": [],
        }

    async def handle_get_team_course_setting_api_request_proto(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "length": 1,
            "nextIndex": -1,
            "teamCourseSettingList": [
                {
                    "orderId": 1,
                    "courseId": 1,
                    "classId": 1,
                    "ruleId": 1,
                    "courseName": "Test",
                    "teamCourseMusicList": [
                        {"track": 184, "type": 1, "level": 3, "selectLevel": -1},
                        {"track": 184, "type": 1, "level": 3, "selectLevel": -1},
                        {"track": 184, "type": 1, "level": 3, "selectLevel": -1}
                    ],
                    "teamCourseRankingInfoList": [],
                    "recodeDate": "2099-12-31 11:59:99.0",
                    "isPlayed": False
                }
            ],
        }

    async def handle_get_team_course_rule_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "length": 0,
            "nextIndex": -1,
            "teamCourseRuleList": []
        }

    async def handle_get_team_course_rule_api_request_proto(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "length": 1,
            "nextIndex": -1,
            "teamCourseRuleList": [
                {
                    "recoveryLife": 0,
                    "clearLife": 100,
                    "damageMiss": 1,
                    "damageAttack": 1,
                    "damageJustice": 1,
                    "damageJusticeC": 1
                }
            ],
        }

    async def handle_upsert_user_all_api_request(self, data: Dict) -> Dict:
        upsert = data["upsertUserAll"]
        user_id = data["userId"]

        if int(user_id) & 0x1000000000001 == 0x1000000000001:
            place_id = int(user_id) & 0xFFFC00000000
            
            self.logger.info("Guest play from place ID %d, ignoring.", place_id)
            return {"returnCode": "1"}

        if "userData" in upsert:
            try:
                upsert["userData"][0]["userName"] = self.read_wtf8(
                    upsert["userData"][0]["userName"]
                )
            except Exception:
                pass

            await self.data.profile.put_profile_data(
                user_id, self.version, upsert["userData"][0]
            )

        if "userDataEx" in upsert:
            await self.data.profile.put_profile_data_ex(
                user_id, self.version, upsert["userDataEx"][0]
            )

        if "userGameOption" in upsert:
            await self.data.profile.put_profile_option(user_id, upsert["userGameOption"][0])

        if "userGameOptionEx" in upsert:
            await self.data.profile.put_profile_option_ex(
                user_id, upsert["userGameOptionEx"][0]
            )
        if "userRecentRatingList" in upsert:
            await self.data.profile.put_profile_recent_rating(
                user_id, upsert["userRecentRatingList"]
            )

        if "userCharacterList" in upsert:
            for character in upsert["userCharacterList"]:
                await self.data.item.put_character(user_id, character)

        if "userMapList" in upsert:
            for map in upsert["userMapList"]:
                await self.data.item.put_map(user_id, map)

        if "userCourseList" in upsert:
            for course in upsert["userCourseList"]:
                await self.data.score.put_course(user_id, course)

        if "userDuelList" in upsert:
            for duel in upsert["userDuelList"]:
                await self.data.item.put_duel(user_id, duel)

        if "userItemList" in upsert:
            for item in upsert["userItemList"]:
                await self.data.item.put_item(user_id, item)

        if "userActivityList" in upsert:
            for activity in upsert["userActivityList"]:
                await self.data.profile.put_profile_activity(user_id, activity)

        if "userChargeList" in upsert:
            for charge in upsert["userChargeList"]:
                await self.data.profile.put_profile_charge(user_id, charge)

        if "userMusicDetailList" in upsert:
            for song in upsert["userMusicDetailList"]:
                await self.data.score.put_score(user_id, song)

        if "userPlaylogList" in upsert:
            for playlog in upsert["userPlaylogList"]:
                # convert the player names to utf-8
                if playlog["playedUserName1"] is not None:
                  playlog["playedUserName1"] = self.read_wtf8(playlog["playedUserName1"])
                if playlog["playedUserName2"] is not None:
                  playlog["playedUserName2"] = self.read_wtf8(playlog["playedUserName2"])
                if playlog["playedUserName3"] is not None:
                  playlog["playedUserName3"] = self.read_wtf8(playlog["playedUserName3"])
                await self.data.score.put_playlog(user_id, playlog, self.version)

        if "userTeamPoint" in upsert:
            team_points = upsert["userTeamPoint"]
            try:
                for tp in team_points:
                    if tp["teamId"] != '65535':
                        # Fetch the current team data
                        current_team = await self.data.profile.get_team_by_id(tp["teamId"])

                        # Calculate the new teamPoint
                        new_team_point = int(tp["teamPoint"]) + current_team["teamPoint"]

                        # Prepare the data to update
                        team_data = {
                            "teamPoint": new_team_point
                        }

                        # Update the team data
                        await self.data.profile.update_team(tp["teamId"], team_data)
            except:
                pass # Probably a better way to catch if the team is not set yet (new profiles), but let's just pass
        if "userMapAreaList" in upsert:
            for map_area in upsert["userMapAreaList"]:
                await self.data.item.put_map_area(user_id, map_area)

        if "userOverPowerList" in upsert:
            for overpower in upsert["userOverPowerList"]:
                await self.data.profile.put_profile_overpower(user_id, overpower)

        if "userEmoneyList" in upsert:
            for emoney in upsert["userEmoneyList"]:
                await self.data.profile.put_profile_emoney(user_id, emoney)

        if "userLoginBonusList" in upsert:
            for login in upsert["userLoginBonusList"]:
                await self.data.item.put_login_bonus(
                    user_id, self.version, login["presetId"], isWatched=True
                )
        
        if "userRecentPlayerList" in upsert: # TODO: Seen in Air, maybe implement sometime
            for rp in upsert["userRecentPlayerList"]:
                pass

        for rating_type in {"userRatingBaseList", "userRatingBaseHotList", "userRatingBaseNextList"}:
            if rating_type not in upsert:
                continue
            
            await self.data.profile.put_profile_rating(
                user_id,
                self.version,
                rating_type,
                upsert[rating_type],
            )
        
        # added in LUMINOUS
        if "userCMissionList" in upsert:
            for cmission in upsert["userCMissionList"]:
                mission_id = cmission["missionId"]

                await self.data.item.put_cmission(
                    user_id,
                    {
                        "missionId": mission_id,
                        "point": cmission["point"],
                    },
                )

                for progress in cmission["userCMissionProgressList"]:
                    await self.data.item.put_cmission_progress(user_id, mission_id, progress)

        if "userNetBattleData" in upsert:
            net_battle = upsert["userNetBattleData"][0]

            # fix the boolean
            net_battle["isRankUpChallengeFailed"] = (
                False if net_battle["isRankUpChallengeFailed"] == "false" else True
            )
            await self.data.profile.put_net_battle(user_id, net_battle)

        # New in LUMINOUS PLUS
        if "userFavoriteMusicList" in upsert:
            # musicId, orderId
            music_ids = set(
                int(m["musicId"])
                for m in upsert["userFavoriteMusicList"]
                if m["musicId"] != "-1"
            )
            current_favorites = await self.data.item.get_all_favorites(
                user_id, self.version, fav_kind=FavoriteItemKind.MUSIC.value
            )

            if current_favorites is None:
                current_favorites = []

            current_favorite_ids = set(x.favId for x in current_favorites)
            keep_ids = current_favorite_ids.intersection(music_ids)
            deleted_ids = current_favorite_ids - keep_ids
            added_ids = music_ids - keep_ids

            for fav_id in deleted_ids:
                await self.data.item.delete_favorite_music(user_id, self.version, fav_id)
            
            for fav_id in added_ids:
                await self.data.item.put_favorite_music(user_id, self.version, fav_id)

        return {"returnCode": "1"}

    async def handle_upsert_user_chargelog_api_request(self, data: Dict) -> Dict:
        # add tickets after they got bought, this makes sure the tickets are
        # still valid after an unsuccessful logout
        await self.data.profile.put_profile_charge(data["userId"], data["userCharge"])
        return {"returnCode": "1"}

    async def handle_upsert_client_bookkeeping_api_request(self, data: Dict) -> Dict:
        return {"returnCode": "1"}

    async def handle_upsert_client_develop_api_request(self, data: Dict) -> Dict:
        return {"returnCode": "1"}

    async def handle_upsert_client_error_api_request(self, data: Dict) -> Dict:
        return {"returnCode": "1"}

    async def handle_upsert_client_setting_api_request(self, data: Dict) -> Dict:
        return {"returnCode": "1"}

    async def handle_upsert_client_testmode_api_request(self, data: Dict) -> Dict:
        return {"returnCode": "1"}

    async def handle_get_user_net_battle_data_api_request(self, data: Dict) -> Dict:
        return {
            "userId": data["userId"],
            "userNetBattleData": {"recentNBSelectMusicList": []},
        }
