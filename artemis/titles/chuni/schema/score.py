from typing import Dict, List, Optional

from sqlalchemy import Column, Table, UniqueConstraint
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.types import Boolean, Integer, String

from core.data.schema import BaseData, metadata

from ..config import ChuniConfig

course: Table = Table(
    "chuni_score_course",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("courseId", Integer),
    Column("classId", Integer),
    Column("playCount", Integer),
    Column("scoreMax", Integer),
    Column("isFullCombo", Boolean),
    Column("isAllJustice", Boolean),
    Column("isSuccess", Integer),
    Column("scoreRank", Integer),
    Column("eventId", Integer),
    Column("lastPlayDate", String(25)),
    Column("param1", Integer),
    Column("param2", Integer),
    Column("param3", Integer),
    Column("param4", Integer),
    Column("isClear", Integer),
    Column("theoryCount", Integer),
    Column("orderId", Integer),
    Column("playerRating", Integer),
    UniqueConstraint("user", "courseId", name="chuni_score_course_uk"),
    mysql_charset="utf8mb4",
)

best_score: Table = Table(
    "chuni_score_best",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("playCount", Integer),
    Column("scoreMax", Integer),
    Column("resRequestCount", Integer),
    Column("resAcceptCount", Integer),
    Column("resSuccessCount", Integer),
    Column("missCount", Integer),
    Column("maxComboCount", Integer),
    Column("isFullCombo", Boolean),
    Column("isAllJustice", Boolean),
    Column("isSuccess", Integer),
    Column("fullChain", Integer),
    Column("maxChain", Integer),
    Column("scoreRank", Integer),
    Column("isLock", Boolean),
    Column("ext1", Integer),
    Column("theoryCount", Integer),
    UniqueConstraint("user", "musicId", "level", name="chuni_score_best_uk"),
    mysql_charset="utf8mb4",
)

playlog = Table(
    "chuni_score_playlog",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("orderId", Integer),
    Column("sortNumber", Integer),
    Column("placeId", Integer),
    Column("playDate", String(20)),
    Column("userPlayDate", String(20)),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("customId", Integer),
    Column("playedUserId1", Integer),
    Column("playedUserId2", Integer),
    Column("playedUserId3", Integer),
    Column("playedUserName1", String(20)),
    Column("playedUserName2", String(20)),
    Column("playedUserName3", String(20)),
    Column("playedMusicLevel1", Integer),
    Column("playedMusicLevel2", Integer),
    Column("playedMusicLevel3", Integer),
    Column("playedCustom1", Integer),
    Column("playedCustom2", Integer),
    Column("playedCustom3", Integer),
    Column("track", Integer),
    Column("score", Integer),
    Column("rank", Integer),
    Column("maxCombo", Integer),
    Column("maxChain", Integer),
    Column("rateTap", Integer),
    Column("rateHold", Integer),
    Column("rateSlide", Integer),
    Column("rateAir", Integer),
    Column("rateFlick", Integer),
    Column("judgeGuilty", Integer),
    Column("judgeAttack", Integer),
    Column("judgeJustice", Integer),
    Column("judgeCritical", Integer),
    Column("eventId", Integer),
    Column("playerRating", Integer),
    Column("isNewRecord", Boolean),
    Column("isFullCombo", Boolean),
    Column("fullChainKind", Integer),
    Column("isAllJustice", Boolean),
    Column("isContinue", Boolean),
    Column("isFreeToPlay", Boolean),
    Column("characterId", Integer),
    Column("skillId", Integer),
    Column("playKind", Integer),
    Column("isClear", Integer),
    Column("skillLevel", Integer),
    Column("skillEffect", Integer),
    Column("placeName", String(255)),
    Column("isMaimai", Boolean),
    Column("commonId", Integer),
    Column("charaIllustId", Integer),
    Column("romVersion", String(255)),
    Column("judgeHeaven", Integer),
    Column("regionId", Integer),
    Column("machineType", Integer),
    Column("ticketId", Integer),
    mysql_charset="utf8mb4"
)

