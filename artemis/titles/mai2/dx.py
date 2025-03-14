import itertools
from datetime import datetime, timedelta
from random import randint
from typing import Any, Dict, List

import pytz

from core.config import CoreConfig
from core.utils import Utils
from titles.mai2.base import Mai2Base
from titles.mai2.config import Mai2Config
from titles.mai2.const import Mai2Constants


class Mai2DX(Mai2Base):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX

        # DX earlier version need a efficient old server uri to work
        # game will auto add MaimaiServlet endpoint behind return uri
        # so do not add "MaimaiServlet"
        if not self.core_config.server.is_using_proxy and Utils.get_title_port(self.core_config) != 80:
            self.old_server = f"http://{self.core_config.server.hostname}:{Utils.get_title_port(cfg)}/SDEY/197/"

        else:
            self.old_server = f"http://{self.core_config.server.hostname}/SDEY/197/"

    async def handle_get_game_setting_api_request(self, data: Dict):
        # if reboot start/end time is not defined use the default behavior of being a few hours ago
        if self.core_config.title.reboot_start_time == "" or self.core_config.title.reboot_end_time == "":
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
            reboot_start_time = datetime.strptime(self.core_config.title.reboot_start_time, "%H:%M")
            reboot_end_time = datetime.strptime(self.core_config.title.reboot_end_time, "%H:%M")

            # offset datetimes with current date/time
            reboot_start_time = reboot_start_time.replace(year=current_jst.year, month=current_jst.month, day=current_jst.day, tzinfo=pytz.timezone('Asia/Tokyo'))
            reboot_end_time = reboot_end_time.replace(year=current_jst.year, month=current_jst.month, day=current_jst.day, tzinfo=pytz.timezone('Asia/Tokyo'))

            # create strings for use in gameSetting
            reboot_start = reboot_start_time.strftime(self.date_time_format)
            reboot_end = reboot_end_time.strftime(self.date_time_format)

        return {
            "gameSetting": {
                "isMaintenance": False,
                "requestInterval": 1800,
                "rebootStartTime": reboot_start,
                "rebootEndTime": reboot_end,
                "movieUploadLimit": 100,
                "movieStatus": 1,
                "movieServerUri": "",
                "deliverServerUri": "",
                "oldServerUri": self.old_server,
                "usbDlServerUri": "",
                "rebootInterval": 0,
            },
            "isAouAccession": False,
        }

    async def handle_get_user_preview_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_detail(data["userId"], self.version)
        o = await self.data.profile.get_profile_option(data["userId"], self.version)
        if p is None or o is None:
            return {}  # Register
        profile = p._asdict()
        option = o._asdict()

        return {
            "userId": data["userId"],
            "userName": profile["userName"],
            "isLogin": False,
            "lastGameId": profile["lastGameId"],
            "lastDataVersion": profile["lastDataVersion"],
            "lastRomVersion": profile["lastRomVersion"],
            "lastLoginDate": profile["lastLoginDate"],
            "lastPlayDate": profile["lastPlayDate"],
            "playerRating": profile["playerRating"],
            "nameplateId": 0,  # Unused
            "iconId": profile["iconId"],
            "trophyId": 0,  # Unused
            "partnerId": profile["partnerId"],
            "frameId": profile["frameId"],
            "dispRate": option[
                "dispRate"
            ],  # 0: all/begin, 1: disprate, 2: dispDan, 3: hide, 4: end
            "totalAwake": profile["totalAwake"],
            "isNetMember": profile["isNetMember"],
            "dailyBonusDate": profile["dailyBonusDate"],
            "headPhoneVolume": option["headPhoneVolume"],
            "isInherit": False,  # Not sure what this is or does??
            "banState": profile["banState"]
            if profile["banState"] is not None
            else 0,  # New with uni+
        }

    async def handle_upload_user_playlog_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        playlog = data["userPlaylog"]

        await self.data.score.put_playlog(user_id, playlog)

        return {"returnCode": 1, "apiName": "UploadUserPlaylogApi"}

    async def handle_upsert_user_chargelog_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        charge = data["userCharge"]

        # remove the ".0" from the date string, festival only?
        charge["purchaseDate"] = charge["purchaseDate"].replace(".0", "")
        await self.data.item.put_charge(
            user_id,
            charge["chargeId"],
            charge["stock"],
            datetime.strptime(charge["purchaseDate"], Mai2Constants.DATE_TIME_FORMAT),
            datetime.strptime(charge["validDate"], Mai2Constants.DATE_TIME_FORMAT),
        )

        return {"returnCode": 1, "apiName": "UpsertUserChargelogApi"}

    async def handle_upsert_user_all_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        upsert = data["upsertUserAll"]
        
        if int(user_id) & 0x1000000000001 == 0x1000000000001:
            place_id = int(user_id) & 0xFFFC00000000
            
            self.logger.info("Guest play from place ID %d, ignoring.", place_id)
            return {"returnCode": 1, "apiName": "UpsertUserAllApi"}

        if "userData" in upsert and len(upsert["userData"]) > 0:
            upsert["userData"][0]["isNetMember"] = 1
            upsert["userData"][0].pop("accessCode")
            await self.data.profile.put_profile_detail(
                user_id, self.version, upsert["userData"][0]
            )

        if "userExtend" in upsert and len(upsert["userExtend"]) > 0:
            await self.data.profile.put_profile_extend(
                user_id, self.version, upsert["userExtend"][0]
            )

        if "userGhost" in upsert:
            for ghost in upsert["userGhost"]:
                await self.data.profile.put_profile_ghost(user_id, self.version, ghost)

        if "userOption" in upsert and len(upsert["userOption"]) > 0:
            await self.data.profile.put_profile_option(
                user_id, self.version, upsert["userOption"][0]
            )

        if "userRatingList" in upsert and len(upsert["userRatingList"]) > 0:
            await self.data.profile.put_profile_rating(
                user_id, self.version, upsert["userRatingList"][0]
            )

        if "userActivityList" in upsert and len(upsert["userActivityList"]) > 0:
            for k, v in upsert["userActivityList"][0].items():
                for act in v:
                    await self.data.profile.put_profile_activity(user_id, act)

        if "userChargeList" in upsert and len(upsert["userChargeList"]) > 0:
            for charge in upsert["userChargeList"]:
                # remove the ".0" from the date string, festival only?
                charge["purchaseDate"] = charge["purchaseDate"].replace(".0", "")
                await self.data.item.put_charge(
                    user_id,
                    charge["chargeId"],
                    charge["stock"],
                    datetime.strptime(
                        charge["purchaseDate"], Mai2Constants.DATE_TIME_FORMAT
                    ),
                    datetime.strptime(
                        charge["validDate"], Mai2Constants.DATE_TIME_FORMAT
                    ),
                )

        if "userCharacterList" in upsert and len(upsert["userCharacterList"]) > 0:
            for char in upsert["userCharacterList"]:
                await self.data.item.put_character(
                    user_id,
                    char["characterId"],
                    char["level"],
                    char["awakening"],
                    char["useCount"],
                )

        if "userItemList" in upsert and len(upsert["userItemList"]) > 0:
            for item in upsert["userItemList"]:
                if item["itemKind"] == 4:
                    item_id = item["itemId"] % 1000000
                    item_kind = item["itemId"] // 1000000
                else:
                    item_id = item["itemId"]
                    item_kind = item["itemKind"]
                
                await self.data.item.put_item(
                    user_id,
                    item_kind,
                    item_id,
                    item["stock"],
                    item["isValid"],
                )

        if "userLoginBonusList" in upsert and len(upsert["userLoginBonusList"]) > 0:
            for login_bonus in upsert["userLoginBonusList"]:
                await self.data.item.put_login_bonus(
                    user_id,
                    login_bonus["bonusId"],
                    login_bonus["point"],
                    login_bonus["isCurrent"],
                    login_bonus["isComplete"],
                )

        if "userMapList" in upsert and len(upsert["userMapList"]) > 0:
            for map in upsert["userMapList"]:
                await self.data.item.put_map(
                    user_id,
                    map["mapId"],
                    map["distance"],
                    map["isLock"],
                    map["isClear"],
                    map["isComplete"],
                )

        if "userMusicDetailList" in upsert and len(upsert["userMusicDetailList"]) > 0:
            for music in upsert["userMusicDetailList"]:
                await self.data.score.put_best_score(user_id, music)

        if "userCourseList" in upsert and len(upsert["userCourseList"]) > 0:
            for course in upsert["userCourseList"]:
                await self.data.score.put_course(user_id, course)

        if "userFavoriteList" in upsert and len(upsert["userFavoriteList"]) > 0:
            for fav in upsert["userFavoriteList"]:
                kind_id = fav.get("kind", fav.get("itemKind")) # itemKind key used in BUDDiES+
                if kind_id is not None:
                    await self.data.item.put_favorite(user_id, kind_id, fav["itemIdList"])

        if "userFavoritemusicList" in upsert and len(upsert["userFavoritemusicList"]) > 0:
            for fav in upsert["userFavoritemusicList"]:
                await self.data.item.add_fav_music(user_id, fav["id"], fav["orderId"])

        if (
            "userFriendSeasonRankingList" in upsert
            and len(upsert["userFriendSeasonRankingList"]) > 0
        ):
            for fsr in upsert["userFriendSeasonRankingList"]:
                fsr["recordDate"] = (
                    datetime.strptime(
                        fsr["recordDate"], f"{Mai2Constants.DATE_TIME_FORMAT}.0"
                    ),
                )
                await self.data.item.put_friend_season_ranking(user_id, fsr)
        
        if "user2pPlaylog" in upsert:
            await self.data.score.put_playlog_2p(user_id, upsert["user2pPlaylog"])

        # added in BUDDiES+
        if "userIntimateList" in upsert and len(upsert["userIntimateList"]) > 0:
            for intimate in upsert["userIntimateList"]:
                await self.data.profile.put_intimacy(user_id, intimate["partnerId"], intimate["intimateLevel"], intimate["intimateCountRewarded"])

        return {"returnCode": 1, "apiName": "UpsertUserAllApi"}

    async def handle_get_user_data_api_request(self, data: Dict) -> Dict:
        profile = await self.data.profile.get_profile_detail(data["userId"], self.version)
        if profile is None:
            return

        profile_dict = profile._asdict()
        profile_dict.pop("id")
        profile_dict.pop("user")
        profile_dict.pop("version")

        return {"userId": data["userId"], "userData": profile_dict}

    async def handle_get_user_extend_api_request(self, data: Dict) -> Dict:
        extend = await self.data.profile.get_profile_extend(data["userId"], self.version)
        if extend is None:
            return

        extend_dict = extend._asdict()
        extend_dict.pop("id")
        extend_dict.pop("user")
        extend_dict.pop("version")

        return {"userId": data["userId"], "userExtend": extend_dict}

    async def handle_get_user_option_api_request(self, data: Dict) -> Dict:
        options = await self.data.profile.get_profile_option(data["userId"], self.version)
        if options is None:
            return

        options_dict = options._asdict()
        options_dict.pop("id")
        options_dict.pop("user")
        options_dict.pop("version")

        return {"userId": data["userId"], "userOption": options_dict}

    async def handle_get_user_card_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]        
        
        rows = await self.data.item.get_cards(user_id, limit=max_ct + 1, offset=next_idx)
        
        if rows is None:
            return {"userId": user_id, "nextIndex": 0, "userCardList": []}

        card_list = []

        for row in rows[:max_ct]:
            card = row._asdict()
            card.pop("id")
            card.pop("user")
            card["startDate"] = datetime.strftime(
                card["startDate"], Mai2Constants.DATE_TIME_FORMAT
            )
            card["endDate"] = datetime.strftime(
                card["endDate"], Mai2Constants.DATE_TIME_FORMAT
            )
            card_list.append(card)
    
        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": data["userId"],
            "nextIndex": next_idx,
            "userCardList": card_list,
        }

    async def handle_get_user_item_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]

        kind = next_idx // 10000000000
        next_idx = next_idx % 10000000000

        items: List[Dict[str, Any]] = []
        
        if kind == 4: # presents
            rows = await self.data.item.get_presents_by_version_user(
                version=self.version,
                user_id=user_id,
                exclude_owned=True,
                exclude_not_in_present_period=True,
                limit=max_ct + 1,
                offset=next_idx,
            )

            if rows is None:
                return {
                    "userId": user_id,
                    "nextIndex": 0,
                    "itemKind": kind,
                    "userItemList": [],
                }
            
            for row in rows[:max_ct]:
                self.logger.info(
                    f"Give user {user_id} {row['stock']}x item {row['itemId']} (kind {row['itemKind']}) as present"
                )

                items.append(
                    {
                        "itemId": row["itemKind"] * 1000000 + row["itemId"],
                        "itemKind": kind,
                        "stock": row["stock"],
                        "isValid": True,
                    }
                )
        else:
            rows = await self.data.item.get_items(
                user_id=user_id,
                item_kind=kind,
                limit=max_ct + 1,
                offset=next_idx,
            )

            if rows is None:
                return {
                    "userId": user_id,
                    "nextIndex": 0,
                    "itemKind": kind,
                    "userItemList": [],
                }

            for row in rows[:max_ct]:
                item = row._asdict()
                
                item.pop("id")
                item.pop("user")

                items.append(item)

        if len(rows) > max_ct:
            next_idx = kind * 10000000000 + next_idx + max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "nextIndex": next_idx,
            "itemKind": kind,
            "userItemList": items,
        }

    async def handle_get_user_character_api_request(self, data: Dict) -> Dict:
        characters = await self.data.item.get_characters(data["userId"])

        chara_list = []
        for chara in characters:
            tmp = chara._asdict()
            tmp.pop("id")
            tmp.pop("user")
            chara_list.append(tmp)

        return {"userId": data["userId"], "userCharacterList": chara_list}

    async def handle_get_user_favorite_api_request(self, data: Dict) -> Dict:
        favorites = await self.data.item.get_favorites(data["userId"], data["itemKind"])
        if favorites is None:
            return

        userFavs = []
        for fav in favorites:
            userFavs.append(
                {
                    "userId": data["userId"],
                    "itemKind": fav["itemKind"],
                    "itemIdList": fav["itemIdList"],
                }
            )

        return {"userId": data["userId"], "userFavoriteData": userFavs}

    async def handle_get_user_ghost_api_request(self, data: Dict) -> Dict:
        ghost = await self.data.profile.get_profile_ghost(data["userId"], self.version)
        if ghost is None:
            return

        ghost_dict = ghost._asdict()
        ghost_dict.pop("user")
        ghost_dict.pop("id")
        ghost_dict.pop("version_int")

        return {"userId": data["userId"], "userGhost": ghost_dict}

    async def handle_get_user_rating_api_request(self, data: Dict) -> Dict:
        rating = await self.data.profile.get_profile_rating(data["userId"], self.version)
        if rating is None:
            return

        rating_dict = rating._asdict()
        rating_dict.pop("user")
        rating_dict.pop("id")
        rating_dict.pop("version")

        return {"userId": data["userId"], "userRating": rating_dict}

    async def handle_get_user_activity_api_request(self, data: Dict) -> Dict:
        """
        kind 1 is playlist, kind 2 is music list
        """
        playlist = await self.data.profile.get_profile_activity(data["userId"], 1)
        musiclist = await self.data.profile.get_profile_activity(data["userId"], 2)
        if playlist is None or musiclist is None:
            return

        plst = []
        mlst = []

        for play in playlist:
            tmp = play._asdict()
            tmp["id"] = tmp["activityId"]
            tmp.pop("activityId")
            tmp.pop("user")
            plst.append(tmp)

        for music in musiclist:
            tmp = music._asdict()
            tmp["id"] = tmp["activityId"]
            tmp.pop("activityId")
            tmp.pop("user")
            mlst.append(tmp)

        return {"userActivity": {"playList": plst, "musicList": mlst}}

    async def handle_get_user_course_api_request(self, data: Dict) -> Dict:
        user_courses = await self.data.score.get_courses(data["userId"])
        if user_courses is None:
            return {"userId": data["userId"], "nextIndex": 0, "userCourseList": []}

        course_list = []
        for course in user_courses:
            tmp = course._asdict()
            tmp.pop("user")
            tmp.pop("id")
            course_list.append(tmp)

        return {"userId": data["userId"], "nextIndex": 0, "userCourseList": course_list}

    async def handle_get_user_portrait_api_request(self, data: Dict) -> Dict:
        # No support for custom pfps
        return {"length": 0, "userPortraitList": []}

    async def handle_get_user_friend_season_ranking_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]

        rows = await self.data.item.get_friend_season_ranking(
            user_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {
                "userId": user_id,
                "nextIndex": 0,
                "userFriendSeasonRankingList": [],
            }

        friend_season_ranking_list = []

        for row in rows[:max_ct]:
            friend_season_ranking = row._asdict()
            
            friend_season_ranking.pop("user")
            friend_season_ranking.pop("id")
            friend_season_ranking["recordDate"] = datetime.strftime(
                friend_season_ranking["recordDate"], f"{Mai2Constants.DATE_TIME_FORMAT}.0"
            )
            
            friend_season_ranking_list.append(friend_season_ranking)

        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "nextIndex": next_idx,
            "userFriendSeasonRankingList": friend_season_ranking_list,
        }

    async def handle_get_user_map_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]

        rows = await self.data.item.get_maps(
            user_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {
                "userId": user_id,
                "nextIndex": 0,
                "userMapList": [],
            }

        map_list = []

        for row in rows[:max_ct]:
            map = row._asdict()
            
            map.pop("user")
            map.pop("id")
            
            map_list.append(map)

        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "nextIndex": next_idx,
            "userMapList": map_list,
        }

    async def handle_get_user_login_bonus_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]

        rows = await self.data.item.get_login_bonuses(
            user_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {
                "userId": user_id,
                "nextIndex": 0,
                "userLoginBonusList": [],
            }

        login_bonus_list = []

        for row in rows[:max_ct]:
            login_bonus = row._asdict()
            
            login_bonus.pop("user")
            login_bonus.pop("id")
            
            login_bonus_list.append(login_bonus)

        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "nextIndex": next_idx,
            "userLoginBonusList": login_bonus_list,
        }

    async def handle_get_user_region_api_request(self, data: Dict) -> Dict:
        """
        class UserRegionList:
            regionId: int
            playCount: int
            created: str
        """
        return {"userId": data["userId"], "length": 0, "userRegionList": []}

    async def handle_get_user_rival_data_api_request(self, data: Dict) -> Dict:
        user_id = data.get("userId", 0)
        rival_id = data.get("rivalId", 0)

        if not user_id or not rival_id: return {}

        rival_pf = await self.data.profile.get_profile_detail(rival_id, self.version)
        if not rival_pf: return {}

        return {
            "userId": user_id,
            "userRivalData": {
                "rivalId": rival_id,
                "rivalName": rival_pf['userName']
            }
        }

    async def handle_get_user_rival_music_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        rival_id: int = data["rivalId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = 100
        levels: list[int] = [x["level"] for x in data["userRivalMusicLevelList"]]        

        rows = await self.data.score.get_best_scores(
            rival_id,
            is_dx=True,
            limit=max_ct + 1,
            offset=next_idx,
            levels=levels,
        )

        if rows is None:
            self.logger.debug("handle_get_user_rival_music_api_request: get_best_scores returned None!")

            return {
                "userId": user_id,
                "rivalId": rival_id,
                "nextIndex": 0,
                "userRivalMusicList": [] # musicId userRivalMusicDetailList -> level achievement deluxscoreMax
            }
        
        music_details = [x._asdict() for x in rows]
        returned_count = 0
        music_list = []

        for music_id, details_iter in itertools.groupby(music_details, key=lambda x: x["musicId"]):
            details: list[dict[Any, Any]] = []

            for d in details_iter:
                details.append(
                    {
                        "level": d["level"],
                        "achievement": d["achievement"],
                        "deluxscoreMax": d["deluxscoreMax"],
                    }
                )

            music_list.append({"musicId": music_id, "userRivalMusicDetailList": details})
            returned_count += len(details)

            if len(music_list) >= max_ct:
                break

        if returned_count < len(rows):
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "rivalId": rival_id,
            "nextIndex": next_idx,
            "userRivalMusicList": music_list,
        }

    async def handle_get_user_new_item_api_request(self, data: Dict) -> Dict:
        # TODO: Added in 1.41, implement this?
        user_id = data["userId"]
        version = data.get("version", 1041000)
        user_playlog_list = data.get("userPlaylogList", [])
        
        return {
            "userId": user_id,
            "itemKind": -1,
            "itemId": -1,
        }

    async def handle_get_user_music_api_request(self, data: Dict) -> Dict:
        user_id: int = data.get("userId", 0)        
        next_idx: int = data.get("nextIndex", 0)
        max_ct: int = data.get("maxCount", 50)

        if user_id <= 0:
            self.logger.warning("handle_get_user_music_api_request: Could not find userid in data, or userId is 0")
            return {}
        
        rows = await self.data.score.get_best_scores(
            user_id, is_dx=True, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            self.logger.debug("handle_get_user_music_api_request: get_best_scores returned None!")

            return {
                "userId": user_id,
                "nextIndex": 0,
                "userMusicList": [],
            }

        music_details = [row._asdict() for row in rows]
        returned_count = 0
        music_list = []

        for _music_id, details_iter in itertools.groupby(music_details, key=lambda d: d["musicId"]):
            details: list[dict[Any, Any]] = []

            for d in details_iter:
                d.pop("id")
                d.pop("user")
                
                details.append(d)

            music_list.append({"userMusicDetailList": details})
            returned_count += len(details)

            if len(music_list) >= max_ct:
                break
        
        if returned_count < len(rows):
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "userId": user_id,
            "nextIndex": next_idx,
            "userMusicList": music_list,
        }

    async def handle_user_login_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_user_login_api_request(data)
        if ret is None or not ret:
            return ret
        ret['loginId'] = ret.get('loginCount', 0)
        return ret

    # Intimate api added in BUDDiES+
    async def handle_get_user_intimate_api_request(self, data: Dict) -> Dict:
        intimate = await self.data.profile.get_intimacy(data["userId"])
        if intimate is None:
            return {}

        partner_list = [{
            "partnerId": i["partnerId"],
            "intimateLevel": i["intimateLevel"],
            "intimateCountRewarded": i["intimateCountRewarded"]
        } for i in intimate]

        return {
            "userId": data["userId"],
            "length": len(partner_list),
            "userIntimateList": partner_list
        }

    # CardMaker support added in Universe
    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_detail(data["userId"], self.version)
        if p is None:
            return {}

        return {
            "userName": p["userName"],
            "rating": p["playerRating"],
            # hardcode lastDataVersion for CardMaker
            "lastDataVersion": "1.20.00", # Future versiohs should replace this with the correct version
            # checks if the user is still logged in
            "isLogin": False,
            "isExistSellingCard": True,
        }

    async def handle_cm_get_user_data_api_request(self, data: Dict) -> Dict:
        # user already exists, because the preview checks that already
        p = await self.data.profile.get_profile_detail(data["userId"], self.version)

        cards = await self.data.card.get_user_cards(data["userId"])
        if cards is None or len(cards) == 0:
            # This should never happen
            self.logger.error(
                f"handle_get_user_data_api_request: Internal error - No cards found for user id {data['userId']}"
            )
            return {}

        # get the dict representation of the row so we can modify values
        user_data = p._asdict()

        # remove the values the game doesn't want
        user_data.pop("id")
        user_data.pop("user")
        user_data.pop("version")

        return {"userId": data["userId"], "userData": user_data}

    async def handle_cm_login_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1}

    async def handle_cm_logout_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1}

    async def handle_cm_get_selling_card_api_request(self, data: Dict) -> Dict:
        selling_cards = await self.data.static.get_enabled_cards(self.version)
        if selling_cards is None:
            return {"length": 0, "sellingCardList": []}

        selling_card_list = []
        for card in selling_cards:
            tmp = card._asdict()
            tmp.pop("id")
            tmp.pop("version")
            tmp.pop("cardName")
            tmp.pop("enabled")

            tmp["startDate"] = datetime.strftime(
                tmp["startDate"], Mai2Constants.DATE_TIME_FORMAT
            )
            tmp["endDate"] = datetime.strftime(
                tmp["endDate"], Mai2Constants.DATE_TIME_FORMAT
            )
            tmp["noticeStartDate"] = datetime.strftime(
                tmp["noticeStartDate"], Mai2Constants.DATE_TIME_FORMAT
            )
            tmp["noticeEndDate"] = datetime.strftime(
                tmp["noticeEndDate"], Mai2Constants.DATE_TIME_FORMAT
            )

            selling_card_list.append(tmp)

        return {"length": len(selling_card_list), "sellingCardList": selling_card_list}

    async def handle_cm_get_user_card_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        next_idx: int = data["nextIndex"]
        max_ct: int = data["maxCount"]

        rows = await self.data.item.get_cards(
            user_id, limit=max_ct + 1, offset=next_idx
        )

        if rows is None:
            return {"returnCode": 1, "length": 0, "nextIndex": 0, "userCardList": []}

        card_list = []

        for row in rows[:max_ct]:
            card = row._asdict()
            
            card.pop("id")
            card.pop("user")
            card["startDate"] = datetime.strftime(
                card["startDate"], Mai2Constants.DATE_TIME_FORMAT
            )
            card["endDate"] = datetime.strftime(
                card["endDate"], Mai2Constants.DATE_TIME_FORMAT
            )

            card_list.append(card)
        
        if len(rows) > max_ct:
            next_idx += max_ct
        else:
            next_idx = 0

        return {
            "returnCode": 1,
            "length": len(card_list),
            "nextIndex": next_idx,
            "userCardList": card_list,
        }

    async def handle_cm_get_user_item_api_request(self, data: Dict) -> Dict:
        await self.handle_get_user_item_api_request(data)

    async def handle_cm_get_user_character_api_request(self, data: Dict) -> Dict:
        characters = await self.data.item.get_characters(data["userId"])

        chara_list = []
        for chara in characters:
            chara_list.append(
                {
                    "characterId": chara["characterId"],
                    # no clue why those values are even needed
                    "point": 0,
                    "count": 0,
                    "level": chara["level"],
                    "nextAwake": 0,
                    "nextAwakePercent": 0,
                    "favorite": False,
                    "awakening": chara["awakening"],
                    "useCount": chara["useCount"],
                }
            )

        return {
            "returnCode": 1,
            "length": len(chara_list),
            "userCharacterList": chara_list,
        }

    async def handle_cm_get_user_card_print_error_api_request(self, data: Dict) -> Dict:
        return {"length": 0, "userPrintDetailList": []}

    async def handle_cm_upsert_user_print_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        upsert = data["userPrintDetail"]

        # set a random card serial number
        serial_id = "".join([str(randint(0, 9)) for _ in range(20)])

        # calculate start and end date of the card
        start_date = datetime.utcnow()
        end_date = datetime.utcnow() + timedelta(days=15)

        user_card = upsert["userCard"]
        await self.data.item.put_card(
            user_id,
            user_card["cardId"],
            user_card["cardTypeId"],
            user_card["charaId"],
            user_card["mapId"],
            # add the correct start date and also the end date in 15 days
            start_date,
            end_date,
        )

        # get the profile extend to save the new bought card
        extend = await self.data.profile.get_profile_extend(user_id, self.version)
        if extend:
            extend = extend._asdict()
            # parse the selectedCardList
            # 6 = Freedom Pass, 4 = Gold Pass (cardTypeId)
            selected_cards: List = extend["selectedCardList"]

            # if no pass is already added, add the corresponding pass
            if not user_card["cardTypeId"] in selected_cards:
                selected_cards.insert(0, user_card["cardTypeId"])

            extend["selectedCardList"] = selected_cards
            await self.data.profile.put_profile_extend(user_id, self.version, extend)

        # properly format userPrintDetail for the database
        upsert.pop("userCard")
        upsert.pop("serialId")
        upsert["printDate"] = datetime.strptime(upsert["printDate"], "%Y-%m-%d")

        await self.data.item.put_user_print_detail(user_id, serial_id, upsert)

        return {
            "returnCode": 1,
            "orderId": 0,
            "serialId": serial_id,
            "startDate": datetime.strftime(start_date, Mai2Constants.DATE_TIME_FORMAT),
            "endDate": datetime.strftime(end_date, Mai2Constants.DATE_TIME_FORMAT),
        }

    async def handle_cm_upsert_user_printlog_api_request(self, data: Dict) -> Dict:
        return {
            "returnCode": 1,
            "orderId": 0,
            "serialId": data["userPrintlog"]["serialId"],
        }

    async def handle_cm_upsert_buy_card_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1}
