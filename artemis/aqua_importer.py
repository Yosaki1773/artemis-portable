from datetime import datetime
import os
import inflection
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Row
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict, Optional

import yaml
import argparse
import logging
import coloredlogs

from core.config import CoreConfig
from core.data.database import Data
from titles.chuni.config import ChuniConfig
from titles.chuni.const import ChuniConstants
from titles.chuni.sun import ChuniSun
from titles.ongeki.brightmemory import OngekiBrightMemory
from titles.ongeki.config import OngekiConfig
from titles.ongeki.const import OngekiConstants
from titles.mai2.festival import Mai2Festival
from titles.mai2.config import Mai2Config
from titles.mai2.const import Mai2Constants


class AquaData:
    def __init__(self, aqua_db_path: str) -> None:
        if "@" in aqua_db_path:
            self.__url = f"mysql+pymysql://{aqua_db_path}"
        else:
            self.__url = f"sqlite:///{aqua_db_path}"

        self.__engine = create_engine(self.__url, pool_recycle=3600, echo=False)
        # self.inspector = reflection.Inspector.from_engine(self.__engine)

        session = sessionmaker(bind=self.__engine)
        self.inspect = inspect(self.__engine)
        self.conn = scoped_session(session)

        log_fmt_str = "[%(asctime)s] %(levelname)s | AQUA | %(message)s"
        log_fmt = logging.Formatter(log_fmt_str)
        self.logger = logging.getLogger("aqua")

        # Prevent the logger from adding handlers multiple times
        if not getattr(self.logger, "handler_set", None):
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(log_fmt)

            self.logger.addHandler(consoleHandler)

            self.logger.setLevel("WARN")
            coloredlogs.install("WARN", logger=self.logger, fmt=log_fmt_str)
            self.logger.handler_set = True  # type: ignore

    def execute(self, sql: str, opts: Dict[str, Any] = {}) -> Optional[CursorResult]:
        res = None

        try:
            self.logger.info(f"SQL Execute: {''.join(str(sql).splitlines())} || {opts}")
            res = self.conn.execute(text(sql), opts)

        except SQLAlchemyError as e:
            self.logger.error(f"SQLAlchemy error {e}")
            return None

        except UnicodeEncodeError as e:
            self.logger.error(f"UnicodeEncodeError error {e}")
            return None

        except:
            try:
                res = self.conn.execute(sql, opts)

            except SQLAlchemyError as e:
                self.logger.error(f"SQLAlchemy error {e}")
                return None

            except UnicodeEncodeError as e:
                self.logger.error(f"UnicodeEncodeError error {e}")
                return None

            except:
                self.logger.error(f"Unknown error")
                raise

        return res


