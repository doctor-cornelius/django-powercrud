"""Fail fast when PostgreSQL database collation metadata is stale."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main() -> int:
    """Check every recorded PostgreSQL database collation version."""
    django.setup()

    from django.db import connection

    if connection.vendor != "postgresql":
        return 0

    try:
        with connection.cursor() as cursor:
            # template0 intentionally has no recorded version and stays pristine.
            cursor.execute(
                """
                SELECT datname, datcollversion,
                       pg_database_collation_actual_version(oid)
                FROM pg_database
                WHERE datcollversion IS NOT NULL
                  AND datcollversion IS DISTINCT FROM
                      pg_database_collation_actual_version(oid)
                ORDER BY datname
                """
            )
            mismatches = cursor.fetchall()
    except Exception as error:
        print(
            f"Could not check PostgreSQL database collation versions: {error}",
            file=sys.stderr,
        )
        return 2

    if not mismatches:
        return 0

    print("PostgreSQL database collation version mismatch detected:", file=sys.stderr)
    for database, recorded, actual in mismatches:
        print(
            f"  {database}: recorded {recorded}; current OS version {actual}",
            file=sys.stderr,
        )
    print(
        "Back up affected databases. In each one, run REINDEX SYSTEM and "
        "REINDEX DATABASE; then run ALTER DATABASE ... REFRESH COLLATION "
        "VERSION from another database. See "
        "https://www.postgresql.org/docs/16/sql-altercollation.html.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
