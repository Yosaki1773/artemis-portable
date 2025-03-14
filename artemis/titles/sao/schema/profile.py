from typing import Optional, Tuple, List
from sqlalchemy import Table, Column, UniqueConstraint, PrimaryKeyConstraint, and_, case
from sqlalchemy.types import Integer, String, BOOLEAN, INTEGER, BIGINT, VARCHAR, TIMESTAMP
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.engine import Row
from sqlalchemy.dialects.mysql import insert

from core.data.schema import BaseData, metadata

profile = Table(
    "sao_profile",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
        unique=True,
    ),
    Column("user_type", Integer, server_default="1"),
    Column("nick_name", String(16), server_default="PLAYER"),
    Column("rank_num", Integer, server_default="1"),
    Column("rank_exp", Integer, server_default="0"),
    Column("own_col", Integer, server_default="0"),
    Column("own_vp", Integer, server_default="0"),
    Column("own_yui_medal", Integer, server_default="0"),
    Column("setting_title_id", Integer, server_default="20005"),
    Column("my_shop", INTEGER),
    Column("fav_hero", INTEGER, ForeignKey("sao_hero_log_data.id", ondelete="set null", onupdate="cascade")),
    Column("when_register", TIMESTAMP, server_default=func.now()),
    Column("last_login_date", TIMESTAMP),
    Column("last_yui_medal_date", TIMESTAMP),
    Column("last_bonus_yui_medal_date", TIMESTAMP),
    Column("last_comeback_date", TIMESTAMP),
    Column("last_login_bonus_date", TIMESTAMP),
    Column("ad_confirm_date", TIMESTAMP),
    Column("login_ct", INTEGER, server_default="0"),
    mysql_charset="utf8mb4"
)

beginner_mission = Table(
    "sao_player_beginner_mission",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False, unique=True),
    Column("beginner_mission_id", INTEGER, nullable=False),
    Column("condition_id", INTEGER, nullable=False),
    Column("is_seat", BOOLEAN, nullable=False, server_default="0"),
    Column("achievement_num", INTEGER, nullable=False),
    Column("complete_flag", BOOLEAN, nullable=False, server_default="0"),
    Column("complete_date", TIMESTAMP),
    Column("reward_received_flag", BOOLEAN, nullable=False, server_default="0"),
    Column("reward_received_date", TIMESTAMP),
    UniqueConstraint("user", "condition_id", name="sao_player_beginner_mission_uk"),
    mysql_charset="utf8mb4"
)

resource_card = Table(
    "sao_player_resource_card",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("common_reward_type", INTEGER, nullable=False),
    Column("common_reward_id", INTEGER, nullable=False),
    Column("holographic_flag", BOOLEAN, nullable=False, server_default="0"),
    Column("serial", VARCHAR(20), unique=True),
    mysql_charset="utf8mb4"
)