class Importer:
    def __init__(self, core_cfg: CoreConfig, cfg_folder: str, aqua_folder: str):
        self.config = core_cfg
        self.config_folder = cfg_folder
        self.data = Data(core_cfg)
        self.title_registry: Dict[str, Any] = {}
        self.use_mysql = False

        self.logger = logging.getLogger("importer")
        if not hasattr(self.logger, "initialized"):
            log_fmt_str = "[%(asctime)s] Importer | %(levelname)s | %(message)s"
            log_fmt = logging.Formatter(log_fmt_str)

            fileHandler = TimedRotatingFileHandler(
                "{0}/{1}.log".format(self.config.server.log_dir, "importer"),
                when="d",
                backupCount=10,
            )
            fileHandler.setFormatter(log_fmt)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(log_fmt)

            self.logger.addHandler(fileHandler)
            self.logger.addHandler(consoleHandler)

            self.logger.setLevel("INFO")
            coloredlogs.install(level="INFO", logger=self.logger, fmt=log_fmt_str)
            self.logger.initialized = True

        if not os.path.isfile(f"{aqua_folder}/application.properties"):
            self.logger.error("Could not locate AQUA application.properties file!")
            exit(1)

        with open(f"{aqua_folder}/application.properties") as file:
            lines = file.readlines()

        properties = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("=")
            if len(parts) >= 2:
                key = parts[0].strip()
                value = "=".join(parts[1:]).strip()
                properties[key] = value

        db_driver = properties.get("spring.datasource.driver-class-name")
        if "sqlite" in db_driver:
            aqua_db_path = None
            db_url = properties.get("spring.datasource.url").split("sqlite:")[1]
            temp = os.path.join(f"{aqua_folder}/{db_url}")
            if os.path.isfile(temp):
                aqua_db_path = temp

            if not aqua_db_path:
                self.logger.error("Could not locate AQUA db.sqlite file!")
                exit(1)

            self.aqua = AquaData(aqua_db_path)

        elif "mysql" in db_driver or "mariadb" in db_driver:
            self.use_mysql = True
            db_username = properties.get("spring.datasource.username")
            db_password = properties.get("spring.datasource.password")
            db_url = (
                properties.get("spring.datasource.url").split("?")[0].split("//")[1]
            )
            self.aqua = AquaData(f"{db_username}:{db_password}@{db_url}")

        else:
            self.logger.error("Unknown database type!")

    def get_user_id(self, luid: str):
        user_id = self.data.card.get_user_id_from_card(access_code=luid)
        if user_id is not None:
            return user_id

        user_id = self.data.user.create_user()

        if user_id is None:
            user_id = -1
            self.logger.error("Failed to register user!")

        else:
            card_id = self.data.card.create_card(user_id, luid)

            if card_id is None:
                user_id = -1
                self.logger.error("Failed to register card!")

        return user_id

    def parse_aqua_db(self, table_name: str) -> tuple:
        result = self.aqua.execute(f"SELECT * FROM {table_name}")
        datetime_columns = [
            c
            for c in self.aqua.inspect.get_columns(table_name)
            if str(c["type"]) == "DATETIME"
        ]

        return result, datetime_columns

    def parse_aqua_row(
        self,
        row: Row,
        datetime_columns: list[Dict],
        unused_columns: list[str],
        card_id: int,
    ) -> Dict:
        row = row._asdict()
        if not self.use_mysql:
            for column in datetime_columns:
                ts = row[column["name"]]
                if ts is None or ts == 0:
                    continue

                # actuall remove the last 3 zeros for the correct timestamp
                fixed_ts = int(str(ts)[:-3])
                # save the datetim object in the dict
                row[column["name"]] = datetime.fromtimestamp(fixed_ts)

        tmp = {}
        for k, v in row.items():
            # convert the key (column name) to camelCase for ARTEMiS
            k = inflection.camelize(k, uppercase_first_letter=False)
            # add the new camelCase key, value pair to tmp
            tmp[k] = v if v != "null" else None

        # drop the aqua internal user id
        tmp.pop("userId", None)

        # removes unused columns
        for unused in unused_columns:
            tmp.pop(unused)

        # get from the internal user id the actual luid
        card_data = None
        card_result = self.aqua.execute(f"SELECT * FROM sega_card WHERE id = {card_id}")

        for card in card_result:
            card_data = card._asdict()

        # TODO: Add card_data is None check
        card_id = card_data["luid"]

        # get the ARTEMiS internal user id, if not create an user
        user_id = self.get_user_id(card_id)

        # add the ARTEMiS user id to the dict
        tmp["user"] = user_id

        return tmp

    def get_chuni_card_id_by_aqua_row(self, row: Row, user_id_column: str = "user_id"):
        aqua_user_id = row._asdict()[user_id_column]
        user_result = self.aqua.execute(
            f"SELECT * FROM chusan_user_data WHERE id = {aqua_user_id}"
        )

        # could never be None undless something is really fucked up
        user_data = None
        for user in user_result:
            user_data = user._asdict()

        card_id = user_data["card_id"]

        return card_id

    def import_chuni(self):
        game_cfg = ChuniConfig()
        game_cfg.update(yaml.safe_load(open(f"{self.config_folder}/chuni.yaml")))

        base = ChuniSun(self.config, game_cfg)
        version_str = ChuniConstants.game_ver_to_string(base.version)

        answer = input(
            f"Do you really want to import ALL {version_str} data into ARTEMiS? [N/y]: "
        )
        if answer.lower() != "y":
            self.logger.info("User aborted operation")
            return

        result, datetime_columns = self.parse_aqua_db("chusan_user_data")
        for row in result:
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id", "lastLoginDate", "cardId"],
                card_id=row._asdict()["card_id"],
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userData": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userData: {tmp['user']}")

        result, datetime_columns = self.parse_aqua_db("chusan_user_game_option")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            tmp["speed_120"] = tmp.pop("speed120")
            tmp["fieldWallPosition_120"] = tmp.pop("fieldWallPosition120")
            tmp["playTimingOffset_120"] = tmp.pop("playTimingOffset120")
            tmp["judgeTimingOffset_120"] = tmp.pop("judgeTimingOffset120")

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userGameOption": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userGameOption: {tmp['user']}")

        result, datetime_columns = self.parse_aqua_db("chusan_user_general_data")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            if tmp["propertyKey"] == "recent_rating_list":
                rating_list = []
                for rating in tmp["propertyValue"].split(","):
                    music_id, difficult_id, score = rating.split(":")
                    rating_list.append(
                        {
                            "score": score,
                            "musicId": music_id,
                            "difficultId": difficult_id,
                            "romVersionCode": "2000001",
                        }
                    )
                base.handle_upsert_user_all_api_request(
                    {
                        "userId": tmp["user"],
                        "upsertUserAll": {"userRecentRatingList": rating_list},
                    }
                )

                self.logger.info(
                    f"Imported {version_str} userRecentRating: {tmp['user']}"
                )

        result, datetime_columns = self.parse_aqua_db("chusan_user_activity")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )
            tmp["id"] = tmp["activityId"]
            tmp.pop("activityId")

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userActivityList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userActivity: {tmp['activityId']}"
            )

        result, datetime_columns = self.parse_aqua_db("chusan_user_character")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userCharacterList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userCharacter: {tmp['characterId']}"
            )

        result, datetime_columns = self.parse_aqua_db("chusan_user_course")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userCourseList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userCourse: {tmp['courseId']}")

        result, datetime_columns = self.parse_aqua_db("chusan_user_duel")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userDuelList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userDuel: {tmp['duelId']}")

        result, datetime_columns = self.parse_aqua_db("chusan_user_item")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userItemList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userItem: {tmp['itemId']}")

        result, datetime_columns = self.parse_aqua_db("chusan_user_map_area")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userMapAreaList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userMapArea: {tmp['mapAreaId']}")

        result, datetime_columns = self.parse_aqua_db("chusan_user_music_detail")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userMusicDetailList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userMusicDetail: {tmp['musicId']}"
            )

        result, datetime_columns = self.parse_aqua_db("chusan_user_playlog")
        for row in result:
            user = self.get_chuni_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userPlaylogList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userPlaylog: {tmp['musicId']}")

    def get_ongeki_card_id_by_aqua_row(self, row: Row, user_id_column: str = "user_id"):
        aqua_user_id = row._asdict()[user_id_column]
        user_result = self.aqua.execute(
            f"SELECT * FROM ongeki_user_data WHERE id = {aqua_user_id}"
        )

        # could never be None undless something is really fucked up
        user_data = None
        for user in user_result:
            user_data = user._asdict()

        card_id = user_data["aime_card_id"]

        return card_id

    def import_ongeki(self):
        game_cfg = OngekiConfig()
        game_cfg.update(yaml.safe_load(open(f"{self.config_folder}/ongeki.yaml")))

        base = OngekiBrightMemory(self.config, game_cfg)
        version_str = OngekiConstants.game_ver_to_string(base.version)

        answer = input(
            f"Do you really want to import ALL {version_str} data into ARTEMiS? [N/y]: "
        )
        if answer.lower() != "y":
            self.logger.info("User aborted operation")
            return

        result, datetime_columns = self.parse_aqua_db("ongeki_user_data")
        for row in result:
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id", "aimeCardId"],
                card_id=row._asdict()["aime_card_id"],
            )
            # useless but required
            tmp["accessCode"] = ""

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userData": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userData: {tmp['user']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_option")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )
            tmp.pop("dispbp")

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userOption": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userOption: {tmp['user']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_general_data")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            if tmp["propertyKey"] == "recent_rating_list":
                rating_list = []
                for rating in tmp["propertyValue"].split(","):
                    music_id, difficult_id, score = rating.split(":")
                    rating_list.append(
                        {
                            "score": score,
                            "musicId": music_id,
                            "difficultId": difficult_id,
                            "romVersionCode": "1000000",
                        }
                    )
                base.handle_upsert_user_all_api_request(
                    {
                        "userId": tmp["user"],
                        "upsertUserAll": {"userRecentRatingList": rating_list},
                    }
                )

                self.logger.info(
                    f"Imported {version_str} userRecentRating: {tmp['user']}"
                )

        result, datetime_columns = self.parse_aqua_db("ongeki_user_deck")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userDeckList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userDeck: {tmp['deckId']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_activity")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )
            tmp["id"] = tmp["activityId"]
            tmp.pop("activityId")

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userActivityList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userActivity: {tmp['id']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_card")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userCardList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userCard: {tmp['cardId']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_chapter")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userChapterList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userChapter: {tmp['chapterId']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_character")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userCharacterList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userCharacter: {tmp['characterId']}"
            )

        result, datetime_columns = self.parse_aqua_db("ongeki_user_deck")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userDeckList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userDeck: {tmp['deckId']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_item")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userItemList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userItem: {tmp['itemId']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_item")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userItemList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userItem: {tmp['itemId']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_memory_chapter")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {
                    "userId": tmp["user"],
                    "upsertUserAll": {"userMemoryChapterList": [tmp]},
                }
            )

            self.logger.info(
                f"Imported {version_str} userMemoryChapter: {tmp['chapterId']}"
            )

        result, datetime_columns = self.parse_aqua_db("ongeki_user_mission_point")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {
                    "userId": tmp["user"],
                    "upsertUserAll": {"userMissionPointList": [tmp]},
                }
            )

            self.logger.info(
                f"Imported {version_str} userMissionPoint: {tmp['eventId']}"
            )

        result, datetime_columns = self.parse_aqua_db("ongeki_user_music_detail")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userMusicDetailList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userMusicDetail: {tmp['musicId']}"
            )

        result, datetime_columns = self.parse_aqua_db("ongeki_user_playlog")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userPlaylogList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userPlaylog: {tmp['musicId']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_story")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userStoryList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userStory: {tmp['storyId']}")

        result, datetime_columns = self.parse_aqua_db("ongeki_user_tech_count")
        for row in result:
            user = self.get_ongeki_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userTechCountList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userTechCount: {tmp['levelId']}")

    def get_mai2_card_id_by_aqua_row(self, row: Row, user_id_column: str = "user_id"):
        aqua_user_id = row._asdict()[user_id_column]
        user_result = self.aqua.execute(
            f"SELECT * FROM maimai2_user_detail WHERE id = {aqua_user_id}"
        )

        # could never be None undless something is really fucked up
        user_data = None
        for user in user_result:
            user_data = user._asdict()

        card_id = user_data["aime_card_id"]

        return card_id

    def get_mai2_rating_lists_by_aqua_row(self, row: Row, user_id_column: str = "id"):
        aqua_user_id = row._asdict()[user_id_column]
        user_general_data_result = self.aqua.execute(
            f"SELECT * FROM maimai2_user_general_data WHERE user_id = {aqua_user_id}"
        )

        ratings = {}
        for row in user_general_data_result:
            row = row._asdict()
            propery_key = row["property_key"]
            property_value: str = row["property_value"]

            ratings[propery_key] = []
            if property_value == "":
                continue

            for rating_str in property_value.split(","):
                (
                    music_id_str,
                    level_str,
                    romVersion_str,
                    achievement_str,
                ) = rating_str.split(":")
                ratings[propery_key].append(
                    {
                        "musicId": int(music_id_str),
                        "level": int(level_str),
                        "romVersion": int(romVersion_str),
                        "achievement": int(achievement_str),
                    }
                )

        user_udemae_result = self.aqua.execute(
            f"SELECT * FROM maimai2_user_udemae WHERE user_id = {aqua_user_id}"
        )
        for user_udeame_row in user_udemae_result:
            user_udeame = user_udeame_row._asdict()

        user_udeame.pop("id")
        user_udeame.pop("user_id")

        udemae = {inflection.camelize(k, False): v for k, v in user_udeame.items()}

        return (
            ratings["recent_rating"],
            ratings["recent_rating_new"],
            ratings["recent_rating_next"],
            ratings["recent_rating_next_new"],
            udemae,
        )

    def import_mai2(self):
        game_cfg = Mai2Config()
        game_cfg.update(yaml.safe_load(open(f"{self.config_folder}/mai2.yaml")))

        base = Mai2Festival(self.config, game_cfg)
        version_str = Mai2Constants.game_ver_to_string(base.version)

        answer = input(
            f"Do you really want to import ALL {version_str} data into ARTEMiS? [N/y]: "
        )
        if answer.lower() != "y":
            self.logger.info("User aborted operation")
            return

        # maimai2_user_detail -> userData
        result, datetime_columns = self.parse_aqua_db("maimai2_user_detail")
        for row in result:
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id", "aimeCardId"],
                card_id=row._asdict()["aime_card_id"],
            )

            # useless but required
            tmp["accessCode"] = ""
            # camel case conversion fix
            tmp["lastSelectEMoney"] = tmp.pop("lastSelectemoney")

            # convert charaSlot and charaLockSlot
            # "0;0;0;0;0" to [0, 0, 0, 0, 0]
            tmp["charaSlot"] = [int(x) for x in tmp["charaSlot"].split(";")]
            tmp["charaLockSlot"] = [int(x) for x in tmp["charaLockSlot"].split(";")]

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userData": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userData: {tmp['user']}")

            # ! Here we insert user rating list

            rating = tmp["playerRating"]
            (
                rating_list,
                new_rating_list,
                next_rating_list,
                next_new_rating_list,
                udemae,
            ) = self.get_mai2_rating_lists_by_aqua_row(row)

            base.handle_upsert_user_all_api_request(
                {
                    "userId": tmp["user"],
                    "upsertUserAll": {
                        "userRatingList": [
                            {
                                "rating": rating,
                                "ratingList": rating_list,
                                "newRatingList": new_rating_list,
                                "nextRatingList": next_rating_list,
                                "nextNewRatingList": next_new_rating_list,
                                "udemae": udemae,
                            }
                        ]
                    },
                }
            )

        # maimai2_user_playlog -> userPlaylogList
        result, datetime_columns = self.parse_aqua_db("maimai2_user_playlog")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=[], card_id=user
            )
            tmp["userId"] = tmp["user"]
            id_ = tmp.pop("id")

            base.handle_upload_user_playlog_api_request(
                {"userId": tmp["user"], "userPlaylog": tmp}
            )

            self.logger.info(f"Imported {version_str} userPlaylog: {id_}")

        # maimai2_user_extend -> userExtend
        result, datetime_columns = self.parse_aqua_db("maimai2_user_extend")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            # convert the str to a list, so it matches the JSON schema
            tmp["selectedCardList"] = []

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userExtend": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userExtend: {tmp['user']}")

        # skip userGhost

        # maimai2_user_option -> userOption
        result, datetime_columns = self.parse_aqua_db("maimai2_user_option")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row, datetime_columns, unused_columns=["id"], card_id=user
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userOption": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userOption: {tmp['user']}")

        # maimai2_user_activity -> userActivityList
        result, datetime_columns = self.parse_aqua_db("maimai2_user_activity")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                # we do need the id column cuz aqua always sets activityId to 1
                # and in artemis, activityId will be set to the value of id and id will be dropped
                unused_columns=[],
                card_id=user,
            )

            # using raw operation because wtf
            base.data.profile.put_profile_activity(tmp["user"], tmp)

            self.logger.info(
                f"Imported {version_str} userActivity: {tmp['user']}, {tmp['activityId']}"
            )

        # maimai2_user_charge -> userChargeList
        # untested
        result, datetime_columns = self.parse_aqua_db("maimai2_user_charge")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userChargeList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userCharge: {tmp['user']}, {tmp['chargeId']}"
            )

        # maimai2_user_character -> userCharacterList
        result, datetime_columns = self.parse_aqua_db("maimai2_user_character")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )

            tmp["point"] = 0

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userCharacterList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userCharacter: {tmp['user']}, {tmp['characterId']}"
            )

        # maimai2_user_item -> userItemList
        result, datetime_columns = self.parse_aqua_db("maimai2_user_item")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userItemList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userItem: {tmp['user']}, {tmp['itemKind']},{tmp['itemId']}"
            )

        # maimai2_user_login_bonus -> userLoginBonusList
        result, datetime_columns = self.parse_aqua_db("maimai2_user_login_bonus")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userLoginBonusList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userLoginBonus: {tmp['user']}, {tmp['bonusId']}"
            )

        # maimai2_user_map -> userMapList
        result, datetime_columns = self.parse_aqua_db("maimai2_user_map")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userMapList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userMap: {tmp['user']}, {tmp['mapId']}"
            )

        # maimai2_User_music_detail -> userMusicDetailList
        result, datetime_columns = self.parse_aqua_db("maimai2_user_music_detail")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userMusicDetailList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userMusicDetail: {tmp['user']}, {tmp['musicId']}"
            )

        # maimai2_user_course -> userCourseList
        result, datetime_columns = self.parse_aqua_db("maimai2_user_course")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userCourseList": [tmp]}}
            )

            self.logger.info(
                f"Imported {version_str} userCourse: {tmp['user']}, {tmp['courseId']}"
            )

        # maimai2_user_favorite -> userFavoriteList
        # untested
        result, datetime_columns = self.parse_aqua_db("maimai2_user_favorite")
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )

            tmp = {
                "user": tmp["user"],
                "kind": tmp["itemKind"],
                "itemIdList": tmp["itemIdList"],
            }

            base.handle_upsert_user_all_api_request(
                {"userId": tmp["user"], "upsertUserAll": {"userFavoriteList": [tmp]}}
            )

            self.logger.info(f"Imported {version_str} userFavorite: {tmp['user']}")

        # maimai2_user_friend_season_ranking -> userFriendSeasonRankingList
        result, datetime_columns = self.parse_aqua_db(
            "maimai2_user_friend_season_ranking"
        )
        for row in result:
            user = self.get_mai2_card_id_by_aqua_row(row)
            tmp = self.parse_aqua_row(
                row,
                datetime_columns,
                unused_columns=["id"],
                card_id=user,
            )
            # user is redundant
            artemis_user = tmp.pop("user")

            base.handle_upsert_user_all_api_request(
                {
                    "userId": artemis_user,
                    "upsertUserAll": {"userFriendSeasonRankingList": [tmp]},
                }
            )

            self.logger.info(
                f"Imported {version_str} userFriendSeasonRanking: {artemis_user}, {tmp['seasonId']}"
            )


def main():
    parser = argparse.ArgumentParser(description="AQUA to ARTEMiS")
    parser.add_argument(
        "--config", "-c", type=str, help="Config directory to use", default="config"
    )
    parser.add_argument(
        "aqua_folder_path",
        type=str,
        help="Absolute folder path to AQUA folder, where application.properties is located in.",
    )
    args = parser.parse_args()

    core_cfg = CoreConfig()
    core_cfg.update(yaml.safe_load(open(f"{args.config}/core.yaml")))

    importer = Importer(core_cfg, args.config, args.aqua_folder_path)

    importer.import_chuni()
    importer.import_ongeki()
    importer.import_mai2()


if __name__ == "__main__":
    main()
