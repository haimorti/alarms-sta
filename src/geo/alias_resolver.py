from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ResolvedLocation:
    raw_name: str
    normalized_name: str | None
    matched_by_alias: bool
    is_known_missing: bool


class AliasResolver:
    def __init__(self, aliases: dict[str, str]) -> None:
        self.aliases = aliases

    @classmethod
    def from_json(cls, path: Path) -> "AliasResolver":
        aliases = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return cls(aliases=aliases)

    def resolve(self, raw_name: str) -> ResolvedLocation:
        cleaned = raw_name.strip()
        if cleaned in self.aliases:
            alias_target = self.aliases[cleaned].strip()
            return ResolvedLocation(
                raw_name=raw_name,
                normalized_name=alias_target or None,
                matched_by_alias=True,
                is_known_missing=alias_target == "",
            )
        return ResolvedLocation(
            raw_name=raw_name,
            normalized_name=cleaned,
            matched_by_alias=False,
            is_known_missing=False,
        )
