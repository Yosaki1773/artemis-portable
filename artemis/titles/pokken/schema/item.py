from typing import Optional

from core.data.schema import BaseData, metadata
from sqlalchemy import Column, Table, UniqueConstraint
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Integer

item = Table(
    "pokken_item",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
        unique=True,
    ),
    Column("category", Integer),
    Column("content", Integer),
    Column("type", Integer),
    UniqueConstraint("user", "category", "content", "type", name="pokken_item_uk"),
    mysql_charset="utf8mb4",
)


class PokkenItemData(BaseData):
    """
    Items obtained as rewards
    """

    async def add_reward(
        self, user_id: int, category: int, content: int, item_type: int
    ) -> Optional[int]:
        sql = insert(item).values(
            user=user_id,
            category=category,
            content=content,
            type=item_type,
        )

        conflict = sql.on_duplicate_key_update(
            content=content,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"Failed to insert reward for user {user_id}: {category}-{content}-{item_type}"
            )
            return None
        return result.lastrowid
