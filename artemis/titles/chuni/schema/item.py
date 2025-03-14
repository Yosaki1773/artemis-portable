from typing import Dict, List, Optional

from sqlalchemy import (
    Column,
    PrimaryKeyConstraint,
    Table,
    UniqueConstraint,
    and_,
    delete,
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.types import JSON, TIMESTAMP, Boolean, Integer, String

from core.data.schema import BaseData, metadata

character: Table = Table(
    "chuni_item_character",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("characterId", Integer),
    Column("level", Integer),
    Column("param1", Integer),
    Column("param2", Integer),
    Column("isValid", Boolean),
    Column("skillId", Integer),
    Column("isNewMark", Boolean),
    Column("playCount", Integer),
    Column("friendshipExp", Integer),
    Column("assignIllust", Integer),
    Column("exMaxLv", Integer),
    UniqueConstraint("user", "characterId", name="chuni_item_character_uk"),
    mysql_charset="utf8mb4",
)

item: Table = Table(
    "chuni_item_item",
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
    UniqueConstraint("user", "itemId", "itemKind", name="chuni_item_item_uk"),
    mysql_charset="utf8mb4",
)

duel = Table(
    "chuni_item_duel",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("duelId", Integer),
    Column("progress", Integer),
    Column("point", Integer),
    Column("isClear", Boolean),
    Column("lastPlayDate", String(25)),
    Column("param1", Integer),
    Column("param2", Integer),
    Column("param3", Integer),
    Column("param4", Integer),
    UniqueConstraint("user", "duelId", name="chuni_item_duel_uk"),
    mysql_charset="utf8mb4",
)

map = Table(
    "chuni_item_map",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("mapId", Integer),
    Column("position", Integer),
    Column("isClear", Boolean),
    Column("areaId", Integer),
    Column("routeNumber", Integer),
    Column("eventId", Integer),
    Column("rate", Integer),
    Column("statusCount", Integer),
    Column("isValid", Boolean),
    UniqueConstraint("user", "mapId", name="chuni_item_map_uk"),
    mysql_charset="utf8mb4",
)

map_area = Table(
    "chuni_item_map_area",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("mapAreaId", Integer),
    Column("rate", Integer),
    Column("isClear", Boolean),
    Column("isLocked", Boolean),
    Column("position", Integer),
    Column("statusCount", Integer),
    Column("remainGridCount", Integer),
    UniqueConstraint("user", "mapAreaId", name="chuni_item_map_area_uk"),
    mysql_charset="utf8mb4",
)

gacha = Table(
    "chuni_item_gacha",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("gachaId", Integer, nullable=False),
    Column("totalGachaCnt", Integer, server_default="0"),
    Column("ceilingGachaCnt", Integer, server_default="0"),
    Column("dailyGachaCnt", Integer, server_default="0"),
    Column("fiveGachaCnt", Integer, server_default="0"),
    Column("elevenGachaCnt", Integer, server_default="0"),
    Column("dailyGachaDate", TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("user", "gachaId", name="chuni_item_gacha_uk"),
    mysql_charset="utf8mb4",
)

print_state: Table = Table(
    "chuni_item_print_state",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("hasCompleted", Boolean, nullable=False, server_default="0"),
    Column(
        "limitDate", TIMESTAMP, nullable=False, server_default="2038-01-01 00:00:00.0"
    ),
    Column("placeId", Integer),
    Column("cardId", Integer),
    Column("gachaId", Integer),
    UniqueConstraint("id", "user", name="chuni_item_print_state_uk"),
    mysql_charset="utf8mb4",
)

print_detail = Table(
    "chuni_item_print_detail",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("cardId", Integer, nullable=False),
    Column("printDate", TIMESTAMP, nullable=False),
    Column("serialId", String(20), nullable=False),
    Column("placeId", Integer, nullable=False),
    Column("clientId", String(11), nullable=False),
    Column("printerSerialId", String(20), nullable=False),
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
    UniqueConstraint("serialId", name="chuni_item_print_detail_uk"),
    mysql_charset="utf8mb4",
)

login_bonus = Table(
    "chuni_item_login_bonus",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("version", Integer, nullable=False),
    Column("presetId", Integer, nullable=False),
    Column("bonusCount", Integer, nullable=False, server_default="0"),
    Column("lastUpdateDate", TIMESTAMP, server_default="2018-01-01 00:00:00.0"),
    Column("isWatched", Boolean, server_default="0"),
    Column("isFinished", Boolean, server_default="0"),
    UniqueConstraint("version", "user", "presetId", name="chuni_item_login_bonus_uk"),
    mysql_charset="utf8mb4",
)

favorite: Table = Table(
    "chuni_item_favorite",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("version", Integer, nullable=False),
    Column("favId", Integer, nullable=False),
    Column("favKind", Integer, nullable=False, server_default="1"),
    UniqueConstraint("version", "user", "favId", name="chuni_item_favorite_uk"),
    mysql_charset="utf8mb4",
)

matching = Table(
    "chuni_item_matching",
    metadata,
    Column("roomId", Integer, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("version", Integer, nullable=False),
    Column("restMSec", Integer, nullable=False, server_default="60"),
    Column("isFull", Boolean, nullable=False, server_default="0"),
    PrimaryKeyConstraint("roomId", "version", name="chuni_item_matching_pk"),
    Column("matchingMemberInfoList", JSON, nullable=False),
    mysql_charset="utf8mb4",
)

cmission = Table(
    "chuni_item_cmission",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("missionId", Integer, nullable=False),
    Column("point", Integer),
    UniqueConstraint("user", "missionId", name="chuni_item_cmission_uk"),
    mysql_charset="utf8mb4",
)

cmission_progress = Table(
    "chuni_item_cmission_progress",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("user", ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("missionId", Integer, nullable=False),
    Column("order", Integer),
    Column("stage", Integer),
    Column("progress", Integer),
    UniqueConstraint(
        "user", "missionId", "order", name="chuni_item_cmission_progress_uk"
    ),
    mysql_charset="utf8mb4",
)


class ChuniItemData(BaseData):
    async def get_oldest_free_matching(self, version: int) -> Optional[Row]:
        sql = matching.select(
            and_(
                matching.c.version == version,
                matching.c.isFull == False
            )
        ).order_by(matching.c.roomId.asc())

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_newest_matching(self, version: int) -> Optional[Row]:
        sql = matching.select(
            and_(
                matching.c.version == version
            )
        ).order_by(matching.c.roomId.desc())

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_all_matchings(self, version: int) -> Optional[List[Row]]:
        sql = matching.select(
            and_(
                matching.c.version == version
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_matching(self, version: int, room_id: int) -> Optional[Row]:
        sql = matching.select(
            and_(matching.c.version == version, matching.c.roomId == room_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_matching(
        self,
        version: int,
        room_id: int,
        matching_member_info_list: List,
        user_id: int = None,
        rest_sec: int = 60,
        is_full: bool = False
    ) -> Optional[int]:
        sql = insert(matching).values(
            roomId=room_id,
            version=version,
            restMSec=rest_sec,
            user=user_id,
            isFull=is_full,
            matchingMemberInfoList=matching_member_info_list,
        )

        conflict = sql.on_duplicate_key_update(
            restMSec=rest_sec, matchingMemberInfoList=matching_member_info_list
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def delete_matching(self, version: int, room_id: int):
        sql = delete(matching).where(
            and_(matching.c.roomId == room_id, matching.c.version == version)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def is_favorite(
        self, user_id: int, version: int, fav_id: int, fav_kind: int = 1
    ) -> bool:

        sql = favorite.select(
            and_(
                favorite.c.version == version,
                favorite.c.user == user_id,
                favorite.c.favId == fav_id,
                favorite.c.favKind == fav_kind,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return False

        return True if len(result.all()) else False

    async def get_all_favorites(
        self,
        user_id: int,
        version: int,
        fav_kind: int = 1,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(favorite).where(
            and_(
                favorite.c.version == version,
                favorite.c.user == user_id,
                favorite.c.favKind == fav_kind,
            )
        )

        if limit is not None or offset is not None:
            sql = sql.order_by(favorite.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_login_bonus(
        self, user_id: int, version: int, preset_id: int, **login_bonus_data
    ) -> Optional[int]:
        sql = insert(login_bonus).values(
            version=version, user=user_id, presetId=preset_id, **login_bonus_data
        )

        conflict = sql.on_duplicate_key_update(presetId=preset_id, **login_bonus_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_all_login_bonus(
        self, user_id: int, version: int, is_finished: bool = False
    ) -> Optional[List[Row]]:
        sql = login_bonus.select(
            and_(
                login_bonus.c.version == version,
                login_bonus.c.user == user_id,
                login_bonus.c.isFinished == is_finished,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_login_bonus(
        self, user_id: int, version: int, preset_id: int
    ) -> Optional[Row]:
        sql = login_bonus.select(
            and_(
                login_bonus.c.version == version,
                login_bonus.c.user == user_id,
                login_bonus.c.presetId == preset_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_favorite_music(self, user_id: int, version: int, music_id: int) -> Optional[int]:
        sql = insert(favorite).values(user=user_id, version=version, favId=music_id, favKind=1)

        conflict = sql.on_duplicate_key_update(user=user_id, version=version, favId=music_id, favKind=1)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def delete_favorite_music(self, user_id: int, version: int, music_id: int) -> Optional[int]:
        sql = delete(favorite).where(
            and_(
                favorite.c.user==user_id, 
                favorite.c.version==version, 
                favorite.c.favId==music_id, 
                favorite.c.favKind==1
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def put_character(self, user_id: int, character_data: Dict) -> Optional[int]:
        character_data["user"] = user_id

        character_data = self.fix_bools(character_data)

        sql = insert(character).values(**character_data)
        conflict = sql.on_duplicate_key_update(**character_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_character(self, user_id: int, character_id: int) -> Optional[Dict]:
        sql = select(character).where(
            and_(character.c.user == user_id, character.c.characterId == character_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_characters(
        self, user_id: int, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Optional[List[Row]]:
        sql = select(character).where(character.c.user == user_id)

        if limit is not None or offset is not None:
            sql = sql.order_by(character.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_item(self, user_id: int, item_data: Dict) -> Optional[int]:
        item_data["user"] = user_id

        item_data = self.fix_bools(item_data)

        sql = insert(item).values(**item_data)
        conflict = sql.on_duplicate_key_update(**item_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_items(
        self,
        user_id: int,
        kind: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        cond = item.c.user == user_id

        if kind is not None:
            cond &= item.c.itemKind == kind

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

    async def put_duel(self, user_id: int, duel_data: Dict) -> Optional[int]:
        duel_data["user"] = user_id

        duel_data = self.fix_bools(duel_data)

        sql = insert(duel).values(**duel_data)
        conflict = sql.on_duplicate_key_update(**duel_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_duels(self, user_id: int) -> Optional[List[Row]]:
        sql = select(duel).where(duel.c.user == user_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_map(self, user_id: int, map_data: Dict) -> Optional[int]:
        map_data["user"] = user_id

        map_data = self.fix_bools(map_data)

        sql = insert(map).values(**map_data)
        conflict = sql.on_duplicate_key_update(**map_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_maps(self, user_id: int) -> Optional[List[Row]]:
        sql = select(map).where(map.c.user == user_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_map_area(self, user_id: int, map_area_data: Dict) -> Optional[int]:
        map_area_data["user"] = user_id

        map_area_data = self.fix_bools(map_area_data)

        sql = insert(map_area).values(**map_area_data)
        conflict = sql.on_duplicate_key_update(**map_area_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_map_areas(self, user_id: int, map_area_ids: List[int]) -> Optional[List[Row]]:
        sql = select(map_area).where(map_area.c.user == user_id, map_area.c.mapAreaId.in_(map_area_ids))

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_user_gachas(self, aime_id: int) -> Optional[List[Row]]:
        sql = gacha.select(gacha.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_user_gacha(
        self, aime_id: int, gacha_id: int, gacha_data: Dict
    ) -> Optional[int]:
        sql = insert(gacha).values(user=aime_id, gachaId=gacha_id, **gacha_data)

        conflict = sql.on_duplicate_key_update(
            user=aime_id, gachaId=gacha_id, **gacha_data
        )
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(f"put_user_gacha: Failed to insert! aime_id: {aime_id}")
            return None
        return result.lastrowid

    async def get_user_print_states(
        self,
        aime_id: int,
        has_completed: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(print_state).where(
            and_(
                print_state.c.user == aime_id,
                print_state.c.hasCompleted == has_completed,
            )
        )

        if limit is not None or offset is not None:
            sql = sql.order_by(print_state.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_user_print_states_by_gacha(
        self, aime_id: int, gacha_id: int, has_completed: bool = False
    ) -> Optional[List[Row]]:
        sql = print_state.select(
            and_(
                print_state.c.user == aime_id,
                print_state.c.gachaId == gacha_id,
                print_state.c.hasCompleted == has_completed,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_user_print_state(self, aime_id: int, **print_data) -> Optional[int]:
        sql = insert(print_state).values(user=aime_id, **print_data)

        conflict = sql.on_duplicate_key_update(user=aime_id, **print_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_user_print_state: Failed to insert! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid

    async def put_user_print_detail(
        self, aime_id: int, serial_id: str, user_print_data: Dict
    ) -> Optional[int]:
        sql = insert(print_detail).values(
            user=aime_id, serialId=serial_id, **user_print_data
        )

        conflict = sql.on_duplicate_key_update(user=aime_id, **user_print_data)
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                f"put_user_print_detail: Failed to insert! aime_id: {aime_id}"
            )
            return None
        return result.lastrowid
    
    async def put_cmission_progress(
        self, user_id: int, mission_id: int, progress_data: Dict
    ) -> Optional[int]:
        progress_data["user"] = user_id
        progress_data["missionId"] = mission_id

        sql = insert(cmission_progress).values(**progress_data)
        conflict = sql.on_duplicate_key_update(**progress_data)
        result = await self.execute(conflict)
        
        if result is None:
            return None
        
        return result.lastrowid

    async def get_cmission_progress(
        self, user_id: int, mission_id: int
    ) -> Optional[List[Row]]:
        sql = cmission_progress.select(
            and_(
                cmission_progress.c.user == user_id,
                cmission_progress.c.missionId == mission_id,
            )
        ).order_by(cmission_progress.c.order.asc())
        result = await self.execute(sql)
        
        if result is None:
            return None
        
        return result.fetchall()
    
    async def get_cmission(self, user_id: int, mission_id: int) -> Optional[Row]:
        sql = cmission.select(
            and_(cmission.c.user == user_id, cmission.c.missionId == mission_id)
        )
        result = await self.execute(sql)
        
        if result is None:
            return None
        
        return result.fetchone()

    async def put_cmission(self, user_id: int, mission_data: Dict) -> Optional[int]:
        mission_data["user"] = user_id

        sql = insert(cmission).values(**mission_data)
        conflict = sql.on_duplicate_key_update(**mission_data)
        result = await self.execute(conflict)
        
        if result is None:
            return None
        
        return result.lastrowid

    async def get_cmissions(self, user_id: int) -> Optional[List[Row]]:
        sql = cmission.select(cmission.c.user == user_id)
        result = await self.execute(sql)
        
        if result is None:
            return None
        
        return result.fetchall()
