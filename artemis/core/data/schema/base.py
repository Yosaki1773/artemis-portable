import asyncio
import json
import logging
from random import randrange
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, MetaData, Table
from sqlalchemy.engine import Row
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, text
from sqlalchemy.types import INTEGER, JSON, TEXT, TIMESTAMP, Integer, String

from core.config import CoreConfig

metadata = MetaData()

event_log: Table = Table(
    "event_log",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("system", String(255), nullable=False),
    Column("type", String(255), nullable=False),
    Column("severity", Integer, nullable=False),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade")),
    Column("arcade", INTEGER, ForeignKey("arcade.id", ondelete="cascade", onupdate="cascade")),
    Column("machine", INTEGER, ForeignKey("machine.id", ondelete="cascade", onupdate="cascade")),
    Column("ip", TEXT(39)),
    Column("game", TEXT(4)),
    Column("version", TEXT(24)),
    Column("message", String(1000), nullable=False),
    Column("details", JSON, nullable=False),
    Column("when_logged", TIMESTAMP, nullable=False, server_default=func.now()),
    mysql_charset="utf8mb4",
)


class BaseData:
    def __init__(self, cfg: CoreConfig, conn: "sessionmaker[AsyncSession]") -> None:
        self.config = cfg
        self.conn = conn
        self.logger = logging.getLogger("database")

    async def execute(self, sql: str, opts: Dict[str, Any] = {}) -> Optional[CursorResult]:
        res = None

        async with self.conn() as session:
            try:
                self.logger.debug(f"SQL Execute: {''.join(str(sql).splitlines())}")
                res = await session.execute(text(sql), opts)

            except SQLAlchemyError as e:
                self.logger.error(f"SQLAlchemy error {e}")
                return None

            except UnicodeEncodeError as e:
                self.logger.error(f"UnicodeEncodeError error {e}")
                return None

            except Exception:
                try:
                    res = await session.execute(sql, opts)

                except SQLAlchemyError as e:
                    self.logger.error(f"SQLAlchemy error {e}")
                    return None

                except UnicodeEncodeError as e:
                    self.logger.error(f"UnicodeEncodeError error {e}")
                    return None

                except Exception:
                    self.logger.error(f"Unknown error")
                    raise

        return res

    def generate_id(self) -> int:
        """
        Generate a random 5-7 digit id
        """
        return randrange(10000, 9999999)

    async def log_event(
        self, system: str, type: str, severity: int, message: str, details: Dict = {}, user: int = None, 
        arcade: int = None, machine: int = None, ip: Optional[str] = None, game: Optional[str] = None, version: Optional[str] = None
    ) -> Optional[int]:
        sql = event_log.insert().values(
            system=system,
            type=type,
            severity=severity,
            user=user,
            arcade=arcade,
            machine=machine,
            ip=ip,
            game=game,
            version=version,
            message=message,
            details=json.dumps(details),
        )
        result = await self.execute(sql)

        if result is None:
            self.logger.error(
                f"{__name__}: Failed to insert event into event log! system = {system}, type = {type}, severity = {severity}, message = {message}"
            )
            return None

        return result.lastrowid

    async def get_event_log(self, entries: int = 100) -> Optional[List[Row]]:
        sql = event_log.select().order_by(event_log.c.id.desc()).limit(entries)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    def fix_bools(self, data: Dict) -> Dict:
        for k, v in data.items():
            if k == "userName" or k == "teamName":
                continue
            if type(v) == str and v.lower() == "true":
                data[k] = True
            elif type(v) == str and v.lower() == "false":
                data[k] = False

        return data
