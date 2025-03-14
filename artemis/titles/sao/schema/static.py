from typing import Dict, List, Optional, Union
from sqlalchemy import Table, Column, UniqueConstraint, ForeignKey
from sqlalchemy.types import Integer, String, BIGINT, Boolean, INTEGER, VARCHAR, BOOLEAN, DECIMAL
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.dialects.mysql import insert

from core.data.schema import BaseData, metadata
from core.data import cached

quest = Table(
    "sao_static_quest",
    metadata,
    Column("QuestSceneId", BIGINT, primary_key=True, nullable=False),
    Column("SortNo", INTEGER, nullable=False),
    Column("Tutorial", BOOLEAN, nullable=False),
    Column("ColRate", DECIMAL, nullable=False),
    Column("LimitDefault", INTEGER, nullable=False),
    Column("LimitResurrection", INTEGER, nullable=False),
    Column("RewardTableSubId", INTEGER, nullable=False),
    Column("PlayerTraceTableSubId", INTEGER, nullable=False),
    Column("SuccessPlayerExp", INTEGER, nullable=False),
    Column("FailedPlayerExp", INTEGER, nullable=False),
    Column("PairExpRate", INTEGER, nullable=False),
    Column("TrioExpRate", INTEGER, nullable=False),
    Column("SingleRewardVp", INTEGER, nullable=False),
    Column("PairRewardVp", INTEGER, nullable=False),
    Column("TrioRewardVp", INTEGER, nullable=False),
    mysql_charset="utf8mb4"
)

prop = Table(
    "sao_static_property",
    metadata,
    Column("PropertyId", BIGINT, primary_key=True, nullable=False),
    Column("PropertyTargetType", INTEGER, nullable=False),
    Column("PropertyName", VARCHAR(255), nullable=False),
    Column("PropertyName_en", VARCHAR(255)),
    Column("PropertyNameFormat", VARCHAR(255), nullable=False),
    Column("PropertyNameFormat_en", VARCHAR(255)),
    Column("PropertyTypeId", INTEGER, nullable=False),
    Column("Value1Min", INTEGER, nullable=False),
    Column("Value1Max", INTEGER, nullable=False),
    Column("Value2Min", INTEGER, nullable=False),
    Column("Value2Max", INTEGER, nullable=False),
    mysql_charset="utf8mb4"
)

player_trace = Table(
    "sao_static_trace_table",
    metadata,
    Column("PlayerTraceTableId", BIGINT, primary_key=True, nullable=False),
    Column("PlayerTraceTableSubId", INTEGER, nullable=False),
    Column("CommonRewardType", INTEGER, nullable=False),
    Column("CommonRewardId", INTEGER, nullable=False),
    Column("CommonRewardNum", INTEGER, nullable=False),
    Column("Rate", INTEGER, nullable=False),
    mysql_charset="utf8mb4"
)

skill = Table(
    "sao_static_skill",
    metadata,
    Column("SkillId", BIGINT, nullable=False, primary_key=True),
    Column("WeaponTypeId", INTEGER, nullable=False),
    Column("Name", VARCHAR(255), nullable=False),
    Column("Name_en", VARCHAR(255)),
    Column("Attack", BOOLEAN, nullable=False),
    Column("Passive", BOOLEAN, nullable=False),
    Column("Pet", BOOLEAN, nullable=False),
    Column("Level", INTEGER, nullable=False),
    Column("SkillCondition", INTEGER, nullable=False),
    Column("CoolTime", INTEGER, nullable=False),
    Column("SkillIcon", VARCHAR(255), nullable=False),
    Column("FriendSkillIcon", VARCHAR(255), nullable=False),
    Column("InfoText", VARCHAR(255), nullable=False),
    Column("InfoText_en", VARCHAR(255)),
    mysql_charset="utf8mb4"
)

