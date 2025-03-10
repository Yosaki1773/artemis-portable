from typing import Dict, List, Optional

from core.data.schema import BaseData, metadata
from sqlalchemy import Column, Table, UniqueConstraint, and_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import JSON, Integer

profile = Table(
    "cxb_profile",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("user", ForeignKey("aime_user.id", ondelete="cascade"), nullable=False),
    Column("version", Integer, nullable=False),
    Column("index", Integer, nullable=False),
    Column("data", JSON, nullable=False),
    UniqueConstraint("user", "index", name="cxb_profile_uk"),
    mysql_charset="utf8mb4",
)


class CxbProfileData(BaseData):
    async def put_profile(
        self, user_id: int, version: int, index: int, data: JSON
    ) -> Optional[int]:
        sql = insert(profile).values(
            user=user_id, version=version, index=index, data=data
        )

        conflict = sql.on_duplicate_key_update(index=index, data=data)

        result = await self.execute(conflict)
        if result is None:
            self.logger.error(
                f"{__name__} failed to update! user: {user_id}, index: {index}, data: {data}"
            )
            return None

        return result.lastrowid

    async def get_profile(self, aime_id: int, version: int) -> Optional[List[Dict]]:
        """
        Given a game version and either a profile or aime id, return the profile
        """
        sql = profile.select(
            and_(profile.c.version == version, profile.c.user == aime_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_profile_index(
        self, index: int, aime_id: int = None, version: int = None
    ) -> Optional[Dict]:
        """
        Given a game version and either a profile or aime id, return the profile
        """
        if aime_id is not None and version is not None and index is not None:
            sql = profile.select(
                and_(
                    profile.c.version == version,
                    profile.c.user == aime_id,
                    profile.c.index == index,
                )
            )
        else:
            self.logger.error(
                f"get_profile: Bad arguments!! aime_id {aime_id} version {version}"
            )
            return None

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
