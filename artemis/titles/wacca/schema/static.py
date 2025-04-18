from typing import List, Optional

from core.data.schema import BaseData, metadata
from sqlalchemy import Column, Table, UniqueConstraint, and_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.sql import select
from sqlalchemy.types import Float, Integer, String

music = Table(
    "wacca_static_music",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("songId", Integer),
    Column("chartId", Integer),
    Column("title", String(255)),
    Column("artist", String(255)),
    Column("bpm", String(255)),
    Column("difficulty", Float),
    Column("chartDesigner", String(255)),
    Column("jacketFile", String(255)),
    UniqueConstraint("version", "songId", "chartId", name="wacca_static_music_uk"),
    mysql_charset="utf8mb4",
)


class WaccaStaticData(BaseData):
    async def put_music(
        self,
        version: int,
        song_id: int,
        chart_id: int,
        title: str,
        artist: str,
        bpm: str,
        difficulty: float,
        chart_designer: str,
        jacket: str,
    ) -> Optional[int]:
        sql = insert(music).values(
            version=version,
            songId=song_id,
            chartId=chart_id,
            title=title,
            artist=artist,
            bpm=bpm,
            difficulty=difficulty,
            chartDesigner=chart_designer,
            jacketFile=jacket,
        )

        conflict = sql.on_duplicate_key_update(
            title=title,
            artist=artist,
            bpm=bpm,
            difficulty=difficulty,
            chartDesigner=chart_designer,
            jacketFile=jacket,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert music {song_id} chart {chart_id}")
            return None
        return result.lastrowid

    async def get_music_chart(
        self, version: int, song_id: int, chart_id: int
    ) -> Optional[List[Row]]:
        sql = select(music).where(
            and_(
                music.c.version == version,
                music.c.songId == song_id,
                music.c.chartId == chart_id,
            )
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
