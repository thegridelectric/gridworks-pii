"""The baseline migration and the models agree."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from gwpii.db.models import Base


def test_models_match_migration(engine):
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"include_schemas": True})
        diff = compare_metadata(ctx, Base.metadata)
    assert diff == []