class ChuniRomVersion():
    """
    Class used to easily compare rom version strings and map back to the internal integer version.
    Used with methods that touch the playlog table.
    """
    Versions = {}
    def init_versions(cfg: ChuniConfig):
        if len(ChuniRomVersion.Versions) > 0:
            # dont bother with reinit
            return

        # Build up a easily comparible list of versions. Used when deriving romVersion from the playlog
        all_versions = {
            10: ChuniRomVersion("1.50.0"),
            9: ChuniRomVersion("1.45.0"),
            8: ChuniRomVersion("1.40.0"),
            7: ChuniRomVersion("1.35.0"),
            6: ChuniRomVersion("1.30.0"),
            5: ChuniRomVersion("1.25.0"),
            4: ChuniRomVersion("1.20.0"),
            3: ChuniRomVersion("1.15.0"),
            2: ChuniRomVersion("1.10.0"),
            1: ChuniRomVersion("1.05.0"),
            0: ChuniRomVersion("1.00.0")
        }

        # add the versions from the config
        for ver in range(11,999):
            cfg_ver = cfg.version.version(ver)
            if cfg_ver:
                all_versions[ver] = ChuniRomVersion(cfg_ver["rom"])
            else:
                break

        # sort it by version number for easy iteration
        ChuniRomVersion.Versions = dict(sorted(all_versions.items()))

    def __init__(self, rom_version: Optional[str] = None) -> None:
        if rom_version is None:
            self.major = 0
            self.minor = 0
            self.maint = 0
            self.version = "0.00.00"
            return
        
        (major, minor, maint) = rom_version.split('.')
        self.major = int(major)
        self.minor = int(minor)
        self.maint = int(maint)
        self.version = rom_version

    def __str__(self) -> str:
        return self.version

    def __eq__(self, other) -> bool:
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.maint == other.maint)

    def __lt__(self, other) -> bool:
        return (self.major < other.major) or \
               (self.major == other.major and self.minor < other.minor) or \
               (self.major == other.major and self.minor == other.minor and self.maint < other.maint)

    def __gt__(self, other) -> bool:
        return (self.major > other.major) or \
               (self.major == other.major and self.minor > other.minor) or \
               (self.major == other.major and self.minor == other.minor and self.maint > other.maint)

    def get_int_version(self) -> int:
        """
        Used when displaying the playlog to walk backwards from the recorded romVersion to our internal version number.
        This is effectively a workaround to avoid recording our internal version number along with the romVersion in the db at insert time.
        """
        for ver,rom in ChuniRomVersion.Versions.items():
            # if the version matches exactly, great!
            if self == rom:
                return ver
            
            # If this isnt the last version, use the next as an upper bound
            if ver + 1 < len(ChuniRomVersion.Versions):
                if self > rom and self < ChuniRomVersion.Versions[ver + 1]:
                    # this version fits in the middle! It must be a revision of the version
                    # e.g. 2.15.00 vs 2.16.00
                    return ver
            else:
                # this is the last version in the list.
                # If its greate than this one and still the same major, this call it a match
                if self.major == rom.major and self > rom:
                    return ver

        # Only way we get here is if it was a version that started with "0." which is def invalid
        return -1

