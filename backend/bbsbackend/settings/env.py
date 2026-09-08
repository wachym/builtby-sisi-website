"""Environment helpers.

Deliberately dependency-free: settings should be readable without learning a
configuration library, and the backend should not grow a dependency for twenty
lines of parsing.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


def load_dotenv(path: Path) -> None:
    """Populate os.environ from a .env file without overriding real env vars.

    Real environment always wins, so a container's secrets are never shadowed
    by a stray file left in the image.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def get(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(
            f"{name} must be set. See backend/.env.example for the contract."
        )
    return value or ""


def get_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    lowered = raw.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean, got {raw!r}.")


def get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - configuration error path
        raise ImproperlyConfigured(f"{name} must be an integer, got {raw!r}.") from exc


def get_list(name: str, default: tuple[str, ...] = ()) -> list[str]:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def database_from_url(url: str, base_dir: Path, *, conn_max_age: int = 0) -> dict:
    """Translate a DATABASE_URL into Django's DATABASES['default'].

    Supports sqlite and postgres, which is all this system needs: sqlite for a
    zero-setup local run, postgres everywhere that matters.
    """
    if not url:
        raise ImproperlyConfigured("DATABASE_URL must be set.")

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme in {"sqlite", "sqlite3"}:
        raw_path = url.split("://", 1)[1] if "://" in url else ""
        raw_path = raw_path.lstrip("/") or "db.sqlite3"
        if raw_path == ":memory:":
            name: str | Path = ":memory:"
        else:
            candidate = Path(raw_path)
            name = candidate if candidate.is_absolute() else base_dir / candidate
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": str(name)}

    if scheme in {"postgres", "postgresql", "psql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")) or "postgres",
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "localhost",
            "PORT": str(parsed.port or 5432),
            "CONN_MAX_AGE": conn_max_age,
            "CONN_HEALTH_CHECKS": bool(conn_max_age),
        }

    raise ImproperlyConfigured(
        f"Unsupported DATABASE_URL scheme {scheme!r}. Use sqlite:// or postgres://."
    )