hero_card = Table(
    "sao_player_hero_card",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("user_hero_id", INTEGER, ForeignKey("sao_hero_log_data.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("holographic_flag", BOOLEAN, nullable=False, server_default="0"),
    Column("serial", VARCHAR(20), unique=True),
    mysql_charset="utf8mb4"
)

tutorial = Table(
    "sao_player_tutorial",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("tutorial_byte", INTEGER, nullable=False),
    UniqueConstraint("user", "tutorial_byte", name="sao_player_tutorial_uk"),
    mysql_charset="utf8mb4"
)

class SaoProfileData(BaseData):
    async def create_profile(self, user_id: int) -> Optional[int]:
        sql = insert(profile).values(user=user_id)
        conflict = sql.on_duplicate_key_update(user=user_id)

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error("Failed to create SAO profile!")
    
    async def set_my_shop(self, user_id: int, store_id: int):
        result = await self.execute(profile.update(profile.c.user == user_id).values(my_shop = store_id))
        if result is None:
            self.logger.error(f"Failed to set my shop for user {user_id} to {store_id}!")
    
    async def user_login(self, user_id: int) -> Optional[Row]:
        sql = profile.update(profile.c.user == user_id).values(
            login_ct=profile.c.login_ct + 1,
            last_login_date=func.now()
        )
        result = await self.execute(sql)
        if result:
            return result.last_updated_params()
        self.logger.error(f"Failed to create log in user {user_id}!")
    
    async def update_yui_medal_date(self, user_id: int) -> None:
        sql = profile.update(profile.c.user == user_id).values(
            last_yui_medal_date=func.now()
        )
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update user {user_id} yui medal date!")

    async def add_yui_medals(self, user_id: int, num_medals: int = 1):
        sql = profile.update(profile.c.user == user_id).values(
            own_yui_medal=profile.c.own_yui_medal + num_medals
        )
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to give user {user_id} {num_medals} yui medals!")
    
    async def add_col(self, user_id: int, num_col: int) -> None:
        sql = profile.update(profile.c.user == user_id).values(
            own_col=profile.c.own_col + num_col
        )
        result = await self.execute(sql)
        if not result:
            self.logger.error(f"Failed to give user {user_id} {num_col} Col!")

    async def add_vp(self, user_id: int, num_vp: int) -> None:
        sql = profile.update(profile.c.user == user_id).values(
            own_vp=profile.c.own_vp + num_vp
        )
        result = await self.execute(sql)
        if not result:
            self.logger.error(f"Failed to give user {user_id} {num_vp} VP!")

    async def add_exp(self, user_id: int, xp_ammount: int) -> Optional[int]:
        sql = profile.update(profile.c.user == user_id).values(
            rank_exp=profile.c.rank_exp + xp_ammount
        )
        result = await self.execute(sql)
        if not result:
            self.logger.error(f"Failed to give user {user_id} {xp_ammount} xp!")
    
    async def get_exp(self, user_id: int) -> Optional[int]:
        result = await self.execute(select(profile.c.rank_exp).where(profile.c.user==user_id))
        if result:
            row = result.fetchone()
            if row:
                return row['rank_exp']
            return 0
        self.logger.error(f"Failed to query rank xp for user {user_id}")

    async def set_level(self, user_id: int, level: int):
        sql = profile.update(profile.c.user == user_id).values(
            rank_num=level
        )
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to set user {user_id} level to {level}!")

    async def put_profile(self, user_id: int, user_type: int, nick_name: str, rank_num: int, rank_exp: int, own_col: int, own_vp: int, own_yui_medal: int, setting_title_id: int) -> Optional[int]:
        sql = insert(profile).values(
            user=user_id,
            user_type=user_type,
            nick_name=nick_name,
            rank_num=rank_num,
            rank_exp=rank_exp,
            own_col=own_col,
            own_vp=own_vp,
            own_yui_medal=own_yui_medal,
            setting_title_id=setting_title_id
        )

        conflict = sql.on_duplicate_key_update(
            rank_num=rank_num,
            rank_exp=rank_exp,
            own_col=own_col,
            own_vp=own_vp,
            own_yui_medal=own_yui_medal,
            setting_title_id=setting_title_id
        )

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert profile! user: {user_id}")

    async def get_profile(self, user_id: int) -> Optional[Row]:
        sql = profile.select(profile.c.user == user_id)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
    
    async def set_profile_name(self, user_id: int, new_name: str) -> None:
        sql = profile.update(profile.c.user == user_id).values(
            nick_name=new_name
        )
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update nickname {new_name} for user {user_id}")

    async def add_tutorial_byte(self, user_id: int, tutorial_byte: int) -> None:
        sql = insert(tutorial).values(
            user = user_id,
            tutorial_byte = tutorial_byte
        )

        conflict = sql.on_duplicate_key_update(tutorial_byte = tutorial_byte)
        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"Failed to add tutorial byte {tutorial_byte} to user {user_id}")

    async def get_tutorial_bytes(self, user_id: int) -> Optional[List[Row]]:
        sql = tutorial.select(tutorial.c.user == user_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()
    
    async def put_hero_card(self, user_id: int, serial: str, user_hero_id: int, is_holo: bool) -> Optional[int]:
        sql = insert(hero_card).values(
            user=user_id,
            user_hero_id=user_hero_id,
            holographic_flag=is_holo,
            serial=serial
        )

        conflict = sql.on_duplicate_key_update(
            holographic_flag=is_holo,
            serial=serial
        )
        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert card {serial} for user {user_id} as hero {user_hero_id}")

    async def get_hero_card(self, serial: str) -> Optional[Row]:
        result = await self.execute(hero_card.select(hero_card.c.serial == serial))
        if result is None:
            return None
        return result.fetchone()

    async def put_resource_card(self, user_id: int, serial: str, reward_type: int, reward_id: int, is_holo: bool) -> Optional[int]:
        sql = insert(resource_card).values(
            user=user_id,
            common_reward_type=reward_type,
            common_reward_id=reward_id,
            holographic_flag=is_holo,
            serial=serial
        )

        conflict = sql.on_duplicate_key_update(
            holographic_flag=is_holo,
            serial=serial
        )
        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert card {serial} for user {user_id} as resource {reward_id}")

    async def get_resource_card(self, serial: str) -> Optional[int]:
        result = await self.execute(resource_card.select(resource_card.c.serial == serial))
        if result is None:
            return None
        return result.fetchone()

    async def update_beginner_mission_date(self, user_id: int) -> None:
        sql = profile.update(profile.c.user == user_id).values(
            ad_confirm_date=func.now()
        )
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update user {user_id} yui medal date!")

    async def put_beginner_mission(self, user_id: int, beginner_mission_id: int, condition_id: int, is_seat: bool, achievement_num: int) -> Optional[int]:
        pass

    async def complete_beginner_mission(self, user_id: int, condition_id: int) -> None:
        pass

    async def reward_beginner_mission(self, user_id: int, condition_id: int) -> None:
        pass

    async def get_beginner_missions(self, user_id: int) -> Optional[List[Row]]:
        pass

    async def get_beginner_missions_by_mission_id(self, user_id: int, beginner_mission_id: int) -> Optional[List[Row]]:
        pass

    async def get_beginner_mission(self, user_id: int, condition_id: int) -> Optional[Row]:
        pass

    async def set_title(self, user_id: int, title_id: int) -> None:
        result = await self.execute(profile.update(profile.c.user == user_id).values(setting_title_id=title_id))
        if not result:
            self.logger.error(f"Failed to set user {user_id} title to {title_id}")
