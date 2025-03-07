"""Recipe table update

Revision ID: 92a1d73bc13f
Revises: 89e53d1fc24f
Create Date: 2024-09-30 10:00:30.999254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92a1d73bc13f'
down_revision = '89e53d1fc24f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recipe_url', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('dietary_info', sa.Text(), nullable=True))
        batch_op.drop_column('url')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('url', sa.VARCHAR(length=200), nullable=True))
        batch_op.drop_column('dietary_info')
        batch_op.drop_column('recipe_url')

    # ### end Alembic commands ###
