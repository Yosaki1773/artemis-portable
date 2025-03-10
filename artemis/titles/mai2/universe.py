from datetime import datetime, timedelta
from random import randint
from typing import Dict, List

from core.config import CoreConfig
from titles.mai2.config import Mai2Config
from titles.mai2.const import Mai2Constants
from titles.mai2.splashplus import Mai2SplashPlus


class Mai2Universe(Mai2SplashPlus):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_UNIVERSE

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_detail(data["userId"], self.version)
        if p is None:
            return {}

        return {
            "userName": p["userName"],
            "rating": p["playerRating"],
            # hardcode lastDataVersion for CardMaker
            "lastDataVersion": "1.20.00",
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
        user_cards = await self.data.item.get_cards(data["userId"])
        if user_cards is None:
            return {"returnCode": 1, "length": 0, "nextIndex": 0, "userCardList": []}

        max_ct = data["maxCount"]
        next_idx = data["nextIndex"]
        start_idx = next_idx
        end_idx = max_ct + start_idx

        if len(user_cards[start_idx:]) > max_ct:
            next_idx += max_ct
        else:
            next_idx = 0

        card_list = []
        for card in user_cards:
            tmp = card._asdict()
            tmp.pop("id")
            tmp.pop("user")

            tmp["startDate"] = datetime.strftime(
                tmp["startDate"], Mai2Constants.DATE_TIME_FORMAT
            )
            tmp["endDate"] = datetime.strftime(
                tmp["endDate"], Mai2Constants.DATE_TIME_FORMAT
            )
            card_list.append(tmp)

        return {
            "returnCode": 1,
            "length": len(card_list[start_idx:end_idx]),
            "nextIndex": next_idx,
            "userCardList": card_list[start_idx:end_idx],
        }

    async def handle_cm_get_user_item_api_request(self, data: Dict) -> Dict:
        await super().handle_get_user_item_api_request(data)

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
