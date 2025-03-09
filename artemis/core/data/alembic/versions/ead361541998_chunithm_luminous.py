"""CHUNITHM Luminous

Revision ID: ead361541998
Revises: d8950c7ce2fc
Create Date: 2024-03-05 08:39:14.630558

"""

from alembic import op
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.types import Boolean, Integer

# revision identifiers, used by Alembic.
revision = "ead361541998"
down_revision = "d8950c7ce2fc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chuni_profile_net_battle",
        Column("id", Integer, primary_key=True, nullable=False),
        Column("user", Integer, nullable=False),
        Column("isRankUpChallengeFailed", Boolean),
        Column("highestBattleRankId", Integer),
        Column("battleIconId", Integer),
        Column("battleIconNum", Integer),
        Column("avatarEffectPoint", Integer),
        mysql_charset="utf8mb4",
    )
    op.create_foreign_key(
        None,
        "chuni_profile_net_battle",
        "aime_user",
        ["user"],
        ["id"],
        ondelete="cascade",
        onupdate="cascade",
    )

    op.create_table(
        "chuni_item_cmission",
        Column("id", Integer, primary_key=True, nullable=False),
        Column("user", Integer, nullable=False),
        Column("missionId", Integer, nullable=False),
        Column("point", Integer),
        UniqueConstraint("user", "missionId", name="chuni_item_cmission_uk"),
        mysql_charset="utf8mb4",
    )
    op.create_foreign_key(
        None,
        "chuni_item_cmission",
        "aime_user",
        ["user"],
        ["id"],
        ondelete="cascade",
        onupdate="cascade",
    )

    op.create_table(
        "chuni_item_cmission_progress",
        Column("id", Integer, primary_key=True, nullable=False),
        Column("user", Integer, nullable=False),
        Column("missionId", Integer, nullable=False),
        Column("order", Integer),
        Column("stage", Integer),
        Column("progress", Integer),
        UniqueConstraint(
            "user", "missionId", "order", name="chuni_item_cmission_progress_uk"
        ),
        mysql_charset="utf8mb4",
    )
    op.create_foreign_key(
        None,
        "chuni_item_cmission_progress",
        "aime_user",
        ["user"],
        ["id"],
        ondelete="cascade",
        onupdate="cascade",
    )


def downgrade():
    op.drop_table("chuni_profile_net_battle")
    op.drop_table("chuni_item_cmission")
    op.drop_table("chuni_item_cmission_progress")
