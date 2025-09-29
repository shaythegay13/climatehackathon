"""
Step 3 schema: households, sensor_readings, alerts, health_context

Revision ID: 20250927_01
Revises: 
Create Date: 2025-09-27
"""
from typing import Optional
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func, text

# revision identifiers, used by Alembic.
revision: str = '20250927_01'
down_revision: Optional[str] = None
branch_labels = None
depends_on = None


def _is_sqlite(bind):
    name = bind.dialect.name if bind else None
    return name == 'sqlite'


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = _is_sqlite(bind)

    # households
    op.create_table(
        'households',
        sa.Column('household_id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('zipcode', sa.String(length=10), nullable=False),
        sa.Column('housing_type', sa.String(length=50), nullable=False),
        sa.Column('risk_score', sa.Numeric(5, 2), nullable=False, server_default=text('0.00')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    op.create_index('idx_households_zipcode', 'households', ['zipcode'], unique=False)

    # household_sensor_readings
    op.create_table(
        'household_sensor_readings',
        sa.Column('reading_id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('household_id', sa.BigInteger(), sa.ForeignKey('households.household_id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('pm25', sa.Numeric(6, 2), nullable=True),
        sa.Column('co2', sa.Integer(), nullable=True),
        sa.Column('voc', sa.Numeric(8, 2), nullable=True),
        sa.Column('humidity', sa.Numeric(5, 2), nullable=True),
        sa.Column('mold_flag', sa.Boolean(), nullable=False, server_default=sa.text('0' if is_sqlite else 'FALSE')),
    )
    op.create_index('idx_hh_sensor_readings_household_time', 'household_sensor_readings', ['household_id', 'timestamp'], unique=False)
    op.create_index('idx_hh_sensor_readings_device_time', 'household_sensor_readings', ['device_id', 'timestamp'], unique=False)

    # household_alerts
    op.create_table(
        'household_alerts',
        sa.Column('alert_id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('reading_id', sa.BigInteger(), sa.ForeignKey('household_sensor_readings.reading_id', ondelete='SET NULL'), nullable=True),
        sa.Column('household_id', sa.BigInteger(), sa.ForeignKey('households.household_id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('alert_message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    op.create_index('idx_hh_alerts_household_time', 'household_alerts', ['household_id', 'timestamp'], unique=False)

    # health_context
    op.create_table(
        'health_context',
        sa.Column('zipcode', sa.String(length=10), primary_key=True),
        sa.Column('asthma_rate', sa.Numeric(6, 3), nullable=True),
        sa.Column('er_visit_rate', sa.Numeric(6, 3), nullable=True),
        sa.Column('ej_index', sa.Numeric(6, 3), nullable=True),
    )

    # Trigger for updated_at on households (Postgres only)
    if not is_sqlite:
        op.execute(
            sa.text(
                """
                CREATE OR REPLACE FUNCTION set_households_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS trg_households_updated_at ON households;
                CREATE TRIGGER trg_households_updated_at
                BEFORE UPDATE ON households
                FOR EACH ROW
                EXECUTE PROCEDURE set_households_updated_at();
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = _is_sqlite(bind)

    if not is_sqlite:
        op.execute(sa.text("DROP TRIGGER IF EXISTS trg_households_updated_at ON households;"))
        op.execute(sa.text("DROP FUNCTION IF EXISTS set_households_updated_at();"))

    op.drop_index('idx_hh_alerts_household_time', table_name='household_alerts')
    op.drop_table('household_alerts')

    op.drop_index('idx_hh_sensor_readings_device_time', table_name='household_sensor_readings')
    op.drop_index('idx_hh_sensor_readings_household_time', table_name='household_sensor_readings')
    op.drop_table('household_sensor_readings')

    op.drop_index('idx_households_zipcode', table_name='households')
    op.drop_table('households')

    op.drop_table('health_context')
