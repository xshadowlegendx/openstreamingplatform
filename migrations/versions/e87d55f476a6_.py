"""empty message

Revision ID: e87d55f476a6
Revises: 50bd4a968ad3
Create Date: 2023-12-30 15:00:38.066187

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e87d55f476a6'
down_revision = '50bd4a968ad3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('settings', sa.Column('maxStickerUploadFileSize', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('settings', 'maxStickerUploadFileSize')
    # ### end Alembic commands ###