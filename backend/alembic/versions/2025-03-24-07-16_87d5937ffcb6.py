"""empty message

Revision ID: 87d5937ffcb6
Revises: 
Create Date: 2025-03-24 07:16:04.988369

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = '87d5937ffcb6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm") 
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Source',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_Source_id'), 'Source', ['id'], unique=False)
    op.create_index(op.f('ix_Source_name'), 'Source', ['name'], unique=False)
    op.create_table('ProcessedUrls',
    sa.Column('url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('source_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['source_id'], ['Source.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ProcessedUrls_hash'), 'ProcessedUrls', ['hash'], unique=False)
    op.create_index(op.f('ix_ProcessedUrls_id'), 'ProcessedUrls', ['id'], unique=False)
    op.create_index(op.f('ix_ProcessedUrls_url'), 'ProcessedUrls', ['url'], unique=False)
    op.create_table('TextData',
    sa.Column('text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('elastic_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('processed_urls_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['processed_urls_id'], ['ProcessedUrls.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_TextData_id'), 'TextData', ['id'], unique=False)
    op.create_index(op.f('ix_TextData_text'), 'TextData', ['text'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_TextData_text'), table_name='TextData')
    op.drop_index(op.f('ix_TextData_id'), table_name='TextData')
    op.drop_table('TextData')
    op.drop_index(op.f('ix_ProcessedUrls_url'), table_name='ProcessedUrls')
    op.drop_index(op.f('ix_ProcessedUrls_id'), table_name='ProcessedUrls')
    op.drop_index(op.f('ix_ProcessedUrls_hash'), table_name='ProcessedUrls')
    op.drop_table('ProcessedUrls')
    op.drop_index(op.f('ix_Source_name'), table_name='Source')
    op.drop_index(op.f('ix_Source_id'), table_name='Source')
    op.drop_table('Source')
    # ### end Alembic commands ###