skill_table = Table(
    "sao_static_skill_table",
    metadata,
    Column("SkillTableId", BIGINT, nullable=False, primary_key=True),
    Column("SkillId", BIGINT, ForeignKey("sao_static_skill.SkillId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("SkillTableSubId", INTEGER, nullable=False),
    Column("LevelObtained", INTEGER, nullable=False), # Level
    Column("AwakeningId", INTEGER, nullable=False),
    mysql_charset="utf8mb4"
)

equipment = Table(
    "sao_static_equipment_list",
    metadata,
    Column("EquipmentId", BIGINT, primary_key=True, nullable=False),
    Column("EquipmentType", INTEGER, nullable=False),
    Column("WeaponTypeId", INTEGER, nullable=False),
    Column("Name", VARCHAR(255), nullable=False),
    Column("Name_en", VARCHAR(255)),
    Column("Rarity", INTEGER, nullable=False),
    Column("Power", INTEGER, nullable=False),
    Column("StrengthIncrement", INTEGER, nullable=False),
    Column("SkillCondition", INTEGER, nullable=False),
    Column("Property1PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property1Value1", INTEGER, nullable=False),
    Column("Property1Value2", INTEGER, nullable=False),
    Column("Property2PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property2Value1", INTEGER, nullable=False),
    Column("Property2Value2", INTEGER, nullable=False),
    Column("Property3PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property3Value1", INTEGER, nullable=False),
    Column("Property3Value2", INTEGER, nullable=False),
    Column("Property4PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property4Value1", INTEGER, nullable=False),
    Column("Property4Value2", INTEGER, nullable=False),
    Column("SalePrice", INTEGER, nullable=False),
    Column("CompositionExp", INTEGER, nullable=False),
    Column("AwakeningExp", INTEGER, nullable=False),
    Column("FlavorText", VARCHAR(255), nullable=False),
    Column("FlavorText_en", VARCHAR(255)),
    mysql_charset="utf8mb4"
)

hero = Table(
    "sao_static_hero_list",
    metadata,
    Column("HeroLogId", BIGINT, primary_key=True, nullable=False),
    Column("CharaId", INTEGER, nullable=False),
    Column("Name", VARCHAR(255), nullable=False),
    Column("Nickname", VARCHAR(255), nullable=False),
    Column("Name_en", VARCHAR(255)),
    Column("Nickname_en", VARCHAR(255)),
    Column("Rarity", INTEGER, nullable=False),
    Column("WeaponTypeId", INTEGER, nullable=False),
    Column("HeroLogRoleId", INTEGER, nullable=False),
    Column("CostumeTypeId", INTEGER, nullable=False),
    Column("UnitId", INTEGER, nullable=False),
    Column("DefaultEquipmentId1", BIGINT, ForeignKey("sao_static_equipment_list.EquipmentId", ondelete="cascade", onupdate="cascade")),
    Column("DefaultEquipmentId2", BIGINT, ForeignKey("sao_static_equipment_list.EquipmentId", ondelete="cascade", onupdate="cascade")),
    Column("SkillTableSubId", INTEGER, nullable=False),
    Column("HpMin", INTEGER, nullable=False),
    Column("HpMax", INTEGER, nullable=False),
    Column("StrMin", INTEGER, nullable=False),
    Column("StrMax", INTEGER, nullable=False),
    Column("VitMin", INTEGER, nullable=False),
    Column("VitMax", INTEGER, nullable=False),
    Column("IntMin", INTEGER, nullable=False),
    Column("IntMax", INTEGER, nullable=False),
    Column("Property1PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property1Value1", INTEGER, nullable=False),
    Column("Property1Value2", INTEGER, nullable=False),
    Column("Property2PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property2Value1", INTEGER, nullable=False),
    Column("Property2Value2", INTEGER, nullable=False),
    Column("Property3PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property3Value1", INTEGER, nullable=False),
    Column("Property3Value2", INTEGER, nullable=False),
    Column("Property4PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property4Value1", INTEGER, nullable=False),
    Column("Property4Value2", INTEGER, nullable=False),
    Column("FlavorText", VARCHAR(255), nullable=False),
    Column("FlavorText_en", VARCHAR(255)),
    Column("SalePrice", INTEGER, nullable=False),
    Column("CompositionExp", INTEGER, nullable=False),
    Column("AwakeningExp", INTEGER, nullable=False),
    Column("Slot4UnlockLevel", INTEGER, nullable=False),
    Column("Slot5UnlockLevel", INTEGER, nullable=False),
    Column("CollectionEmptyFrameDisplayFlag", BOOLEAN, nullable=False),
    mysql_charset="utf8mb4"
)

item = Table(
    "sao_static_item_list",
    metadata,
    Column("ItemId", INTEGER, nullable=False, primary_key=True),
    Column("ItemTypeId", INTEGER, nullable=False),
    Column("Name", VARCHAR(255), nullable=False),
    Column("Name_en", VARCHAR(255)),
    Column("Rarity", INTEGER, nullable=False),
    Column("Value", INTEGER, nullable=False),
    Column("PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("PropertyValue1Min", INTEGER, nullable=False),
    Column("PropertyValue1Max", INTEGER, nullable=False),
    Column("PropertyValue2Min", INTEGER, nullable=False),
    Column("PropertyValue2Max", INTEGER, nullable=False),
    Column("FlavorText", VARCHAR(255), nullable=False),
    Column("FlavorText_en", VARCHAR(255)),
    Column("SalePrice", INTEGER, nullable=False),
    Column("ItemIcon", VARCHAR(255), nullable=False),
    mysql_charset="utf8mb4"
)

support = Table(
    "sao_static_support_log_list",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer),
    Column("supportLogId", Integer),
    Column("charaId", Integer),
    Column("name", String(255)),
    Column("rarity", Integer),
    Column("salePrice", Integer),
    Column("skillName", String(255)),
    Column("enabled", Boolean),
    UniqueConstraint(
        "version", "supportLogId", name="sao_static_support_log_list_uk"
    ),
    mysql_charset="utf8mb4"
)

rare_drop = Table(
    "sao_static_rare_drop_list",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer),
    Column("questRareDropId", Integer),
    Column("commonRewardId", Integer),
    Column("enabled", Boolean),
    UniqueConstraint(
        "version", "questRareDropId", "commonRewardId", name="sao_static_rare_drop_list_uk"
    ),
    mysql_charset="utf8mb4"
)

title = Table(
    "sao_static_title_list",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer),
    Column("titleId", Integer),
    Column("displayName", String(255)),
    Column("requirement", Integer),
    Column("rank", Integer),
    Column("imageFilePath", String(255)),
    Column("enabled", Boolean),
    UniqueConstraint(
        "version", "titleId", name="sao_static_title_list_uk"
    ),
    mysql_charset="utf8mb4"
)

