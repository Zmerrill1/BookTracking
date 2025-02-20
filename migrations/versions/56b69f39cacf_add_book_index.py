"""empty message

Revision ID: 56b69f39cacf
Revises: 2e3f7780d24b
Create Date: 2025-01-31 13:58:40.760296

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "56b69f39cacf"
down_revision: Union[str, None] = "2e3f7780d24b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "book", sa.Column("bookid", sqlmodel.sql.sqltypes.AutoString(), nullable=False)
    )
    op.create_index(op.f("ix_book_bookid"), "book", ["bookid"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_book_bookid"), table_name="book")
    op.drop_column("book", "bookid")
    # ### end Alembic commands ###
