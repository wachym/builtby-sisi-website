"""Database-level append-only enforcement for ledger_event.

The Python guards in models.py stop application code. These triggers stop
everything else: a psql session, a future migration written in a hurry, an ORM
path nobody anticipated. The ledger's whole claim is that history was not
rewritten, so the guarantee belongs in the database as well as the code.

Note for test authors: because DELETE is blocked, tests must roll back rather
than flush. Django's TestCase (and pytest-django's default `db` fixture) wrap
each test in a transaction and roll back, which is fine. A TransactionTestCase
flushes tables between tests and will fail here — drop the triggers explicitly
in such a test if one is ever genuinely needed.
"""

from django.db import migrations

POSTGRES_FORWARD = """
CREATE OR REPLACE FUNCTION ledger_event_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'ledger_event is append-only: % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ledger_event_no_update
    BEFORE UPDATE ON ledger_event
    FOR EACH ROW EXECUTE FUNCTION ledger_event_append_only();

CREATE TRIGGER ledger_event_no_delete
    BEFORE DELETE ON ledger_event
    FOR EACH ROW EXECUTE FUNCTION ledger_event_append_only();
"""

POSTGRES_REVERSE = """
DROP TRIGGER IF EXISTS ledger_event_no_update ON ledger_event;
DROP TRIGGER IF EXISTS ledger_event_no_delete ON ledger_event;
DROP FUNCTION IF EXISTS ledger_event_append_only();
"""

SQLITE_FORWARD = [
    """
    CREATE TRIGGER ledger_event_no_update
    BEFORE UPDATE ON ledger_event
    BEGIN
        SELECT RAISE(ABORT, 'ledger_event is append-only: UPDATE is not permitted');
    END;
    """,
    """
    CREATE TRIGGER ledger_event_no_delete
    BEFORE DELETE ON ledger_event
    BEGIN
        SELECT RAISE(ABORT, 'ledger_event is append-only: DELETE is not permitted');
    END;
    """,
]

SQLITE_REVERSE = [
    "DROP TRIGGER IF EXISTS ledger_event_no_update;",
    "DROP TRIGGER IF EXISTS ledger_event_no_delete;",
]


def _run(statements, schema_editor):
    for statement in statements:
        schema_editor.execute(statement)


def forwards(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        _run([POSTGRES_FORWARD], schema_editor)
    elif vendor == "sqlite":
        _run(SQLITE_FORWARD, schema_editor)
    # Any other backend is unsupported for the ledger; the Python guards still
    # apply, and prod settings only permit PostgreSQL.


def backwards(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        _run([POSTGRES_REVERSE], schema_editor)
    elif vendor == "sqlite":
        _run(SQLITE_REVERSE, schema_editor)


class Migration(migrations.Migration):
    dependencies = [("ledger", "0001_initial")]

    operations = [migrations.RunPython(forwards, backwards)]
