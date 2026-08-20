"""create users table

Revision ID: 68de50ee3071
Revises: 
Create Date: 2026-08-20 10:17:10.183487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68de50ee3071'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('email', sa.String(200), nullable=False),
        sa.Column('password', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('mfa_enabled', sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column('mfa_secret', sa.String(200), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('users')
