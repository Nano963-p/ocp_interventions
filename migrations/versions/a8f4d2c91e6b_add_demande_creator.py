"""add request creator for technician ownership

Revision ID: a8f4d2c91e6b
Revises: 34ef4c51645d
"""
from alembic import op
import sqlalchemy as sa


revision = 'a8f4d2c91e6b'
down_revision = '34ef4c51645d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('demande') as batch_op:
        batch_op.add_column(sa.Column('createur_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_demande_createur_id_user', 'user', ['createur_id'], ['id'])


def downgrade():
    with op.batch_alter_table('demande') as batch_op:
        batch_op.drop_constraint('fk_demande_createur_id_user', type_='foreignkey')
        batch_op.drop_column('createur_id')