reward = Table(
    "sao_static_reward",
    metadata,
    Column("RewardTableId", BIGINT, primary_key=True, nullable=False),
    Column("RewardTableSubId", INTEGER, nullable=False),
    Column("UnanalyzedLogGradeId", INTEGER, nullable=False),
    Column("CommonRewardType", INTEGER, nullable=False),
    Column("CommonRewardId", INTEGER, nullable=False),
    Column("CommonRewardNum", INTEGER, nullable=False),
    Column("StrengthMin", INTEGER, nullable=False),
    Column("StrengthMax", INTEGER, nullable=False),
    Column("PropertyTableSubId", INTEGER, nullable=False),
    Column("QuestInfoDisplayFlag", BOOLEAN, nullable=False),
    Column("Rate", INTEGER, nullable=False),
    mysql_charset="utf8mb4"
)

ex_bonus = Table(
    "sao_static_ex_bonus",
    metadata,
    Column("ExBonusTableId", BIGINT, primary_key=True, nullable=False),
    Column("ExBonusTableSubId", INTEGER, nullable=False),
    Column("ExBonusConditionId", INTEGER, nullable=False),
    Column("ConditionValue1", INTEGER, nullable=False),
    Column("ConditionValue2", INTEGER, nullable=False),
    Column("CommonRewardType", INTEGER, nullable=False),
    Column("CommonRewardId", INTEGER, nullable=False),
    Column("CommonRewardNum", INTEGER, nullable=False),
    Column("Strength", INTEGER, nullable=False),
    Column("Property1PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property1Value1", INTEGER, nullable=False),
    Column("Property1Value2", INTEGER, nullable=False),
    Column("Property2PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property2Value1", INTEGER, nullable=False),
    Column("Property2Value2", INTEGER, nullable=False),
    Column("Property3PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property3Value1", INTEGER, nullable=False),
    Column("Property3Value2", INTEGER, nullable=False),
    Column("Property4PropertyId", BIGINT, ForeignKey("sao_static_property.PropertyId", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("Property4Value1", INTEGER, nullable=False),
    Column("Property4Value2", INTEGER, nullable=False),
    mysql_charset="utf8mb4"
)

episode = Table(
    "sao_static_episode",
    metadata,
    Column("EpisodeId", BIGINT, nullable=False, primary_key=True),
    Column("EpisodeChapterId", INTEGER, nullable=False),
    Column("ReleaseEpisodeId", INTEGER, nullable=False),
    Column("Title", VARCHAR(255), nullable=False),
    Column("CommentSummary", VARCHAR(255), nullable=False),
    Column("ExBonusTableSubId", INTEGER, nullable=False),
    Column("QuestSceneId", BIGINT, ForeignKey("sao_static_quest.QuestSceneId", ondelete="cascade", onupdate="cascade")),
    mysql_charset="utf8mb4"
)

tower = Table(
    "sao_static_tower",
    metadata,
    Column("TowerId", BIGINT, nullable=False, primary_key=True),
    Column("ReleaseTowerId", INTEGER, nullable=False),
    Column("ExBonusTableSubId", INTEGER, nullable=False),
    Column("QuestSceneId", BIGINT, ForeignKey("sao_static_quest.QuestSceneId", ondelete="cascade", onupdate="cascade"), nullable=False),
    mysql_charset="utf8mb4"
)

ex_tower = Table(
    "sao_static_ex_tower",
    metadata,
    Column("ExTowerQuestId", BIGINT, nullable=False, primary_key=True),
    Column("ExTowerId", INTEGER, nullable=False),
    Column("ReleaseExTowerQuestId", INTEGER, nullable=False),
    Column("Title", VARCHAR(255), nullable=False),
    Column("Title_en", VARCHAR(255)),
    Column("ExBonusTableSubId", INTEGER, nullable=False),
    Column("QuestSceneId", BIGINT, ForeignKey("sao_static_quest.QuestSceneId", ondelete="cascade", onupdate="cascade"), nullable=False),
    mysql_charset="utf8mb4"
)

side_quest = Table(
    "sao_static_side_quest",
    metadata,
    Column("SideQuestId", BIGINT, nullable=False, unique=True, primary_key=True),
    Column("DisplayName", VARCHAR(255), nullable=False),
    Column("DisplayName_en", VARCHAR(255)),
    Column("EpisodeNum", INTEGER, nullable=False),
    Column("ExBonusTableSubId", INTEGER, nullable=False),
    Column("QuestSceneId", BIGINT, ForeignKey("sao_static_quest.QuestSceneId", ondelete="cascade", onupdate="cascade"), nullable=False),
    mysql_charset="utf8mb4"
)

class SaoStaticData(BaseData):
    async def put_quest(self, data: Dict[str, str]) -> Optional[int]:
        sql = insert(quest).values(
            QuestSceneId=data["QuestSceneId"],
            SortNo=data["SortNo"],
            Tutorial=data["Tutorial"],
            ColRate=data["ColRate"],
            LimitDefault=data["LimitDefault"],
            LimitResurrection=data["LimitResurrection"],
            RewardTableSubId=data["RewardTableSubId"],
            PlayerTraceTableSubId=data["PlayerTraceTableSubId"],
            SuccessPlayerExp=data["SuccessPlayerExp"],
            FailedPlayerExp=data["FailedPlayerExp"],
            PairExpRate=data["PairExpRate"],
            TrioExpRate=data["TrioExpRate"],
            SingleRewardVp=data["SingleRewardVp"],
            PairRewardVp=data["PairRewardVp"],
            TrioRewardVp=data["TrioRewardVp"],
        )

        conflict = sql.on_duplicate_key_update(QuestSceneId=data["QuestSceneId"])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data["QuestSceneId"]
    
    async def put_hero(self, data: Dict[str, str]) -> Optional[int]:
        sql = insert(hero).values(
            HeroLogId=data["HeroLogId"],
            CharaId=data["CharaId"],
            Name=data["Name"],
            Nickname=data["Nickname"],
            Rarity=data["Rarity"],
            WeaponTypeId=data["WeaponTypeId"],
            HeroLogRoleId=data["HeroLogRoleId"],
            CostumeTypeId=data["CostumeTypeId"],
            UnitId=data["UnitId"],
            DefaultEquipmentId1=data["DefaultEquipmentId1"],
            DefaultEquipmentId2=data["DefaultEquipmentId2"],
            SkillTableSubId=data["SkillTableSubId"],
            HpMin=data["HpMin"],
            HpMax=data["HpMax"],
            StrMin=data["StrMin"],
            StrMax=data["StrMax"],
            VitMin=data["VitMin"],
            VitMax=data["VitMax"],
            IntMin=data["IntMin"],
            IntMax=data["IntMax"],
            Property1PropertyId=data["Property1PropertyId"],
            Property1Value1=data["Property1Value1"],
            Property1Value2=data["Property1Value2"],
            Property2PropertyId=data["Property2PropertyId"],
            Property2Value1=data["Property2Value1"],
            Property2Value2=data["Property2Value2"],
            Property3PropertyId=data["Property3PropertyId"],
            Property3Value1=data["Property3Value1"],
            Property3Value2=data["Property3Value2"],
            Property4PropertyId=data["Property4PropertyId"],
            Property4Value1=data["Property4Value1"],
            Property4Value2=data["Property4Value2"],
            FlavorText=data["FlavorText"],
            SalePrice=data["SalePrice"],
            CompositionExp=data["CompositionExp"],
            AwakeningExp=data["AwakeningExp"],
            Slot4UnlockLevel=data["Slot4UnlockLevel"],
            Slot5UnlockLevel=data["Slot5UnlockLevel"],
            CollectionEmptyFrameDisplayFlag=data["CollectionEmptyFrameDisplayFlag"],
        )

        conflict = sql.on_duplicate_key_update(HeroLogId=data["HeroLogId"])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data["HeroLogId"]
    
    async def put_hero_translation(self, hero_id: int, name_en: str, nickname_en: str, flavor_text_en: str) -> None:
        result = await self.execute(hero.update(hero.c.HeroLogId == hero_id).values(
            Name=name_en,
            Nickname=nickname_en,
            FlavorText=flavor_text_en,
        ))

        result = await self.execute(result)
        if result is None:
            self.logger.error(f"Failed to add translated text for hero {hero_id}")
    
    async def put_equipment(self, data: Dict[str, str]) -> Optional[int]:
        sql = insert(equipment).values(
            EquipmentId=data["EquipmentId"],
            EquipmentType=data["EquipmentType"],
            WeaponTypeId=data["WeaponTypeId"],
            Name=data["Name"],
            Rarity=data["Rarity"],
            Power=data["Power"],
            StrengthIncrement=data["StrengthIncrement"],
            SkillCondition=data["SkillCondition"],
            Property1PropertyId=data["Property1PropertyId"],
            Property1Value1=data["Property1Value1"],
            Property1Value2=data["Property1Value2"],
            Property2PropertyId=data["Property2PropertyId"],
            Property2Value1=data["Property2Value1"],
            Property2Value2=data["Property2Value2"],
            Property3PropertyId=data["Property3PropertyId"],
            Property3Value1=data["Property3Value1"],
            Property3Value2=data["Property3Value2"],
            Property4PropertyId=data["Property4PropertyId"],
            Property4Value1=data["Property4Value1"],
            Property4Value2=data["Property4Value2"],
            SalePrice=data["SalePrice"],
            CompositionExp=data["CompositionExp"],
            AwakeningExp=data["AwakeningExp"],
            FlavorText=data["FlavorText"],
        )

        conflict = sql.on_duplicate_key_update(EquipmentId=data["EquipmentId"])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data["EquipmentId"]
    
    async def put_equipment_translation(self, equip_id: int, name_en: str, flavor_text_en: str) -> None:
        result = await self.execute(equipment.update(equipment.c.EquipmentId == equip_id).values(
            Name_en=name_en,
            FlavorText_en=flavor_text_en,
        ))

        result = await self.execute(result)
        if result is None:
            self.logger.error(f"Failed to add translated text for equipment {equip_id}")
    
    async def put_item(self, data: Dict[str, str]) -> Optional[int]:
        sql = insert(item).values(
            ItemId=data["ItemId"],
            ItemTypeId=data["ItemTypeId"],
            Name=data["Name"],
            Rarity=data["Rarity"],
            Value=data["Value"],
            PropertyId=data["PropertyId"],
            PropertyValue1Min=data["PropertyValue1Min"],
            PropertyValue1Max=data["PropertyValue1Max"],
            PropertyValue2Min=data["PropertyValue2Min"],
            PropertyValue2Max=data["PropertyValue2Max"],
            FlavorText=data["FlavorText"],
            SalePrice=data["SalePrice"],
            ItemIcon=data["ItemIcon"],

        )

        conflict = sql.on_duplicate_key_update(ItemId=data["ItemId"])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data["ItemId"]

    async def put_item_translation(self, item_id: int, name_en: str, flavor_text_en: str) -> None:
        result = await self.execute(item.update(item.c.ItemId == item_id).values(
            Name_en=name_en,
            FlavorText_en=flavor_text_en,
        ))

        result = await self.execute(result)
        if result is None:
            self.logger.error(f"Failed to add translated text for item {item_id}")

    async def put_property(self, data: Dict[str, str]) -> None:
        sql = insert(prop).values(
            PropertyId=data["PropertyId"],
            PropertyTargetType=data["PropertyTargetType"],
            PropertyName=data["PropertyName"],
            PropertyNameFormat=data["PropertyNameFormat"],
            PropertyTypeId=data["PropertyTypeId"],
            Value1Min=data["Value1Min"],
            Value1Max=data["Value1Max"],
            Value2Min=data["Value2Min"],
            Value2Max=data["Value2Max"],
        )

        conflict = sql.on_duplicate_key_update(PropertyId=data["PropertyId"])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data["PropertyId"]
    
    async def put_property_translation(self, property_id: int, name_en: str, name_fmt: str) -> None:
        result = await self.execute(prop.update(prop.c.PropertyId == property_id).values(
            Name_en=name_en,
            PropertyNameFormat_en=name_fmt,
        ))

        result = await self.execute(result)
        if result is None:
            self.logger.error(f"Failed to add translated text for property {property_id}")

    async def put_skill(self, data: Dict[str, str]) -> None:
        sql = insert(skill).values(
            SkillId=data["SkillId"],
            WeaponTypeId=data["WeaponTypeId"],
            Name=data["Name"],
            Attack=data["Attack"],
            Passive=data["Passive"],
            Pet=data["Pet"],
            Level=data["Level"],
            SkillCondition=data["SkillCondition"],
            CoolTime=data["CoolTime"],
            SkillIcon=data["SkillIcon"],
            FriendSkillIcon=data["FriendSkillIcon"],
            InfoText=data["InfoText"],
        )

        conflict = sql.on_duplicate_key_update(SkillId=data["SkillId"])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data["SkillId"]
    
    async def put_skill_translation(self, skill_id: int, name_en: str, info_txt: str) -> None:
        result = await self.execute(skill.update(skill.c.SkillId == skill_id).values(
            Name_en=name_en,
            InfoText_en=info_txt,
        ))

        result = await self.execute(result)
        if result is None:
            self.logger.error(f"Failed to add translated text for skill {skill_id}")

    async def put_skill_table(self, skill_id: int, sub_id: int, level: int, awakening: int, table_id: int) -> None:
        sql = insert(skill_table).values(
            SkillTableId=table_id,
            SkillId=skill_id,
            SkillTableSubId=sub_id,
            LevelObtained=level,
            AwakeningId=awakening,
        )
        conflict = sql.on_duplicate_key_update(SkillTableId=table_id)
        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"Failed to add skill table {skill_id}")

    async def put_player_trace(self, data: Dict[str, str]) -> None:
        sql = insert(player_trace).values(
            PlayerTraceTableId=data["PlayerTraceTableId"],
            PlayerTraceTableSubId=data["PlayerTraceTableSubId"],
            CommonRewardType=data["CommonRewardType"],
            CommonRewardId=data["CommonRewardId"],
            CommonRewardNum=data["CommonRewardNum"],
            Rate=data["Rate"],
        )

        conflict = sql.on_duplicate_key_update(PlayerTraceTableId=data["PlayerTraceTableId"])
        result = await self.execute(conflict)
        if result is None:
            return None
        return data["PlayerTraceTableId"]

    async def put_support_log( self, version: int, supportLogId: int, charaId: int, name: str, rarity: int, salePrice: int, skillName: str, enabled: bool ) -> Optional[int]:
        sql = insert(support).values(
            version=version,
            supportLogId=supportLogId,
            charaId=charaId,
            name=name,
            rarity=rarity,
            salePrice=salePrice,
            skillName=skillName,
            enabled=enabled
        )

        conflict = sql.on_duplicate_key_update(version=version)

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert support log {supportLogId}!")

    async def put_rare_drop( self, version: int, questRareDropId: int, commonRewardId: int, enabled: bool ) -> Optional[int]:
        sql = insert(rare_drop).values(
            version=version,
            questRareDropId=questRareDropId,
            commonRewardId=commonRewardId,
            enabled=enabled,
        )

        conflict = sql.on_duplicate_key_update(version=version)

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert rare drop {questRareDropId}!")
    
    async def put_title( self, version: int, titleId: int, displayName: str, requirement: int, rank: int, imageFilePath: str, enabled: bool ) -> Optional[int]:
        sql = insert(title).values(
            version=version,
            titleId=titleId,
            displayName=displayName,
            requirement=requirement,
            rank=rank,
            imageFilePath=imageFilePath,
            enabled=enabled
        )

        conflict = sql.on_duplicate_key_update(version=version)

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        self.logger.error(f"Failed to insert title {titleId}")

    async def put_reward_table(self, data: Dict[str, Union[str, bool]]) -> None:
        sql = insert(reward).values(
            **data
        )

        conflict = sql.on_duplicate_key_update(**data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return data['RewardTableId']
    
    async def put_ex_bonus(self, data: Dict[str, int]) -> None:
        sql = insert(ex_bonus).values(
            **data
        )

        conflict = sql.on_duplicate_key_update(**data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return data['ExBonusTableId']

    async def put_episode(self, data: Dict[str, int]) -> None:
        sql = insert(episode).values(
            EpisodeId=data['EpisodeId'],
            EpisodeChapterId=data['EpisodeChapterId'],
            ReleaseEpisodeId=data['ReleaseEpisodeId'],
            Title=data['Title'],
            CommentSummary=data['CommentSummary'],
            ExBonusTableSubId=data['ExBonusTableSubId'],
            QuestSceneId=data['QuestSceneId'] if data['QuestSceneId'] > 0 else None,
        )

        conflict = sql.on_duplicate_key_update(EpisodeId=data['EpisodeId'])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data['EpisodeId']

    async def put_tower(self, data: Dict[str, int]) -> None:
        sql = insert(tower).values(
            TowerId=data['TrialTowerId'],
            ReleaseTowerId=data['ReleaseTrialTowerId'],
            ExBonusTableSubId=data['ExBonusTableSubId'],
            QuestSceneId=data['QuestSceneId'],
        )

        conflict = sql.on_duplicate_key_update(TowerId=data['TrialTowerId'])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data['TrialTowerId']
    
    async def put_ex_tower(self, data: Dict[str, int]) -> None:
        sql = insert(ex_tower).values(
            ExTowerQuestId=data['ExTowerQuestId'],
            ExTowerId=data['ExTowerId'],
            ReleaseExTowerQuestId=data['ReleaseExTowerQuestId'],
            Title=data['Title'],
            ExBonusTableSubId=data['ExBonusTableSubId'],
            QuestSceneId=data['QuestSceneId'],
        )

        conflict = sql.on_duplicate_key_update(ExTowerQuestId=data['ExTowerQuestId'])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data['ExTowerQuestId']

    async def put_side_quest(self, data: Dict[str, int]) -> None:
        sql = insert(side_quest).values(
            SideQuestId=data['SideQuestId'],
            DisplayName=data['DisplayName'],
            EpisodeNum=data['EpisodeNum'],
            ExBonusTableSubId=data['ExBonusTableSubId'],
            QuestSceneId=data['QuestSceneId'],
        )

        conflict = sql.on_duplicate_key_update(SideQuestId=data['SideQuestId'])

        result = await self.execute(conflict)
        if result is None:
            return None
        return data['SideQuestId']

    async def get_quest_by_id(self, quest_scene_id: int) -> Optional[Row]:
        result = await self.execute(quest.select(quest.c.QuestSceneId == quest_scene_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_quests(self) -> Optional[List[Row]]:
        result = await self.execute(quest.select())
        if result is None:
            return None
        return result.fetchall()
    
    async def get_hero_by_id(self, heroLogId: int) -> Optional[Row]:
        result = await self.execute(hero.select(hero.c.HeroLogId == heroLogId))
        if result is None:
            return None
        return result.fetchone()
    
    async def get_heros(self) -> Optional[List[Row]]:
        result = await self.execute(hero.select())
        if result is None:
            return None
        return result.fetchall()
    
    async def get_equipment_by_id(self, equipmentId: int) -> Optional[Dict]:
        result = await self.execute(equipment.select(equipment.c.EquipmentId == equipmentId))
        if result is None:
            return None
        return result.fetchone()
    
    async def get_equipment(self) -> Optional[List[Dict]]:
        result = await self.execute(equipment.select())
        if result is None:
            return None
        return result.fetchall()

    async def get_item_id(self, item_id: int) -> Optional[Dict]:
        sql = item.select(item.c.ItemId == item_id)
        
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_rare_drop_id(self, questRareDropId: int) -> Optional[Dict]:
        sql = rare_drop.select(rare_drop.c.questRareDropId == questRareDropId)
        
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
    
    async def get_item_ids(self, version: int, enabled: bool) -> Optional[List[Dict]]:
        sql = item.select(item.c.version == version and item.c.enabled == enabled).order_by(
            item.c.itemId.asc()
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return [list[2] for list in result.fetchall()]
    
    async def get_support_logs(self) -> Optional[List[Dict]]:
        result = await self.execute(support.select())
        if result is None:
            return None
        return result.fetchall()

    async def get_support_log_ids(self, version: int, enabled: bool) -> Optional[List[Dict]]:
        sql = support.select(support.c.version == version and support.c.enabled == enabled).order_by(
            support.c.supportLogId.asc()
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return [list[2] for list in result.fetchall()]
    
    async def get_title_ids(self, version: int, enabled: bool) -> Optional[List[Dict]]:
        sql = title.select(title.c.version == version and title.c.enabled == enabled).order_by(
            title.c.titleId.asc()
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return [list[2] for list in result.fetchall()]

    async def get_reward_by_table(self, table_id: int) -> Optional[Row]:
        result = await self.execute(reward.select(reward.c.RewardTableId == table_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_rewards_by_subtable(self, subtable_id: int) -> Optional[List[Row]]:
        result = await self.execute(reward.select(reward.c.RewardTableSubId == subtable_id))
        if result is None:
            return None
        return result.fetchall()

    async def get_rewards(self) -> Optional[List[Row]]:
        result = await self.execute(reward.select())
        if result is None:
            return None
        return result.fetchall()

    async def get_ex_bonus_by_table(self, table_id: int) -> Optional[Row]:
        result = await self.execute(ex_bonus.select(ex_bonus.c.ExBonusTableId == table_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_ex_bonuses_by_subtable(self, subtable_id: int) -> Optional[List[Row]]:
        result = await self.execute(ex_bonus.select(ex_bonus.c.ExBonusTableSubId == subtable_id))
        if result is None:
            return None
        return result.fetchall()

    async def get_ex_bonuses(self) -> Optional[List[Row]]:
        result = await self.execute(ex_bonus.select())
        if result is None:
            return None
        return result.fetchall()
    
    async def get_episode_by_id(self, episode_id: int) -> Optional[Row]:
        result = await self.execute(episode.select(episode.c.EpisodeId == episode_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_episode_by_quest_id(self, quest_id: int) -> Optional[Row]:
        result = await self.execute(episode.select(episode.c.QuestSceneId == quest_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_episodes(self) -> Optional[List[Row]]:
        result = await self.execute(episode.select())
        if result is None:
            return None
        return result.fetchall()

    async def get_tower_by_id(self, tower_id: int) -> Optional[Row]:
        result = await self.execute(tower.select(tower.c.TowerId == tower_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_tower_by_quest_id(self, quest_id: int) -> Optional[Row]:
        result = await self.execute(tower.select(tower.c.QuestSceneId == quest_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_towers(self) -> Optional[List[Row]]:
        result = await self.execute(tower.select())
        if result is None:
            return None
        return result.fetchall()

    async def get_ex_tower_by_id(self, ex_tower_id: int) -> Optional[Row]:
        result = await self.execute(ex_tower.select(ex_tower.c.ExTowerQuestId == ex_tower_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_ex_tower_by_quest_id(self, quest_id: int) -> Optional[Row]:
        result = await self.execute(ex_tower.select(ex_tower.c.QuestSceneId == quest_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_ex_towers(self) -> Optional[List[Row]]:
        result = await self.execute(ex_tower.select())
        if result is None:
            return None
        return result.fetchall()

    async def get_ex_towers_by_tower(self, ex_tower_id: int) -> Optional[List[Row]]:
        result = await self.execute(ex_tower.select(ex_tower.c.ExTowerId == ex_tower_id))
        if result is None:
            return None
        return result.fetchall()

    async def get_side_quest_by_id(self, side_quest_id: int) -> Optional[Row]:
        result = await self.execute(side_quest.select(side_quest.c.SideQuestId == side_quest_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_side_quest_by_quest_id(self, quest_id: int) -> Optional[Row]:
        result = await self.execute(side_quest.select(side_quest.c.QuestSceneId == quest_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_side_quests(self) -> Optional[List[Row]]:
        result = await self.execute(side_quest.select())
        if result is None:
            return None
        return result.fetchall()

    async def get_side_quests_by_episode(self, episode_num: int) -> Optional[List[Row]]:
        result = await self.execute(side_quest.select(side_quest.c.EpisodeNum == episode_num))
        if result is None:
            return None
        return result.fetchall()

    async def get_player_trace_by_id(self, trace_id: int) -> Optional[Row]:
        result = await self.execute(player_trace.select(player_trace.c.PlayerTraceTableId == trace_id))
        if result is None:
            return None
        return result.fetchone()

    async def get_player_trace_by_subid(self, trace_sub_id: int) -> Optional[List[Row]]:
        result = await self.execute(player_trace.select(player_trace.c.PlayerTraceTableSubId == trace_sub_id))
        if result is None:
            return None
        return result.fetchall()

    async def get_player_traces(self) -> Optional[List[Row]]:
        result = await self.execute(player_trace.select())
        if result is None:
            return None
        return result.fetchall()

    async def get_skill_table_by_subid(self, table_sub_id: int) -> Optional[List[Row]]:
        result = await self.execute(skill_table.select(skill_table.c.SkillTableSubId == table_sub_id))

        if result is None:
            return None
        return result.fetchall()
    
    async def get_skill_by_id(self, skill_id: int) -> Optional[Row]:
        result = await self.execute(skill.select(skill.c.SkillId == skill_id))

        if result is None:
            return None
        return result.fetchone()