class ChuniScoreData(BaseData):
    async def get_courses(
        self,
        aime_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(course).where(course.c.user == aime_id)

        if limit is not None or offset is not None:
            sql = sql.order_by(course.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_course(self, aime_id: int, course_data: Dict) -> Optional[int]:
        course_data["user"] = aime_id
        course_data = self.fix_bools(course_data)

        sql = insert(course).values(**course_data)
        conflict = sql.on_duplicate_key_update(**course_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_scores(
        self,
        aime_id: int,
        levels: Optional[list[int]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        condition = best_score.c.user == aime_id

        if levels is not None:
            condition &= best_score.c.level.in_(levels)

        if limit is None and offset is None:
            sql = (
                select(best_score)
                .where(condition)
                .order_by(best_score.c.musicId.asc(), best_score.c.level.asc())
            )
        else:
            subq = (
                select(best_score.c.musicId)
                .distinct()
                .where(condition)
                .order_by(best_score.c.musicId)
            )

            if limit is not None:
                subq = subq.limit(limit)
            if offset is not None:
                subq = subq.offset(offset)
            
            subq = subq.subquery()

            sql = (
                select(best_score)
                .join(subq, best_score.c.musicId == subq.c.musicId)
                .where(condition)
                .order_by(best_score.c.musicId, best_score.c.level)
            )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_score(self, aime_id: int, score_data: Dict) -> Optional[int]:
        score_data["user"] = aime_id
        score_data = self.fix_bools(score_data)

        sql = insert(best_score).values(**score_data)
        conflict = sql.on_duplicate_key_update(**score_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_playlogs(self, aime_id: int) -> Optional[Row]:
        sql = select(playlog).where(playlog.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_playlog_rom_versions_by_int_version(self, version: int, aime_id: int = -1) -> Optional[str]:
        # Get a set of all romVersion values present
        sql = select([playlog.c.romVersion])
        if aime_id != -1:
            # limit results to a specific user
            sql = sql.where(playlog.c.user == aime_id)
        sql = sql.distinct()

        result = await self.execute(sql)
        if result is None:
            return None
        record_versions = result.fetchall()

        # for each romVersion recorded, check if it maps back the current version we are operating on
        matching_rom_versions = []
        for v in record_versions:
            # Do this to prevent null romVersion from causing an error in ChuniRomVersion.__init__()
            if v[0] is None:
                continue
            
            if ChuniRomVersion(v[0]).get_int_version() == version:
                matching_rom_versions += [v[0]]

        self.logger.debug(f"romVersions {matching_rom_versions} map to version {version}")
        return matching_rom_versions

    async def get_playlogs_limited(self, aime_id: int, version: int, index: int, count: int) -> Optional[Row]:
        # Get a list of all the recorded romVersions in the playlog 
        # for this user that map to the given version.
        rom_versions = await self.get_playlog_rom_versions_by_int_version(version, aime_id)
        if rom_versions is None:
            return None

        # Query results that have the matching romVersions
        sql = select(playlog).where((playlog.c.user == aime_id) & (playlog.c.romVersion.in_(rom_versions))).order_by(playlog.c.id.desc()).limit(count).offset(index * count)

        result = await self.execute(sql)
        if result is None:
            self.logger.info(f" aime_id {aime_id} has no playlog for version {version}")
            return None
        return result.fetchall()

    async def get_user_playlogs_count(self, aime_id: int, version: int) -> Optional[Row]:
        # Get a list of all the recorded romVersions in the playlog 
        # for this user that map to the given version.
        rom_versions = await self.get_playlog_rom_versions_by_int_version(version, aime_id)
        if rom_versions is None:
            return None

        # Query results that have the matching romVersions
        sql = select(func.count()).where((playlog.c.user == aime_id) & (playlog.c.romVersion.in_(rom_versions)))

        result = await self.execute(sql)
        if result is None:
            self.logger.info(f" aime_id {aime_id} has no playlog for version {version}")
            return 0
        return result.scalar()

    async def put_playlog(self, aime_id: int, playlog_data: Dict, version: int) -> Optional[int]:
        playlog_data["user"] = aime_id
        playlog_data = self.fix_bools(playlog_data)
        # If the romVersion is not in the data (Version 10 and earlier), look it up from our internal mapping
        if "romVersion" not in playlog_data:
            playlog_data["romVersion"] = ChuniRomVersion.Versions[version]

        sql = insert(playlog).values(**playlog_data)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def get_rankings(self, version: int) -> Optional[List[Dict]]:
        # Get a list of all the recorded romVersions in the playlog for the given version
        rom_versions = await self.get_playlog_rom_versions_by_int_version(version)
        if rom_versions is None:
            return None

        # Query results that have the matching romVersions
        sql = select([playlog.c.musicId.label('id'), func.count(playlog.c.musicId).label('point')]).where((playlog.c.level != 4) & (playlog.c.romVersion.in_(rom_versions))).group_by(playlog.c.musicId).order_by(func.count(playlog.c.musicId).desc()).limit(10)
        result = await self.execute(sql)

        if result is None:
            return None

        rows = result.fetchall()
        return [dict(row) for row in rows]
