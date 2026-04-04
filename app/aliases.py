import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_aliases() -> dict[str, str]:
    path = Path(__file__).resolve().parent / "player_aliases.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_nationalities() -> dict[str, str]:
    path = Path(__file__).resolve().parent / "player_nationalities.json"
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_player_name(name: str) -> str:
    aliases = load_aliases()
    return aliases.get(name, name)
