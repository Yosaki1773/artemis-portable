"""ongeki: fix clearStatus

Revision ID: 8ad40a6e7be2
Revises: 7dc13e364e53
Create Date: 2024-05-29 19:03:30.062157

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '8ad40a6e7be2'
down_revision = '7dc13e364e53'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('ongeki_score_best', 'clearStatus',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Integer(),
               existing_nullable=False)


def downgrade():
    op.alter_column('ongeki_score_best', 'clearStatus',
               existing_type=sa.Integer(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=False)
