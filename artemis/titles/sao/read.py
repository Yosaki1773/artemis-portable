import csv
from os import path
from typing import Optional, Dict, List

from core.config import CoreConfig
from read import BaseReader

from .database import SaoData
from .const import SaoConstants

class SaoReader(BaseReader):
    def __init__(self, config: CoreConfig, version: int, bin_dir: Optional[str], opt_dir: Optional[str], extra: Optional[str]) -> None:
        super().__init__(config, version, bin_dir, opt_dir, extra)
        self.data = SaoData(config)

        try:
            self.logger.info(
                f"Start importer for {SaoConstants.game_ver_to_string(version)}"
            )
        except IndexError:
            self.logger.error(f"Invalid project SAO version {version}")
            exit(1)
    
    async def read(self) -> None:
        if path.exists(self.bin_dir):
            await self.read_csv(f"{self.bin_dir}")

        else:
            self.logger.warning("Directory not found, nothing to import")

    def load_csv_file(self, file: str) -> List[Dict]:
        ret = []
        try:
            fullPath = self.bin_dir + "/" if not self.bin_dir.endswith("/") else ""
            fullPath += file
            with open(fullPath, encoding="UTF-8") as fp:
                reader = csv.DictReader(fp)
                for row in reader:
                    tmp = {}
                    
                    fkey = list(row.keys())[0]
                    new_fkey = fkey.replace("// ", "")
                    fval = row[fkey]
                    row.pop(fkey)
                    row[new_fkey] = fval

                    for k,v in row.items():
                        if v == "-1":
                            row[k] = None
                        elif v.isdigit():
                            row[k] = int(v)
                        elif v.isdecimal():
                            row[k] = float(v)
                        elif v == "True":
                            row[k] = True
                        elif v == "False":
                            row[k] = False
                    ret.append(row)

        except Exception as e:
            self.logger.warning(f"Couldn't read csv file {fullPath}, skipping - {e}")
        
        return ret

    async def read_csv(self, bin_dir: str) -> None:
        self.logger.info(f"Read csv from {bin_dir}")

        self.logger.info("Now reading QuestScene.csv")
        reader = self.load_csv_file("QuestScene.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding quest {row['QuestSceneId']}")
                await self.data.static.put_quest(row)

        self.logger.info("Now reading Property.csv")
        reader = self.load_csv_file("Property.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding property {row['PropertyId']}")
                await self.data.static.put_property(row)

        self.logger.info("Now reading Equipment.csv")
        reader = self.load_csv_file("Equipment.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding equipment {row['EquipmentId']}")
                await self.data.static.put_equipment(row)

        self.logger.info("Now reading Skill.csv")
        reader = self.load_csv_file("Skill.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding skill {row['SkillId']}")
                await self.data.static.put_skill(row)

        self.logger.info("Now reading SkillTable.csv")
        reader = self.load_csv_file("SkillTable.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding skill table {row['SkillId']} | SubId: {row['SkillTableSubId']}")
                await self.data.static.put_skill_table(row['SkillId'], row['SkillTableSubId'], row['Level'], row['AwakeningId'], row['SkillTableId'])

        self.logger.info("Now reading HeroLog.csv")
        reader = self.load_csv_file("HeroLog.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding hero {row['HeroLogId']}")
                await self.data.static.put_hero(row)

        self.logger.info("Now reading Item.csv")
        reader = self.load_csv_file("Item.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding item {row['ItemId']}")
                await self.data.static.put_item(row)

        self.logger.info("Now reading SupportLog.csv")
        reader = self.load_csv_file("SupportLog.csv")
        if reader:
            for row in reader:
                supportLogId = row["SupportLogId"]
                charaId = row["CharaId"]
                name = row["Name"]
                rarity = row["Rarity"]
                salePrice = row["SalePrice"]
                skillName = row["SkillName"]
                enabled = True

                self.logger.info(f"Adding support log {supportLogId}")
                await self.data.static.put_support_log(
                    0,
                    supportLogId,
                    charaId,
                    name,
                    rarity,
                    salePrice,
                    skillName,
                    enabled
                )

        self.logger.info("Now reading Title.csv")
        reader = self.load_csv_file("Title.csv")
        if reader:
            for row in reader:
                titleId = row["TitleId"]
                displayName = row["DisplayName"]
                requirement = row["Requirement"]
                rank = row["Rank"]
                imageFilePath = row["ImageFilePath"]
                enabled = True

                self.logger.info(f"Adding title {titleId}")
                await self.data.static.put_title(
                    0,
                    titleId,
                    displayName,
                    requirement,
                    rank,
                    imageFilePath,
                    enabled
                )

        self.logger.info("Now reading QuestRareDrop.csv")
        reader = self.load_csv_file("QuestRareDrop.csv")
        if reader:
            for row in reader:
                questRareDropId = row["QuestRareDropId"]
                commonRewardId = row["CommonRewardId"]
                enabled = True

                self.logger.info(f"Adding rare drop {questRareDropId} | Reward: {commonRewardId}")
                await self.data.static.put_rare_drop(
                        0,
                        questRareDropId,
                        commonRewardId,
                        enabled
                    )

        self.logger.info("Now reading RewardTable.csv")
        reader = self.load_csv_file("RewardTable.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding reward table {row['RewardTableId']} | Sub-ID: {row['RewardTableSubId']} | Reward {row['CommonRewardId']}")
                await self.data.static.put_reward_table(row)

        self.logger.info("Now reading ExBonusTable.csv")
        reader = self.load_csv_file("ExBonusTable.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding ex bonus {row['ExBonusTableId']} | Sub-ID: {row['ExBonusTableSubId']} | Reward {row['CommonRewardId']}")
                await self.data.static.put_ex_bonus(row)

        self.logger.info("Now reading PlayerTraceTable.csv")
        reader = self.load_csv_file("PlayerTraceTable.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding trace table {row['PlayerTraceTableId']} | Sub-ID: {row['PlayerTraceTableSubId']} | Reward {row['CommonRewardId']}")
                await self.data.static.put_player_trace(row)

        self.logger.info("Now reading Episode.csv")
        reader = self.load_csv_file("Episode.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding episode {row['EpisodeId']}")
                await self.data.static.put_episode(row)

        self.logger.info("Now reading TrialTower.csv")
        reader = self.load_csv_file("TrialTower.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding tower {row['TrialTowerId']}")
                await self.data.static.put_tower(row)

        self.logger.info("Now reading ExTowerQuests.csv")
        reader = self.load_csv_file("ExTowerQuests.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding ex tower {row['ExTowerQuestId']}")
                await self.data.static.put_ex_tower(row)

        self.logger.info("Now reading SideQuest.csv")
        reader = self.load_csv_file("SideQuest.csv")
        if reader:
            for row in reader:
                self.logger.info(f"Adding side quest {row['SideQuestId']}")
                await self.data.static.put_side_quest(row)
