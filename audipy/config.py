"""Configuration for AudiPy — a local, single-user tool.

Everything lives under a single home directory (default ``~/.audipy``), kept
outside the git repo so tokens and the local database are never committed.
Optional overrides come from ``$AUDIPY_HOME/config.toml`` and environment
variables; sensible defaults mean the tool works with zero configuration.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

# Valid Audible marketplaces (locale codes accepted by the `audible` library).
MARKETPLACES = ("us", "uk", "de", "fr", "ca", "au", "in", "it", "es", "jp", "br")


def audipy_home() -> Path:
    """Return the AudiPy home directory, creating it (0700) if needed."""
    home = Path(os.environ.get("AUDIPY_HOME", Path.home() / ".audipy")).expanduser()
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    return home


@dataclass(frozen=True)
class Config:
    """Resolved runtime configuration."""

    home: Path
    marketplace: str = "us"
    # Price threshold for the cash-vs-credit rule: below this, pay cash and save
    # a credit; at or above, a credit is the better value. 12.66 = cost of one
    # credit in a 3-credit bundle.
    max_price: float = 12.66
    language: str = "english"
    # How many of your top authors/narrators/series to generate recommendations
    # from. Kept modest to limit Audible catalog calls per run.
    top_authors: int = 25
    top_narrators: int = 25
    top_series: int = 100

    @property
    def auth_file(self) -> Path:
        """Local Audible token cache (JSON). Never committed; chmod 0600."""
        return self.home / "auth.json"

    @property
    def db_file(self) -> Path:
        """Local SQLite database holding the synced library + recommendations."""
        return self.home / "audipy.db"

    @classmethod
    def load(cls) -> "Config":
        """Build config from defaults, then config.toml, then env overrides."""
        home = audipy_home()
        values: dict = {}

        toml_path = home / "config.toml"
        if toml_path.exists():
            with toml_path.open("rb") as fh:
                values.update(tomllib.load(fh))

        # Environment overrides (highest precedence).
        env_map = {
            "AUDIPY_MARKETPLACE": ("marketplace", str),
            "AUDIPY_MAX_PRICE": ("max_price", float),
            "AUDIPY_LANGUAGE": ("language", str),
        }
        for env_key, (field, caster) in env_map.items():
            if (raw := os.environ.get(env_key)) is not None:
                values[field] = caster(raw)

        # Only keep keys we know about, so a stray config.toml key can't crash us.
        known = {f for f in cls.__dataclass_fields__ if f != "home"}
        clean = {k: v for k, v in values.items() if k in known}

        marketplace = str(clean.get("marketplace", "us")).lower()
        if marketplace not in MARKETPLACES:
            raise ValueError(
                f"Unknown marketplace {marketplace!r}. Valid: {', '.join(MARKETPLACES)}"
            )
        clean["marketplace"] = marketplace

        return cls(home=home, **clean)
