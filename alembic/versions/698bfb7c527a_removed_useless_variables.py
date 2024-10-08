"""Removed useless variables

Revision ID: 698bfb7c527a
Revises: 5579f5ee1e9f
Create Date: 2024-06-10 11:25:36.981537

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = "698bfb7c527a"
down_revision: Union[str, None] = "5579f5ee1e9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("past_climate_data", "surface_net_solar_radiation")
    op.drop_column("past_climate_data", "dewpoint_temperature_2m")
    op.drop_column("past_climate_data", "surface_net_thermal_radiation")
    op.drop_column("past_climate_data", "snowfall")
    op.drop_column("past_climate_data", "total_cloud_cover")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "past_climate_data",
        sa.Column(
            "total_cloud_cover",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "past_climate_data",
        sa.Column(
            "snowfall",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "past_climate_data",
        sa.Column(
            "surface_net_thermal_radiation",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "past_climate_data",
        sa.Column(
            "dewpoint_temperature_2m",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "past_climate_data",
        sa.Column(
            "surface_net_solar_radiation",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
    )
    # ### end Alembic commands ###
