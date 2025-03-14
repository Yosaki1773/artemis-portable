from typing import Dict, List, Optional
from sqlalchemy import (
    ForeignKeyConstraint,
    Table,
    Column,
    UniqueConstraint,
    PrimaryKeyConstraint,
    and_,
)
from sqlalchemy.types import Integer, String, TIMESTAMP, Boolean, JSON, Float
from sqlalchemy.engine.base import Connection
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.dialects.mysql import insert
from datetime import datetime

from core.data.schema import BaseData, metadata

events = Table(
    "chuni_static_events",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("eventId", Integer),
    Column("type", Integer),
    Column("name", String(255)),
    Column("startDate", TIMESTAMP, server_default=func.now()),
    Column("enabled", Boolean, server_default="1"),
    UniqueConstraint("version", "eventId", name="chuni_static_events_uk"),
    mysql_charset="utf8mb4",
)

music = Table(
    "chuni_static_music",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("songId", Integer),
    Column("chartId", Integer),
    Column("title", String(255)),
    Column("artist", String(255)),
    Column("level", Float),
    Column("genre", String(255)),
    Column("jacketPath", String(255)),
    Column("worldsEndTag", String(7)),
    UniqueConstraint("version", "songId", "chartId", name="chuni_static_music_uk"),
    mysql_charset="utf8mb4",
)

charge = Table(
    "chuni_static_charge",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("chargeId", Integer),
    Column("name", String(255)),
    Column("expirationDays", Integer),
    Column("consumeType", Integer),
    Column("sellingAppeal", Boolean),
    Column("enabled", Boolean, server_default="1"),
    UniqueConstraint("version", "chargeId", name="chuni_static_charge_uk"),
    mysql_charset="utf8mb4",
)

avatar = Table(
    "chuni_static_avatar",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("avatarAccessoryId", Integer),
    Column("name", String(255)),
    Column("category", Integer),
    Column("iconPath", String(255)),
    Column("texturePath", String(255)),
    Column("isEnabled", Boolean, server_default="1"),
    Column("defaultHave", Boolean, server_default="0"),
    Column("sortName", String(255)),
    UniqueConstraint("version", "avatarAccessoryId", name="chuni_static_avatar_uk"),
    mysql_charset="utf8mb4",
)

nameplate = Table(
    "chuni_static_nameplate",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("nameplateId", Integer),
    Column("name", String(255)),
    Column("texturePath", String(255)),
    Column("isEnabled", Boolean, server_default="1"),
    Column("defaultHave", Boolean, server_default="0"),
    Column("sortName", String(255)),
    UniqueConstraint("version", "nameplateId", name="chuni_static_nameplate_uk"),
    mysql_charset="utf8mb4",
)

character = Table(
    "chuni_static_character",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("characterId", Integer),
    Column("name", String(255)),
    Column("sortName", String(255)),
    Column("worksName", String(255)),
    Column("rareType", Integer),
    Column("imagePath1", String(255)),
    Column("imagePath2", String(255)),
    Column("imagePath3", String(255)),
    Column("isEnabled", Boolean, server_default="1"),
    Column("defaultHave", Boolean, server_default="0"),
    UniqueConstraint("version", "characterId", name="chuni_static_character_uk"),
    mysql_charset="utf8mb4",
)

trophy = Table(
    "chuni_static_trophy",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("trophyId", Integer),
    Column("name", String(255)),
    Column("rareType", Integer),
    Column("isEnabled", Boolean, server_default="1"),
    Column("defaultHave", Boolean, server_default="0"),
    UniqueConstraint("version", "trophyId", name="chuni_static_trophy_uk"),
    mysql_charset="utf8mb4",
)

map_icon = Table(
    "chuni_static_map_icon",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("mapIconId", Integer),
    Column("name", String(255)),
    Column("sortName", String(255)),
    Column("iconPath", String(255)),
    Column("isEnabled", Boolean, server_default="1"),
    Column("defaultHave", Boolean, server_default="0"),
    UniqueConstraint("version", "mapIconId", name="chuni_static_mapicon_uk"),
    mysql_charset="utf8mb4",
)

system_voice = Table(
    "chuni_static_system_voice",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("voiceId", Integer),
    Column("name", String(255)),
    Column("sortName", String(255)),
    Column("imagePath", String(255)),
    Column("isEnabled", Boolean, server_default="1"),
    Column("defaultHave", Boolean, server_default="0"),
    UniqueConstraint("version", "voiceId", name="chuni_static_systemvoice_uk"),
    mysql_charset="utf8mb4",
)

