"""Add model mse and r2 to crop

Revision ID: 4586d4950019
Revises: a52220c4b05b
Create Date: 2024-07-10 11:48:42.394691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '4586d4950019'
down_revision: Union[str, None] = 'a52220c4b05b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('crop', sa.Column('crop_yield_model', sa.LargeBinary(), nullable=True))
    op.add_column('crop', sa.Column('mse', sa.Float(), nullable=True))
    op.add_column('crop', sa.Column('r2', sa.Float(), nullable=True))
    op.drop_constraint('crop_name_key', 'crop', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('crop_name_key', 'crop', ['name'])
    op.drop_column('crop', 'r2')
    op.drop_column('crop', 'mse')
    op.drop_column('crop', 'crop_yield_model')
    # ### end Alembic commands ###