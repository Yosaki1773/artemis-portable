from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Table, UniqueConstraint, and_, or_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.types import BIGINT, INTEGER, JSON, TIMESTAMP, Boolean, Integer, String

from core.data.schema import BaseData, metadata

character: Table = Table(
    "mai2_item_character",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("characterId", Integer),
    Column("level", Integer),
    Column("awakening", Integer),
    Column("useCount", Integer),
    Column("point", Integer),
    UniqueConstraint("user", "characterId", name="mai2_item_character_uk"),
    mysql_charset="utf8mb4",
)

card: Table = Table(
    "mai2_item_card",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("cardId", Integer),
    Column("cardTypeId", Integer),
    Column("charaId", Integer),
    Column("mapId", Integer),
    Column("startDate", TIMESTAMP, server_default=func.now()),
    Column("endDate", TIMESTAMP),
    UniqueConstraint("user", "cardId", "cardTypeId", name="mai2_item_card_uk"),
    mysql_charset="utf8mb4",
)

item: Table = Table(
    "mai2_item_item",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("itemId", Integer),
    Column("itemKind", Integer),
    Column("stock", Integer),
    Column("isValid", Boolean),
    UniqueConstraint("user", "itemId", "itemKind", name="mai2_item_item_uk"),
    mysql_charset="utf8mb4",
)

map: Table = Table(
    "mai2_item_map",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("mapId", Integer),
    Column("distance", Integer),
    Column("isLock", Boolean),
    Column("isClear", Boolean),
    Column("isComplete", Boolean),
    UniqueConstraint("user", "mapId", name="mai2_item_map_uk"),
    mysql_charset="utf8mb4",
)

login_bonus: Table = Table(
    "mai2_item_login_bonus",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("bonusId", Integer),
    Column("point", Integer),
    Column("isCurrent", Boolean),
    Column("isComplete", Boolean),
    UniqueConstraint("user", "bonusId", name="mai2_item_login_bonus_uk"),
    mysql_charset="utf8mb4",
)

friend_season_ranking: Table = Table(
    "mai2_item_friend_season_ranking",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("seasonId", Integer),
    Column("point", Integer),
    Column("rank", Integer),
    Column("rewardGet", Boolean),
    Column("userName", String(8)),
    Column("recordDate", TIMESTAMP),
    UniqueConstraint(
        "user", "seasonId", "userName", name="mai2_item_friend_season_ranking_uk"
    ),
    mysql_charset="utf8mb4",
)

favorite = Table(
    "mai2_item_favorite",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("itemKind", Integer),
    Column("itemIdList", JSON),
    UniqueConstraint("user", "itemKind", name="mai2_item_favorite_uk"),
    mysql_charset="utf8mb4",
)

fav_music: Table = Table(
    "mai2_item_favorite_music",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("musicId", Integer, nullable=False),
    Column("orderId", Integer, nullable=True),
    UniqueConstraint("user", "musicId", name="mai2_item_favorite_music_uk"),
    mysql_charset="utf8mb4",
)

charge = Table(
    "mai2_item_charge",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("chargeId", Integer),
    Column("stock", Integer),
    Column("purchaseDate", String(255)),
    Column("validDate", String(255)),
    UniqueConstraint("user", "chargeId", name="mai2_item_charge_uk"),
    mysql_charset="utf8mb4",
)

print_detail = Table(
    "mai2_item_print_detail",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("orderId", Integer),
    Column("printNumber", Integer),
    Column("printDate", TIMESTAMP, server_default=func.now()),
    Column("serialId", String(20)),
    Column("placeId", Integer),
    Column("clientId", String(11)),
    Column("printerSerialId", String(20)),
    Column("cardRomVersion", Integer),
    Column("isHolograph", Boolean, server_default="1"),
    Column("printOption1", Boolean, server_default="0"),
    Column("printOption2", Boolean, server_default="0"),
    Column("printOption3", Boolean, server_default="0"),
    Column("printOption4", Boolean, server_default="0"),
    Column("printOption5", Boolean, server_default="0"),
    Column("printOption6", Boolean, server_default="0"),
    Column("printOption7", Boolean, server_default="0"),
    Column("printOption8", Boolean, server_default="0"),
    Column("printOption9", Boolean, server_default="0"),
    Column("printOption10", Boolean, server_default="0"),
    Column("created", String(255), server_default=""),
    UniqueConstraint("user", "serialId", name="mai2_item_print_detail_uk"),
    mysql_charset="utf8mb4",
)

