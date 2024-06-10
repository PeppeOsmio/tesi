"""Add mse

Revision ID: 64cb1184cd43
Revises: d0b6299bfa2e
Create Date: 2024-06-09 17:48:09.134754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '64cb1184cd43'
down_revision: Union[str, None] = 'd0b6299bfa2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('climate_generative_model', sa.Column('mse', sa.Float(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('climate_generative_model', 'mse')
    # ### end Alembic commands ###