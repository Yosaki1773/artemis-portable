from typing import Optional, Dict, List
from sqlalchemy import Table, Column, UniqueConstraint, PrimaryKeyConstraint, and_, case
from sqlalchemy.types import Integer, String, TIMESTAMP, Boolean, JSON, BOOLEAN, INTEGER, BIGINT
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select, update, delete
from sqlalchemy.engine import Row
from sqlalchemy.dialects.mysql import insert

from core.data.schema import BaseData, metadata

equipment_data = Table(
    "sao_equipment_data",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("equipment_id", BIGINT, ForeignKey("sao_static_equipment_list.EquipmentId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("enhancement_value", Integer, nullable=False),
    Column("enhancement_exp", Integer, nullable=False),
    Column("awakening_exp", Integer, nullable=False),
    Column("awakening_stage", Integer, nullable=False),
    Column("possible_awakening_flag", Integer, nullable=False),
    Column("is_shop_purchase", BOOLEAN, nullable=False, server_default="0"),
    Column("is_protect", BOOLEAN, nullable=False, server_default="0"),
    Column("property1_property_id", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False, server_default="2"),
    Column("property1_value1", INTEGER, nullable=False, server_default="0"),
    Column("property1_value2", INTEGER, nullable=False, server_default="0"),
    Column("property2_property_id", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False, server_default="2"),
    Column("property2_value1", INTEGER, nullable=False, server_default="0"),
    Column("property2_value2", INTEGER, nullable=False, server_default="0"),
    Column("property3_property_id", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False, server_default="2"),
    Column("property3_value1", INTEGER, nullable=False, server_default="0"),
    Column("property3_value2", INTEGER, nullable=False, server_default="0"),
    Column("property4_property_id", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False, server_default="2"),
    Column("property4_value1", INTEGER, nullable=False, server_default="0"),
    Column("property4_value2", INTEGER, nullable=False, server_default="0"),
    Column("converted_card_num", INTEGER, nullable=False, server_default="0"),
    Column("get_date", TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("user", "equipment_id", name="sao_equipment_data_uk"),
    mysql_charset="utf8mb4"
)

item_data = Table(
    "sao_item_data",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("item_id", Integer, nullable=False),
    Column("get_date", TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("user", "item_id", name="sao_item_data_uk"),
    mysql_charset="utf8mb4"
)

hero_log_data = Table(
    "sao_hero_log_data",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("hero_log_id", BIGINT, ForeignKey("sao_static_hero_list.HeroLogId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("log_level", Integer, nullable=False),
    Column("log_exp", Integer, nullable=False),
    Column("main_weapon", INTEGER, ForeignKey("sao_equipment_data.id", ondelete="set null", onupdate="set null")),
    Column("sub_equipment", INTEGER, ForeignKey("sao_equipment_data.id", ondelete="set null", onupdate="set null")),
    Column("skill_slot1_skill_id", BIGINT, ForeignKey("sao_static_skill.SkillId", ondelete="set null", onupdate="set null")),
    Column("skill_slot2_skill_id", BIGINT, ForeignKey("sao_static_skill.SkillId", ondelete="set null", onupdate="set null")),
    Column("skill_slot3_skill_id", BIGINT, ForeignKey("sao_static_skill.SkillId", ondelete="set null", onupdate="set null")),
    Column("skill_slot4_skill_id", BIGINT, ForeignKey("sao_static_skill.SkillId", ondelete="set null", onupdate="set null")),
    Column("skill_slot5_skill_id", BIGINT, ForeignKey("sao_static_skill.SkillId", ondelete="set null", onupdate="set null")),
    Column("max_level_extend_num", INTEGER, nullable=False, server_default="0"),
    Column("is_awakenable", BOOLEAN, nullable=False, server_default="0"),
    Column("awakening_stage", INTEGER, nullable=False, server_default="0"),
    Column("awakening_exp", INTEGER, nullable=False, server_default="0"),
    Column("is_shop_purchase", BOOLEAN, nullable=False, server_default="0"),
    Column("is_protect", BOOLEAN, nullable=False, server_default="0"),
    Column("property1_property_id", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False, server_default="2"),
    Column("property1_value1", INTEGER, nullable=False, server_default="0"),
    Column("property1_value2", INTEGER, nullable=False, server_default="0"),
    Column("property2_property_id", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False, server_default="2"),
    Column("property2_value1", INTEGER, nullable=False, server_default="0"),
    Column("property2_value2", INTEGER, nullable=False, server_default="0"),
    Column("property3_property_id", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False, server_default="2"),
    Column("property3_value1", INTEGER, nullable=False, server_default="0"),
    Column("property3_value2", INTEGER, nullable=False, server_default="0"),
    Column("property4_property_id", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False, server_default="2"),
    Column("property4_value1", INTEGER, nullable=False, server_default="0"),
    Column("property4_value2", INTEGER, nullable=False, server_default="0"),
    Column("converted_card_num", INTEGER, nullable=False, server_default="0"),
    Column("get_date", TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("user", "hero_log_id", name="sao_hero_log_data_uk"),
    mysql_charset="utf8mb4"
)

hero_party = Table(
    "sao_hero_party",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("user_party_team_id", Integer, nullable=False),
    Column("user_hero_log_id_1", Integer, ForeignKey("sao_hero_log_data.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("user_hero_log_id_2", Integer, ForeignKey("sao_hero_log_data.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("user_hero_log_id_3", Integer, ForeignKey("sao_hero_log_data.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    UniqueConstraint("user", "user_party_team_id", name="sao_hero_party_uk"),
    mysql_charset="utf8mb4"
)

quest = Table(
    "sao_player_quest",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("quest_type", INTEGER, nullable=False, server_default="1"),
    Column("quest_scene_id", BIGINT, ForeignKey("sao_static_quest.QuestSceneId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("quest_clear_flag", Boolean, nullable=False),
    Column("clear_time", Integer, nullable=False),
    Column("combo_num", Integer, nullable=False),
    Column("total_damage", Integer, nullable=False),
    Column("concurrent_destroying_num", Integer, nullable=False),
    Column("play_date", TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("user", "quest_scene_id", name="sao_player_quest_uk"),
    mysql_charset="utf8mb4"
)

ex_bonus = Table(
    "sao_player_ex_bonus",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("quest_scene_id", BIGINT, ForeignKey("sao_static_quest.QuestSceneId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("ex_bonus_table_id", BIGINT, ForeignKey("sao_static_ex_bonus.ExBonusTableId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("quest_clear_flag", BOOLEAN, nullable=False, server_default="0"),
    UniqueConstraint("user", "quest_scene_id", "ex_bonus_table_id", name="sao_player_ex_bonus_uk"),
    mysql_charset="utf8mb4"
)

sessions = Table(
    "sao_play_sessions",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("user_party_team_id", Integer, nullable=False),
    Column("episode_id", Integer, nullable=False), # TODO: Change to quest scene id
    Column("play_mode", Integer, nullable=False),
    Column("quest_drop_boost_apply_flag", Integer, nullable=False),
    Column("play_date", TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("user", "user_party_team_id", "play_date", name="sao_play_sessions_uk"),
    mysql_charset="utf8mb4"
)

end_sessions = Table(
    "sao_end_sessions",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("quest_id", Integer, nullable=False),
    Column("play_result_flag", Boolean, nullable=False),
    Column("reward_data", JSON, nullable=True),
    Column("play_date", TIMESTAMP, nullable=False, server_default=func.now()),
    mysql_charset="utf8mb4"
)

class SaoItemData(BaseData):
    async def create_session(self, user_id: int, user_party_team_id: int, episode_id: int, play_mode: int, quest_drop_boost_apply_flag: int) -> Optional[int]:
        sql = insert(sessions).values(
            user=user_id,
            user_party_team_id=user_party_team_id,
            episode_id=episode_id,
            play_mode=play_mode,
            quest_drop_boost_apply_flag=quest_drop_boost_apply_flag
            )

        conflict = sql.on_duplicate_key_update(
            user_party_team_id=user_party_team_id,
            episode_id=episode_id,
            play_mode=play_mode,
            quest_drop_boost_apply_flag=quest_drop_boost_apply_flag
        )

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to create SAO session for user {user_id}!")

    async def create_end_session(self, user_id: int, quest_id: int, play_result_flag: bool, reward_data: JSON) -> Optional[int]:
        sql = insert(end_sessions).values(
            user=user_id,
            quest_id=quest_id,
            play_result_flag=play_result_flag,
            reward_data=reward_data,
            )

        conflict = sql.on_duplicate_key_update(
            play_result_flag=play_result_flag,
            reward_data=reward_data
        )

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        
        self.logger.error(f"Failed to create SAO end session for user {user_id}!")

    async def put_item(self, user_id: int, item_id: int) -> Optional[int]:
        sql = insert(item_data).values(
            user=user_id,
            item_id=item_id,
        )

        conflict = sql.on_duplicate_key_update(item_id=item_id)

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert item! user: {user_id}, item_id: {item_id}")
    
    async def put_equipment(self, user_id: int, equipment_id: int) -> Optional[int]:
        sql = insert(equipment_data).values(
            user=user_id,
            equipment_id=equipment_id,
            enhancement_value=1,
            enhancement_exp=200,
            awakening_exp=0,
            awakening_stage=0,
            possible_awakening_flag=0,
        )

        conflict = sql.on_duplicate_key_update(equipment_id=equipment_id)

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert equipment! user: {user_id}, equipment_id: {equipment_id}")
    
    async def put_ex_bonus(self, user_id: int, quest_scene_id: int, ex_bonus_id: int, clear: bool = False) -> Optional[int]:
        sql = insert(ex_bonus).values(
            user=user_id,
            quest_scene_id=quest_scene_id,
            ex_bonus_table_id=ex_bonus_id,
            quest_clear_flag=clear,
        )

        conflict = sql.on_duplicate_key_update(quest_clear_flag=clear)
        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert ex bonus status! user: {user_id}, quest_scene_id: {quest_scene_id}, ex_bonus_id: {ex_bonus_id}, clear: {clear}")

    async def add_equipment_enhancement_exp(self, user_weapon_id: int, enhancement_exp: int) -> None:
        result = await self.execute(
            equipment_data.update(equipment_data.c.id == user_weapon_id)
            .values(enhancement_exp=equipment_data.c.enhancement_exp + enhancement_exp)
        )
        if not result:
            self.logger.error(f"Failed to give equipment {user_weapon_id} {enhancement_exp} xp!")

    async def get_equipment_enhancement_exp(self, user_weapon_id: int) -> Optional[int]:
        result = await self.execute(select(equipment_data.c.enhancement_exp).where(equipment_data.c.id==user_weapon_id))
        if result:
            row = result.fetchone()
            if row:
                return row['enhancement_exp']
            return 0
        self.logger.error(f"Failed to get equipment {user_weapon_id} xp!")
    
    async def set_equipment_enhancement_value(self, user_equip_id: int, enhancement_val: int) -> None:
        result = await self.execute(equipment_data.update(equipment_data.c.id == user_equip_id).values(enhancement_value=enhancement_val))
        if result is None:
            self.logger.error(f"Failed to set equipment {user_equip_id} level to {enhancement_val}!")
    
    async def add_hero_xp(self, user_hero_log_id: int, add_xp: int) -> Optional[int]:
        result = await self.execute(
            hero_log_data.update(hero_log_data.c.id == user_hero_log_id)
            .values(log_exp=hero_log_data.c.log_exp + add_xp)
        )
        if not result:
            self.logger.error(f"Failed to give hero {user_hero_log_id} {add_xp} xp!")

    async def get_hero_xp(self, user_hero_log_id: int) -> Optional[int]:
        result = await self.execute(select(hero_log_data.c.log_exp).where(hero_log_data.c.id==user_hero_log_id))
        if result:
            row = result.fetchone()
            if row:
                return row['log_exp']
            return 0
        self.logger.error(f"Failed to get hero xp for {user_hero_log_id}")

    async def set_hero_level(self, user_hero_log_id: int, new_level: int):
        result = await self.execute(hero_log_data.update(hero_log_data.c.id == user_hero_log_id).values(log_level=new_level))
        if result is None:
            self.logger.error(f"Failed to set hero {user_hero_log_id} level to {new_level}!")

    async def put_hero_log(self, user_id: int, user_hero_log_id: int, log_level: int, log_exp: int, main_weapon: int, sub_equipment: int, skill_slot1_skill_id: int, skill_slot2_skill_id: int, skill_slot3_skill_id: int, skill_slot4_skill_id: int, skill_slot5_skill_id: int) -> Optional[int]:
        sql = insert(hero_log_data).values(
            user=user_id,
            hero_log_id=user_hero_log_id,
            log_level=log_level,
            log_exp=log_exp,
            main_weapon=main_weapon,
            sub_equipment=sub_equipment,
            skill_slot1_skill_id=skill_slot1_skill_id,
            skill_slot2_skill_id=skill_slot2_skill_id,
            skill_slot3_skill_id=skill_slot3_skill_id,
            skill_slot4_skill_id=skill_slot4_skill_id,
            skill_slot5_skill_id=skill_slot5_skill_id,
        )

        conflict = sql.on_duplicate_key_update(
            log_level=log_level,
            log_exp=log_exp,
            main_weapon=main_weapon,
            sub_equipment=sub_equipment,
            skill_slot1_skill_id=skill_slot1_skill_id,
            skill_slot2_skill_id=skill_slot2_skill_id,
            skill_slot3_skill_id=skill_slot3_skill_id,
            skill_slot4_skill_id=skill_slot4_skill_id,
            skill_slot5_skill_id=skill_slot5_skill_id
        )

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert hero! user: {user_id}, user_hero_log_id: {user_hero_log_id}")
    
    async def set_user_hero_weapons(self, user_hero_id: int, main_weapon: int, sub_weapon: int) -> None:
        sql = hero_log_data.update(hero_log_data.c.id == user_hero_id).values(
            main_weapon=main_weapon,
            sub_equipment=sub_weapon,
        )
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update user hero {user_hero_id} weapons {main_weapon}/{sub_weapon}")
            return None

    async def set_user_hero_skills(self, user_hero_id: int, skill1: int, skill2: int, skill3: int, skill4: int, skill5: int) -> None:
        sql = hero_log_data.update(hero_log_data.c.id == user_hero_id).values(
            skill_slot1_skill_id = skill1,
            skill_slot2_skill_id = skill2,
            skill_slot3_skill_id = skill3,
            skill_slot4_skill_id = skill4,
            skill_slot5_skill_id = skill5,
        )
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update user hero {user_hero_id} skills {skill1}/{skill2}/{skill3}/{skill4}/{skill5}")
            return None

    async def put_hero_party(self, user_id: int, user_party_team_id: int, user_hero_log_id_1: int, user_hero_log_id_2: int, user_hero_log_id_3: int) -> Optional[int]:
        sql = insert(hero_party).values(
            user=user_id,
            user_party_team_id=user_party_team_id,
            user_hero_log_id_1=user_hero_log_id_1,
            user_hero_log_id_2=user_hero_log_id_2,
            user_hero_log_id_3=user_hero_log_id_3,
        )

        conflict = sql.on_duplicate_key_update(
            user_hero_log_id_1=user_hero_log_id_1,
            user_hero_log_id_2=user_hero_log_id_2,
            user_hero_log_id_3=user_hero_log_id_3
        )

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert hero party! user: {user_id}, user_party_team_id: {user_party_team_id}")

    async def put_player_quest(self, user_id: int, quest_type: int, quest_scene_id: int, quest_clear_flag: bool, clear_time: int, combo_num: int, total_damage: int, concurrent_destroying_num: int) -> Optional[int]:
        sql = insert(quest).values(
            user=user_id,
            quest_type=quest_type,
            quest_scene_id=quest_scene_id,
            quest_clear_flag=quest_clear_flag,
            clear_time=clear_time,
            combo_num=combo_num,
            total_damage=total_damage,
            concurrent_destroying_num=concurrent_destroying_num
        )

        conflict = sql.on_duplicate_key_update(
            quest_clear_flag=quest_clear_flag,
            clear_time=clear_time,
            combo_num=combo_num,
            total_damage=total_damage,
            concurrent_destroying_num=concurrent_destroying_num
        )

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert quest! user: {user_id}, quest_scene_id: {quest_scene_id}")

    async def get_user_equipment(self, user_id: int, equipment_id: int) -> Optional[Dict]:
        sql = equipment_data.select(equipment_data.c.user == user_id and equipment_data.c.equipment_id == equipment_id)
        
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
    
    async def get_user_equipment_by_id(self, equipment_user_id: int) -> Optional[Row]:
        sql = equipment_data.select(equipment_data.c.id == equipment_user_id)
        
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_user_equipments(
        self, user_id: int
    ) -> Optional[List[Row]]:
        """
        A catch-all equipments lookup given a profile
        """
        sql = equipment_data.select(
            and_(
                equipment_data.c.user == user_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_user_items(
        self, user_id: int
    ) -> Optional[List[Row]]:
        """
        A catch-all items lookup given a profile
        """
        sql = item_data.select(
            and_(
                item_data.c.user == user_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_player_ex_bonus_status(self, user_id: int) -> Optional[List[Row]]:
        sql = equipment_data.select(ex_bonus.c.user == user_id)
        
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_player_ex_bonus_by_quest(self, user_id: int, quest_scene_id) -> Optional[List[Row]]:
        sql = ex_bonus.select(and_(ex_bonus.c.user == user_id, ex_bonus.c.quest_scene_id == quest_scene_id))
        
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_user_item_by_id(
        self, user_item_id: int
    ) -> Optional[Row]:
        sql = item_data.select(item_data.c.id == user_item_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_user_hero_by_id(self, user_hero_id: int) -> Optional[Row]:
        result = await self.execute(hero_log_data.select(hero_log_data.c.id == user_hero_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_hero_log(
        self, user_id: int, user_hero_log_id: int = None
    ) -> Optional[List[Row]]:
        """
        A catch-all hero lookup given a profile and user_party_team_id and ID specifiers
        """
        sql = hero_log_data.select(
            and_(
                hero_log_data.c.user == user_id,
                hero_log_data.c.hero_log_id == user_hero_log_id if user_hero_log_id is not None else True,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
    
    async def get_hero_log_by_id(self, user_hero_log_id: int) -> Optional[Row]:
        result = await self.execute(hero_log_data.select(hero_log_data.c.id == user_hero_log_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_hero_logs(
        self, user_id: int
    ) -> Optional[List[Row]]:
        """
        A catch-all hero lookup given a profile
        """
        result = await self.execute(hero_log_data.select(hero_log_data.c.user == user_id))
        if result is None:
            return None
        return result.fetchall()

    async def get_hero_party_by_id(self, party_id: int) -> Optional[Row]:
        result = await self.execute(hero_party.select(hero_party.c.id == party_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_hero_party(
        self, user_id: int, user_party_team_id: int = None
    ) -> Optional[List[Row]]:
        sql = hero_party.select(
            and_(
                hero_party.c.user == user_id,
                hero_party.c.user_party_team_id == user_party_team_id if user_party_team_id is not None else True,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_quest_log(
        self, user_id: int, quest_scene_id: int
    ) -> Optional[Row]:
        """
        A catch-all quest lookup given a profile and quest_scene_id
        """
        sql = quest.select(
            and_(
                quest.c.user == user_id,
                quest.c.quest_scene_id == quest_scene_id
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_quest_logs(
        self, user_id: int
    ) -> Optional[List[Row]]:
        result = await self.execute(quest.select(quest.c.user == user_id))
        if result is None:
            return None
        return result.fetchall()

    async def get_session(
        self, user_id: int = None
    ) -> Optional[List[Row]]:
        sql = sessions.select(sessions.c.user == user_id).order_by(sessions.c.play_date.desc())

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_end_session(
        self, user_id: int = None
    ) -> Optional[List[Row]]:
        sql = end_sessions.select(end_sessions.c.user == user_id).order_by(end_sessions.c.play_date.desc())

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
    
    async def remove_end_session(self, end_id: int) -> None:
        result = await self.execute(end_sessions.delete(end_sessions.c.id == end_id))
        if result is None:
            self.logger.error(f"Failed to delete end session {end_id}")
    
    async def remove_hero_log(self, user_hero_log_id: int) -> None:
        sql = hero_log_data.delete(hero_log_data.c.id == user_hero_log_id)

        result = await self.execute(sql)
        if not result:
            self.logger.error(f"Failed to remove hero log id: {user_hero_log_id}")

    async def remove_equipment(self, equipment_id: int) -> None:
        sql = equipment_data.delete(equipment_data.c.id == equipment_id)

        result = await self.execute(sql)
        if not result:
            self.logger.error(f"Failed to remove equipment id {equipment_id}")

    async def remove_item(self, user_item_id: int) -> None:
        sql = item_data.delete(item_data.c.id == user_item_id)

        result = await self.execute(sql)
        if not result:
            self.logger.error(f"Failed to remove item {user_item_id}!")

