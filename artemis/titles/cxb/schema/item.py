from typing import Dict, Optional

from core.data.schema import BaseData, metadata
from sqlalchemy import Column, Table, UniqueConstraint, and_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Integer

energy = Table(
    "cxb_rev_energy",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("user", ForeignKey("aime_user.id", ondelete="cascade"), nullable=False),
    Column("energy", Integer, nullable=False, server_default="0"),
    UniqueConstraint("user", name="cxb_rev_energy_uk"),
    mysql_charset="utf8mb4",
)


class CxbItemData(BaseData):
    async def put_energy(self, user_id: int, rev_energy: int) -> Optional[int]:
        sql = insert(energy).values(user=user_id, energy=rev_energy)

        conflict = sql.on_duplicate_key_update(energy=rev_energy)

        result = await self.execute(conflict)
        if result is None:
            self.logger.error(
                f"{__name__} failed to insert item! user: {user_id}, energy: {rev_energy}"
            )
            return None

        return result.lastrowid

    async def get_energy(self, user_id: int) -> Optional[Dict]:
        sql = energy.select(and_(energy.c.user == user_id))

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
