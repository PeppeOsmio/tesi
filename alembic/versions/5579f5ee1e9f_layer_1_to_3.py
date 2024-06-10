"""Layer 1 to 3

Revision ID: 5579f5ee1e9f
Revises: 64cb1184cd43
Create Date: 2024-06-10 02:49:02.986982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '5579f5ee1e9f'
down_revision: Union[str, None] = '64cb1184cd43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('past_climate_data', sa.Column('soil_temperature_level_3', sa.Float(), nullable=False, server_default="0.0"))
    op.add_column('past_climate_data', sa.Column('volumetric_soil_water_layer_3', sa.Float(), nullable=False, server_default="0.0"))
    op.drop_column('past_climate_data', 'volumetric_soil_water_layer_1')
    op.drop_column('past_climate_data', 'soil_temperature_level_1')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('past_climate_data', sa.Column('soil_temperature_level_1', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.add_column('past_climate_data', sa.Column('volumetric_soil_water_layer_1', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.drop_column('past_climate_data', 'volumetric_soil_water_layer_3')
    op.drop_column('past_climate_data', 'soil_temperature_level_3')
    # ### end Alembic commands ###