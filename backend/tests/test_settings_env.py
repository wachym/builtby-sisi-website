"""The environment contract.

Settings parsing decides which database production talks to and whether the
service starts at all, so it is tested like any other logic.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from bbsbackend.settings import env

BASE = Path("/srv/app")


def test_bool_accepts_the_usual_spellings(monkeypatch):
    for raw in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv("FLAG", raw)
        assert env.get_bool("FLAG") is True
    for raw in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("FLAG", raw)
        assert env.get_bool("FLAG", True) is False


def test_bool_rejects_nonsense(monkeypatch):
    """A typo in a deployment variable must not silently mean False."""
    monkeypatch.setenv("FLAG", "maybe")
    with pytest.raises(ImproperlyConfigured):
        env.get_bool("FLAG")


def test_required_values_fail_loudly(monkeypatch):
    monkeypatch.delenv("MISSING", raising=False)
    with pytest.raises(ImproperlyConfigured):
        env.get("MISSING", required=True)


def test_list_splits_and_trims(monkeypatch):
    monkeypatch.setenv("HOSTS", " api.example.com , example.com ,, ")
    assert env.get_list("HOSTS") == ["api.example.com", "example.com"]


def test_sqlite_relative_path_is_resolved_against_the_project():
    config = env.database_from_url("sqlite:///db.sqlite3", BASE)
    assert config["ENGINE"].endswith("sqlite3")
    assert Path(config["NAME"]) == BASE / "db.sqlite3"


def test_sqlite_absolute_path_is_left_absolute():
    """Four slashes means absolute; three means relative."""
    config = env.database_from_url("sqlite:////var/lib/sisi/db.sqlite3", BASE)
    assert Path(config["NAME"]).as_posix() == "/var/lib/sisi/db.sqlite3"


def test_sqlite_memory():
    assert env.database_from_url("sqlite://:memory:", BASE)["NAME"] == ":memory:"


def test_postgres_url_is_fully_parsed():
    config = env.database_from_url(
        "postgres://sisi:p%40ss@db.internal:6543/sisi_prod", BASE, conn_max_age=60
    )
    assert config["ENGINE"] == "django.db.backends.postgresql"
    assert config["NAME"] == "sisi_prod"
    assert config["USER"] == "sisi"
    assert config["PASSWORD"] == "p@ss"  # percent-encoding is decoded
    assert config["HOST"] == "db.internal"
    assert config["PORT"] == "6543"
    assert config["CONN_MAX_AGE"] == 60
    assert config["CONN_HEALTH_CHECKS"] is True


def test_postgres_defaults_to_5432():
    assert env.database_from_url("postgres://u:p@host/db", BASE)["PORT"] == "5432"


def test_unknown_scheme_is_refused():
    with pytest.raises(ImproperlyConfigured):
        env.database_from_url("mysql://u:p@host/db", BASE)


def test_empty_url_is_refused():
    with pytest.raises(ImproperlyConfigured):
        env.database_from_url("", BASE)