gachas = Table(
    "chuni_static_gachas",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("gachaId", Integer, nullable=False),
    Column("gachaName", String(255), nullable=False),
    Column("type", Integer, nullable=False, server_default="0"),
    Column("kind", Integer, nullable=False, server_default="0"),
    Column("isCeiling", Boolean, server_default="0"),
    Column("ceilingCnt", Integer, server_default="10"),
    Column("changeRateCnt1", Integer, server_default="0"),
    Column("changeRateCnt2", Integer, server_default="0"),
    Column("startDate", TIMESTAMP, server_default="2018-01-01 00:00:00.0"),
    Column("endDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("noticeStartDate", TIMESTAMP, server_default="2018-01-01 00:00:00.0"),
    Column("noticeEndDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    UniqueConstraint("version", "gachaId", "gachaName", name="chuni_static_gachas_uk"),
    mysql_charset="utf8mb4",
)

cards = Table(
    "chuni_static_cards",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("cardId", Integer, nullable=False),
    Column("charaName", String(255), nullable=False),
    Column("charaId", Integer, nullable=False),
    Column("presentName", String(255), nullable=False),
    Column("rarity", Integer, server_default="2"),
    Column("labelType", Integer, nullable=False),
    Column("difType", Integer, nullable=False),
    Column("miss", Integer, nullable=False),
    Column("combo", Integer, nullable=False),
    Column("chain", Integer, nullable=False),
    Column("skillName", String(255), nullable=False),
    UniqueConstraint("version", "cardId", name="chuni_static_cards_uk"),
    mysql_charset="utf8mb4",
)

gacha_cards = Table(
    "chuni_static_gacha_cards",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("gachaId", Integer, nullable=False),
    Column("cardId", Integer, nullable=False),
    Column("rarity", Integer, nullable=False),
    Column("weight", Integer, server_default="1"),
    Column("isPickup", Boolean, server_default="0"),
    UniqueConstraint("gachaId", "cardId", name="chuni_static_gacha_cards_uk"),
    mysql_charset="utf8mb4",
)

login_bonus_preset = Table(
    "chuni_static_login_bonus_preset",
    metadata,
    Column("presetId", Integer, nullable=False),
    Column("version", Integer, nullable=False),
    Column("presetName", String(255), nullable=False),
    Column("isEnabled", Boolean, server_default="1"),
    PrimaryKeyConstraint(
        "presetId", "version", name="chuni_static_login_bonus_preset_pk"
    ),
    mysql_charset="utf8mb4",
)

login_bonus = Table(
    "chuni_static_login_bonus",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("presetId", Integer, nullable=False),
    Column("loginBonusId", Integer, nullable=False),
    Column("loginBonusName", String(255), nullable=False),
    Column("presentId", Integer, nullable=False),
    Column("presentName", String(255), nullable=False),
    Column("itemNum", Integer, nullable=False),
    Column("needLoginDayCount", Integer, nullable=False),
    Column("loginBonusCategoryType", Integer, nullable=False),
    UniqueConstraint(
        "version", "presetId", "loginBonusId", name="chuni_static_login_bonus_uk"
    ),
    ForeignKeyConstraint(
        ["presetId", "version"],
        [
            "chuni_static_login_bonus_preset.presetId",
            "chuni_static_login_bonus_preset.version",
        ],
        onupdate="CASCADE",
        ondelete="CASCADE",
        name="chuni_static_login_bonus_ibfk_1",
    ),
    mysql_charset="utf8mb4",
)


class ChuniStaticData(BaseData):
    async def put_login_bonus(
        self,
        version: int,
        preset_id: int,
        login_bonus_id: int,
        login_bonus_name: str,
        present_id: int,
        present_ame: str,
        item_num: int,
        need_login_day_count: int,
        login_bonus_category_type: int,
    ) -> Optional[int]:
        sql = insert(login_bonus).values(
            version=version,
            presetId=preset_id,
            loginBonusId=login_bonus_id,
            loginBonusName=login_bonus_name,
            presentId=present_id,
            presentName=present_ame,
            itemNum=item_num,
            needLoginDayCount=need_login_day_count,
            loginBonusCategoryType=login_bonus_category_type,
        )

        conflict = sql.on_duplicate_key_update(
            loginBonusName=login_bonus_name,
            presentName=present_ame,
            itemNum=item_num,
            needLoginDayCount=need_login_day_count,
            loginBonusCategoryType=login_bonus_category_type,
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_login_bonus(
        self,
        version: int,
        preset_id: int,
    ) -> Optional[List[Row]]:
        sql = login_bonus.select(
            and_(
                login_bonus.c.version == version,
                login_bonus.c.presetId == preset_id,
            )
        ).order_by(login_bonus.c.needLoginDayCount.desc())

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_login_bonus_by_required_days(
        self, version: int, preset_id: int, need_login_day_count: int
    ) -> Optional[Row]:
        sql = login_bonus.select(
            and_(
                login_bonus.c.version == version,
                login_bonus.c.presetId == preset_id,
                login_bonus.c.needLoginDayCount == need_login_day_count,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_login_bonus_preset(
        self, version: int, preset_id: int, preset_name: str, is_enabled: bool
    ) -> Optional[int]:
        sql = insert(login_bonus_preset).values(
            presetId=preset_id,
            version=version,
            presetName=preset_name,
            isEnabled=is_enabled,
        )

        conflict = sql.on_duplicate_key_update(
            presetName=preset_name, isEnabled=is_enabled
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_login_bonus_presets(
        self, version: int, is_enabled: bool = True
    ) -> Optional[List[Row]]:
        sql = login_bonus_preset.select(
            and_(
                login_bonus_preset.c.version == version,
                login_bonus_preset.c.isEnabled == is_enabled,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_event(
        self, version: int, event_id: int, type: int, name: str
    ) -> Optional[int]:
        sql = insert(events).values(
            version=version, eventId=event_id, type=type, name=name
        )

        conflict = sql.on_duplicate_key_update(name=name)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def update_event(
        self, version: int, event_id: int, enabled: bool
    ) -> Optional[bool]:
        sql = events.update(
            and_(events.c.version == version, events.c.eventId == event_id)
        ).values(enabled=enabled)

        result = await self.execute(sql)
        if result is None:
            self.logger.warning(
                f"update_event: failed to update event! version: {version}, event_id: {event_id}, enabled: {enabled}"
            )
            return None

        event = self.get_event(version, event_id)
        if event is None:
            self.logger.warning(
                f"update_event: failed to fetch event {event_id} after updating"
            )
            return None
        return event["enabled"]

    async def get_event(self, version: int, event_id: int) -> Optional[Row]:
        sql = select(events).where(
            and_(events.c.version == version, events.c.eventId == event_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_enabled_events(self, version: int) -> Optional[List[Row]]:
        sql = select(events).where(
            and_(events.c.version == version, events.c.enabled == True)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_events(self, version: int) -> Optional[List[Row]]:
        sql = select(events).where(events.c.version == version)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_music(
        self,
        version: int,
        song_id: int,
        chart_id: int,
        title: int,
        artist: str,
        level: float,
        genre: str,
        jacketPath: str,
        we_tag: str,
    ) -> Optional[int]:
        sql = insert(music).values(
            version=version,
            songId=song_id,
            chartId=chart_id,
            title=title,
            artist=artist,
            level=level,
            genre=genre,
            jacketPath=jacketPath,
            worldsEndTag=we_tag,
        )

        conflict = sql.on_duplicate_key_update(
            title=title,
            artist=artist,
            level=level,
            genre=genre,
            jacketPath=jacketPath,
            worldsEndTag=we_tag,
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def put_charge(
        self,
        version: int,
        charge_id: int,
        name: str,
        expiration_days: int,
        consume_type: int,
        selling_appeal: bool,
    ) -> Optional[int]:
        sql = insert(charge).values(
            version=version,
            chargeId=charge_id,
            name=name,
            expirationDays=expiration_days,
            consumeType=consume_type,
            sellingAppeal=selling_appeal,
        )

        conflict = sql.on_duplicate_key_update(
            name=name,
            expirationDays=expiration_days,
            consumeType=consume_type,
            sellingAppeal=selling_appeal,
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_enabled_charges(self, version: int) -> Optional[List[Row]]:
        sql = select(charge).where(
            and_(charge.c.version == version, charge.c.enabled == True)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_charges(self, version: int) -> Optional[List[Row]]:
        sql = select(charge).where(charge.c.version == version)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_music(self, version: int) -> Optional[List[Row]]:
        sql = music.select(music.c.version <= version)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_music_chart(
        self, version: int, song_id: int, chart_id: int
    ) -> Optional[List[Row]]:
        sql = select(music).where(
            and_(
                music.c.version == version,
                music.c.songId == song_id,
                music.c.chartId == chart_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_song(self, music_id: int) -> Optional[Row]:
        sql = music.select(music.c.songId == music_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()


    async def put_avatar(
        self,
        version: int,
        avatarAccessoryId: int,
        name: str,
        category: int,
        iconPath: str,
        texturePath: str,
        isEnabled: int,
        defaultHave: int,
        sortName: str
    ) -> Optional[int]:
        sql = insert(avatar).values(
            version=version,
            avatarAccessoryId=avatarAccessoryId,
            name=name,
            category=category,
            iconPath=iconPath,
            texturePath=texturePath,
            isEnabled=isEnabled,
            defaultHave=defaultHave,
            sortName=sortName
        )

        conflict = sql.on_duplicate_key_update(
            name=name,
            category=category,
            iconPath=iconPath,
            texturePath=texturePath,
            isEnabled=isEnabled,
            defaultHave=defaultHave,
            sortName=sortName
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_avatar_items(self, version: int, category: int, enabled_only: bool = True) -> Optional[List[Dict]]:
        if enabled_only:
            sql = select(avatar).where((avatar.c.version == version) & (avatar.c.category == category) & (avatar.c.isEnabled)).order_by(avatar.c.sortName)
        else:
            sql = select(avatar).where((avatar.c.version == version) & (avatar.c.category == category)).order_by(avatar.c.sortName)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def put_nameplate(
        self,
        version: int,
        nameplateId: int,
        name: str,
        texturePath: str,
        isEnabled: int,
        defaultHave: int,
        sortName: str
    ) -> Optional[int]:
        sql = insert(nameplate).values(
            version=version,
            nameplateId=nameplateId,
            name=name,
            texturePath=texturePath,
            isEnabled=isEnabled,
            defaultHave=defaultHave,
            sortName=sortName
        )

        conflict = sql.on_duplicate_key_update(
            name=name,
            texturePath=texturePath,
            isEnabled=isEnabled,
            defaultHave=defaultHave,
            sortName=sortName
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_nameplates(self, version: int, enabled_only: bool = True) -> Optional[List[Dict]]:
        if enabled_only:
            sql = select(nameplate).where((nameplate.c.version == version) & (nameplate.c.isEnabled)).order_by(nameplate.c.sortName)
        else:
            sql = select(nameplate).where(nameplate.c.version == version).order_by(nameplate.c.sortName)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def put_trophy(
        self,
        version: int,
        trophyId: int,
        name: str,
        rareType: int,
        isEnabled: int,
        defaultHave: int,
    ) -> Optional[int]:
        sql = insert(trophy).values(
            version=version,
            trophyId=trophyId,
            name=name,
            rareType=rareType,
            isEnabled=isEnabled,
            defaultHave=defaultHave
        )

        conflict = sql.on_duplicate_key_update(
            name=name,
            rareType=rareType,
            isEnabled=isEnabled,
            defaultHave=defaultHave
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_trophies(self, version: int, enabled_only: bool = True) -> Optional[List[Dict]]:
        if enabled_only:
            sql = select(trophy).where((trophy.c.version == version) & (trophy.c.isEnabled)).order_by(trophy.c.name)
        else:
            sql = select(trophy).where(trophy.c.version == version).order_by(trophy.c.name)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def put_map_icon(
        self,
        version: int,
        mapIconId: int,
        name: str,
        sortName: str,
        iconPath: str,
        isEnabled: int,
        defaultHave: int,
    ) -> Optional[int]:
        sql = insert(map_icon).values(
            version=version,
            mapIconId=mapIconId,
            name=name,
            sortName=sortName,
            iconPath=iconPath,
            isEnabled=isEnabled,
            defaultHave=defaultHave
        )

        conflict = sql.on_duplicate_key_update(
            name=name,
            sortName=sortName,
            iconPath=iconPath,
            isEnabled=isEnabled,
            defaultHave=defaultHave
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_map_icons(self, version: int, enabled_only: bool = True) -> Optional[List[Dict]]:
        if enabled_only:
            sql = select(map_icon).where((map_icon.c.version == version) & (map_icon.c.isEnabled)).order_by(map_icon.c.sortName)
        else:
            sql = select(map_icon).where(map_icon.c.version == version).order_by(map_icon.c.sortName)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def put_system_voice(
        self,
        version: int,
        voiceId: int,
        name: str,
        sortName: str,
        imagePath: str,
        isEnabled: int,
        defaultHave: int,
    ) -> Optional[int]:
        sql = insert(system_voice).values(
            version=version,
            voiceId=voiceId,
            name=name,
            sortName=sortName,
            imagePath=imagePath,
            isEnabled=isEnabled,
            defaultHave=defaultHave
        )

        conflict = sql.on_duplicate_key_update(
            name=name,
            sortName=sortName,
            imagePath=imagePath,
            isEnabled=isEnabled,
            defaultHave=defaultHave
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_system_voices(self, version: int, enabled_only: bool = True) -> Optional[List[Dict]]:
        if enabled_only:
            sql = select(system_voice).where((system_voice.c.version == version) & (system_voice.c.isEnabled)).order_by(system_voice.c.sortName)
        else:
            sql = select(system_voice).where(system_voice.c.version == version).order_by(system_voice.c.sortName)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def put_character(
        self,
        version: int,
        characterId: int,
        name: str,
        sortName: str,
        worksName: str,
        rareType: int,
        imagePath1: str,
        imagePath2: str,
        imagePath3: str,
        isEnabled: int,
        defaultHave: int
    ) -> Optional[int]:
        sql = insert(character).values(
            version=version,
            characterId=characterId,
            name=name,
            sortName=sortName,
            worksName=worksName,
            rareType=rareType,
            imagePath1=imagePath1,
            imagePath2=imagePath2,
            imagePath3=imagePath3,
            isEnabled=isEnabled,
            defaultHave=defaultHave
        )

        conflict = sql.on_duplicate_key_update(
            name=name,
            sortName=sortName,
            worksName=worksName,
            rareType=rareType,
            imagePath1=imagePath1,
            imagePath2=imagePath2,
            imagePath3=imagePath3,
            isEnabled=isEnabled,
            defaultHave=defaultHave
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_characters(self, version: int, enabled_only: bool = True) -> Optional[List[Dict]]:
        if enabled_only:
            sql = select(character).where((character.c.version == version) & (character.c.isEnabled)).order_by(character.c.sortName)
        else:
            sql = select(character).where(character.c.version == version).order_by(character.c.sortName)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def put_gacha(
        self,
        version: int,
        gacha_id: int,
        gacha_name: int,
        **gacha_data,
    ) -> Optional[int]:
        sql = insert(gachas).values(
            version=version,
            gachaId=gacha_id,
            gachaName=gacha_name,
            **gacha_data,
        )

        conflict = sql.on_duplicate_key_update(
            version=version,
            gachaId=gacha_id,
            gachaName=gacha_name,
            **gacha_data,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert gacha! gacha_id {gacha_id}")
            return None
        return result.lastrowid

    async def get_gachas(self, version: int) -> Optional[List[Dict]]:
        sql = gachas.select(gachas.c.version <= version).order_by(
            gachas.c.gachaId.asc()
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_gacha(self, version: int, gacha_id: int) -> Optional[Dict]:
        sql = gachas.select(
            and_(gachas.c.version <= version, gachas.c.gachaId == gacha_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_gacha_card(
        self, gacha_id: int, card_id: int, **gacha_card
    ) -> Optional[int]:
        sql = insert(gacha_cards).values(gachaId=gacha_id, cardId=card_id, **gacha_card)

        conflict = sql.on_duplicate_key_update(
            gachaId=gacha_id, cardId=card_id, **gacha_card
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert gacha card! gacha_id {gacha_id}")
            return None
        return result.lastrowid

    async def get_gacha_cards(self, gacha_id: int) -> Optional[List[Dict]]:
        sql = gacha_cards.select(gacha_cards.c.gachaId == gacha_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_gacha_card_by_character(
        self, gacha_id: int, chara_id: int
    ) -> Optional[Dict]:
        sql_sub = (
            select(cards.c.cardId).filter(cards.c.charaId == chara_id).scalar_subquery()
        )

        # Perform the main query, also rename the resulting column to ranking
        sql = gacha_cards.select(
            and_(gacha_cards.c.gachaId == gacha_id, gacha_cards.c.cardId == sql_sub)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def put_card(self, version: int, card_id: int, **card_data) -> Optional[int]:
        sql = insert(cards).values(version=version, cardId=card_id, **card_data)

        conflict = sql.on_duplicate_key_update(**card_data)

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert card! card_id {card_id}")
            return None
        return result.lastrowid

    async def get_card(self, version: int, card_id: int) -> Optional[Dict]:
        sql = cards.select(and_(cards.c.version <= version, cards.c.cardId == card_id))

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()