present: Table = Table(
    "mai2_item_present",
    metadata,
    Column('id', BIGINT, primary_key=True, nullable=False),
    Column('version', INTEGER),
    Column("user", Integer, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade")),
    Column("itemKind", INTEGER, nullable=False),
    Column("itemId", INTEGER, nullable=False),
    Column("stock", INTEGER, nullable=False, server_default="1"),
    Column("startDate", TIMESTAMP),
    Column("endDate", TIMESTAMP),
    UniqueConstraint("version", "user", "itemKind", "itemId", name="mai2_item_present_uk"),
    mysql_charset="utf8mb4",
)

class Mai2ItemData(BaseData):
    async def put_item(
        self, user_id: int, item_kind: int, item_id: int, stock: int, is_valid: bool
    ) -> None:
        sql = insert(item).values(
            user=user_id,
            itemKind=item_kind,
            itemId=item_id,
            stock=stock,
            isValid=is_valid,
        )

        conflict = sql.on_duplicate_key_update(
            stock=stock,
            isValid=is_valid,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_item: failed to insert item! user_id: {user_id}, item_kind: {item_kind}, item_id: {item_id}"
            )
            return None
        return result.lastrowid

    async def get_items(
        self,
        user_id: int,
        item_kind: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        cond = item.c.user == user_id

        if item_kind is not None:
            cond &= item.c.itemKind == item_kind

        sql = select(item).where(cond)

        if limit is not None or offset is not None:
            sql = sql.order_by(item.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_item(self, user_id: int, item_kind: int, item_id: int) -> Optional[Row]:
        sql = item.select(
            and_(
                item.c.user == user_id,
                item.c.itemKind == item_kind,
                item.c.itemId == item_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_login_bonus(
        self,
        user_id: int,
        bonus_id: int,
        point: int,
        is_current: bool,
        is_complete: bool,
    ) -> None:
        sql = insert(login_bonus).values(
            user=user_id,
            bonusId=bonus_id,
            point=point,
            isCurrent=is_current,
            isComplete=is_complete,
        )

        conflict = sql.on_duplicate_key_update(
            point=point,
            isCurrent=is_current,
            isComplete=is_complete,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_login_bonus: failed to insert item! user_id: {user_id}, bonus_id: {bonus_id}, point: {point}"
            )
            return None
        return result.lastrowid

    async def get_login_bonuses(
        self,
        user_id: int,
        limit: Optional[int] = None, 
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(login_bonus).where(login_bonus.c.user == user_id)

        if limit is not None or offset is not None:
            sql = sql.order_by(login_bonus.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_login_bonus(self, user_id: int, bonus_id: int) -> Optional[Row]:
        sql = login_bonus.select(
            and_(login_bonus.c.user == user_id, login_bonus.c.bonus_id == bonus_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_map(
        self,
        user_id: int,
        map_id: int,
        distance: int,
        is_lock: bool,
        is_clear: bool,
        is_complete: bool,
    ) -> None:
        sql = insert(map).values(
            user=user_id,
            mapId=map_id,
            distance=distance,
            isLock=is_lock,
            isClear=is_clear,
            isComplete=is_complete,
        )

        conflict = sql.on_duplicate_key_update(
            distance=distance,
            isLock=is_lock,
            isClear=is_clear,
            isComplete=is_complete,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_map: failed to insert item! user_id: {user_id}, map_id: {map_id}, distance: {distance}"
            )
            return None
        return result.lastrowid

    async def get_maps(
        self,
        user_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(map).where(map.c.user == user_id)

        if limit is not None or offset is not None:
            sql = sql.order_by(map.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_map(self, user_id: int, map_id: int) -> Optional[Row]:
        sql = map.select(and_(map.c.user == user_id, map.c.mapId == map_id))

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_character_(self, user_id: int, char_data: Dict) -> Optional[int]:
        char_data["user"] = user_id
        sql = insert(character).values(**char_data)

        conflict = sql.on_duplicate_key_update(**char_data)
        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_character_: failed to insert item! user_id: {user_id}"
            )
            return None
        return result.lastrowid

    async def put_character(
        self,
        user_id: int,
        character_id: int,
        level: int,
        awakening: int,
        use_count: int,
    ) -> None:
        sql = insert(character).values(
            user=user_id,
            characterId=character_id,
            level=level,
            awakening=awakening,
            useCount=use_count,
        )

        conflict = sql.on_duplicate_key_update(
            level=level,
            awakening=awakening,
            useCount=use_count,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_character: failed to insert item! user_id: {user_id}, character_id: {character_id}, level: {level}"
            )
            return None
        return result.lastrowid

    async def get_characters(self, user_id: int) -> Optional[List[Row]]:
        sql = character.select(character.c.user == user_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_character(self, user_id: int, character_id: int) -> Optional[Row]:
        sql = character.select(
            and_(character.c.user == user_id, character.c.character_id == character_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_friend_season_ranking(
        self,
        user_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(friend_season_ranking).where(friend_season_ranking.c.user == user_id)

        if limit is not None or offset is not None:
            sql = sql.order_by(friend_season_ranking.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_friend_season_ranking(
        self, aime_id: int, friend_season_ranking_data: Dict
    ) -> Optional[int]:
        sql = insert(friend_season_ranking).values(
            user=aime_id, **friend_season_ranking_data
        )

        conflict = sql.on_duplicate_key_update(**friend_season_ranking_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_friend_season_ranking: failed to insert",
                f"friend_season_ranking! aime_id: {aime_id}",
            )
            return None
        return result.lastrowid

    async def put_favorite(
        self, user_id: int, kind: int, item_id_list: List[int]
    ) -> Optional[int]:
        sql = insert(favorite).values(
            user=user_id, itemKind=kind, itemIdList=item_id_list
        )

        conflict = sql.on_duplicate_key_update(itemIdList=item_id_list)

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_favorite: failed to insert item! user_id: {user_id}, kind: {kind}"
            )
            return None
        return result.lastrowid

    async def get_favorites(self, user_id: int, kind: int = None) -> Optional[Row]:
        if kind is None:
            sql = favorite.select(favorite.c.user == user_id)
        else:
            sql = favorite.select(
                and_(favorite.c.user == user_id, favorite.c.itemKind == kind)
            )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_fav_music(
        self,
        user_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(fav_music).where(fav_music.c.user == user_id)

        if limit is not None or offset is not None:
            sql = sql.order_by(fav_music.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)

        if result:
            return result.fetchall()

    async def add_fav_music(self, user_id: int, music_id: int, order_id: Optional[int] = None) -> Optional[int]:
        sql = insert(fav_music).values(
            user = user_id,
            musicId = music_id,
            orderId = order_id
        )
        
        conflict = sql.on_duplicate_key_update(orderId = order_id)
        
        result = await self.execute(conflict)
        if result:
            return result.lastrowid
        
        self.logger.error(f"Failed to add music {music_id} as favorite for user {user_id}!")
        
    async def remove_fav_music(self, user_id: int, music_id: int) -> None:
        result = await self.execute(fav_music.delete(and_(fav_music.c.user == user_id, fav_music.c.musicId == music_id)))
        if not result:
            self.logger.error(f"Failed to remove music {music_id} as favorite for user {user_id}!")

    async def put_card(
        self,
        user_id: int,
        card_type_id: int,
        card_kind: int,
        chara_id: int,
        map_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Row]:
        sql = insert(card).values(
            user=user_id,
            cardId=card_type_id,
            cardTypeId=card_kind,
            charaId=chara_id,
            mapId=map_id,
            startDate=start_date,
            endDate=end_date,
        )

        conflict = sql.on_duplicate_key_update(
            charaId=chara_id, mapId=map_id, startDate=start_date, endDate=end_date
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_card: failed to insert card! user_id: {user_id}, kind: {card_kind}"
            )
            return None
        return result.lastrowid

    async def get_cards(
        self,
        user_id: int,
        kind: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        condition = card.c.user == user_id

        if kind is not None:
            condition &= card.c.cardKind == kind

        sql = select(card).where(condition).order_by(card.c.startDate.desc(), card.c.id.asc())

        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_charge(
        self,
        user_id: int,
        charge_id: int,
        stock: int,
        purchase_date: str,
        valid_date: str,
    ) -> Optional[Row]:
        sql = insert(charge).values(
            user=user_id,
            chargeId=charge_id,
            stock=stock,
            purchaseDate=purchase_date,
            validDate=valid_date,
        )

        conflict = sql.on_duplicate_key_update(
            stock=stock, purchaseDate=purchase_date, validDate=valid_date
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"put_card: failed to insert charge! user_id: {user_id}, chargeId: {charge_id}"
            )
            return None
        return result.lastrowid

    async def get_charges(self, user_id: int) -> Optional[Row]:
        sql = charge.select(charge.c.user == user_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_user_print_detail(
        self, aime_id: int, serial_id: str, user_print_data: Dict
    ) -> Optional[int]:
        sql = insert(print_detail).values(
            user=aime_id, serialId=serial_id, **user_print_data
        )

        conflict = sql.on_duplicate_key_update(**user_print_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_user_print_detail: Failed to insert! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid

    async def put_present(self, item_kind: int, item_id: int, version: int = None, user_id: int = None, start_date: datetime = None, end_date: datetime = None) -> Optional[int]:
        sql = insert(present).values(
            version = version,
            user = user_id,
            itemKind = item_kind,
            itemId = item_id,
            startDate = start_date,
            endDate = end_date
        )
        
        conflict = sql.on_duplicate_key_update(
            startDate = start_date,
            endDate = end_date
        )
        
        result = await self.execute(conflict)
        if result:
            return result.lastrowid
        
        self.logger.error(f"Failed to add present item {item_id}!")
    
    async def get_presents_by_user(self, user_id: int = None) -> Optional[List[Row]]:
        result = await self.execute(present.select(or_(present.c.user == user_id, present.c.user is None)))
        if result:
            return result.fetchall()

    async def get_presents_by_version(self, ver: int = None) -> Optional[List[Row]]:
        result = await self.execute(present.select(or_(present.c.version == ver, present.c.version is None)))
        if result:
            return result.fetchall()

    async def get_presents_by_version_user(
        self,
        version: Optional[int] = None,
        user_id: Optional[int] = None,
        exclude_owned: bool = False,
        exclude_not_in_present_period: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(present)
        condition = (
            ((present.c.user == user_id) | present.c.user.is_(None))
            & ((present.c.version == version) | present.c.version.is_(None))
        )

        # Do an anti-join with the mai2_item_item table to exclude any
        # items the users have already owned.
        if exclude_owned:
            sql = sql.join(
                item,
                (present.c.itemKind == item.c.itemKind)
                & (present.c.itemId == item.c.itemId)
            )
            condition &= (item.c.itemKind.is_(None) & item.c.itemId.is_(None))

        if exclude_not_in_present_period:
            condition &= (present.c.startDate.is_(None) | (present.c.startDate <= func.now()))
            condition &= (present.c.endDate.is_(None) | (present.c.endDate >= func.now()))
        
        sql = sql.where(condition)

        if limit is not None or offset is not None:
            sql = sql.order_by(present.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)

        if result:
            return result.fetchall()
    
    async def get_present_by_id(self, present_id: int) -> Optional[Row]:
        result = await self.execute(present.select(present.c.id == present_id))
        if result:
            return result.fetchone()
