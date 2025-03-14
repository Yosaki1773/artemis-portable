from typing import Dict, List, Optional

from sqlalchemy import Column, Table, UniqueConstraint
from sqlalchemy.engine import Row
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.types import BIGINT, TIMESTAMP, VARCHAR, Boolean, Integer, String

from core.data.schema.base import BaseData, metadata

aime_card: Table = Table(
    "aime_card",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("user", ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("access_code", String(20), nullable=False, unique=True),
    Column("idm", String(16), unique=True),
    Column("chip_id", BIGINT, unique=True),
    Column("created_date", TIMESTAMP, server_default=func.now()),
    Column("last_login_date", TIMESTAMP, onupdate=func.now()),
    Column("is_locked", Boolean, server_default="0"),
    Column("is_banned", Boolean, server_default="0"),
    Column("memo", VARCHAR(16)),
    UniqueConstraint("user", "access_code", name="aime_card_uk"),
    mysql_charset="utf8mb4",
)


class CardData(BaseData):
    moble_os_codes = set([0x06, 0x07, 0x10, 0x12, 0x13, 0x14, 0x15, 0x17, 0x18])
    card_os_codes  = set([0x20, 0xF0, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7])

    async def get_card_by_access_code(self, access_code: str) -> Optional[Row]:
        sql = aime_card.select(aime_card.c.access_code == access_code)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_card_by_id(self, card_id: int) -> Optional[Row]:
        sql = aime_card.select(aime_card.c.id == card_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def update_access_code(self, old_ac: str, new_ac: str) -> None:
        sql = aime_card.update(aime_card.c.access_code == old_ac).values(
            access_code=new_ac
        )

        result = await self.execute(sql)
        if result is None:
            self.logger.error(
                f"Failed to change card access code from {old_ac} to {new_ac}"
            )

    async def get_user_id_from_card(self, access_code: str) -> Optional[int]:
        """
        Given a 20 digit access code as a string, get the user id associated with that card
        """
        card = await self.get_card_by_access_code(access_code)
        if card is None:
            return None

        return int(card["user"])

    async def get_card_banned(self, access_code: str) -> Optional[bool]:
        """
        Given a 20 digit access code as a string, check if the card is banned
        """
        card = await self.get_card_by_access_code(access_code)
        if card is None:
            return None
        if card["is_banned"]:
            return True
        return False
    
    async def get_card_locked(self, access_code: str) -> Optional[bool]:
        """
        Given a 20 digit access code as a string, check if the card is locked
        """
        card = await self.get_card_by_access_code(access_code)
        if card is None:
            return None
        if card["is_locked"]:
            return True
        return False

    async def delete_card(self, card_id: int) -> None:
        sql = aime_card.delete(aime_card.c.id == card_id)

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to delete card with id {card_id}")

    async def get_user_cards(self, aime_id: int) -> Optional[List[Row]]:
        """
        Returns all cards owned by a user
        """
        sql = aime_card.select(aime_card.c.user == aime_id)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def create_card(self, user_id: int, access_code: str) -> Optional[int]:
        """
        Given a aime_user id and a 20 digit access code as a string, create a card and return the ID if successful
        """
        sql = aime_card.insert().values(user=user_id, access_code=access_code)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def update_card_last_login(self, access_code: str) -> None:
        sql = aime_card.update(aime_card.c.access_code == access_code).values(
            last_login_date=func.now()
        )
        
        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f"Failed to update last login time for {access_code}")

    async def get_card_by_idm(self, idm: str) -> Optional[Row]:
        result = await self.execute(aime_card.select(aime_card.c.idm == idm))
        if result:
            return result.fetchone()

    async def get_card_by_chip_id(self, chip_id: int) -> Optional[Row]:
        result = await self.execute(aime_card.select(aime_card.c.chip_id == chip_id))
        if result:
            return result.fetchone()

    async def set_chip_id_by_access_code(self, access_code: str, chip_id: int) -> Optional[Row]:
        result = await self.execute(aime_card.update(aime_card.c.access_code == access_code).values(chip_id=chip_id))
        if not result:
            self.logger.error(f"Failed to update chip ID to {chip_id} for {access_code}")

    async def set_idm_by_access_code(self, access_code: str, idm: str) -> Optional[Row]:
        result = await self.execute(aime_card.update(aime_card.c.access_code == access_code).values(idm=idm))
        if not result:
            self.logger.error(f"Failed to update IDm to {idm} for {access_code}")

    async def set_access_code_by_access_code(self, old_ac: str, new_ac: str) -> None:
        result = await self.execute(aime_card.update(aime_card.c.access_code == old_ac).values(access_code=new_ac))
        if not result:
            self.logger.error(f"Failed to change card access code from {old_ac} to {new_ac}")

    async def set_memo_by_access_code(self, access_code: str, memo: str) -> None:
        result = await self.execute(aime_card.update(aime_card.c.access_code == access_code).values(memo=memo))
        if not result:
            self.logger.error(f"Failed to add memo to card {access_code}")

    def to_access_code(self, luid: str) -> str:
        """
        Given a felica cards internal 16 hex character luid, convert it to a 0-padded 20 digit access code as a string
        """
        return f"{int(luid, base=16):0{20}}"

    def to_idm(self, access_code: str) -> str:
        """
        Given a 20 digit access code as a string, return the 16 hex character luid
        """
        return f"{int(access_code):0{16}X}"
