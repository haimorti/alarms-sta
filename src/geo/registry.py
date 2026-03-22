from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RegistrySource:
    path: Path
    purpose: str


REGISTRY_SOURCES: tuple[RegistrySource, ...] = (
    RegistrySource(Path("data/coord.csv"), "Primary settlement coordinates seed"),
    RegistrySource(Path("data/location_dictionary.csv"), "Hebrew/English settlement name dictionary"),
    RegistrySource(Path("data/coord_area.csv"), "Known area/polygon fragments for settlements and sublocations"),
    RegistrySource(Path("data/missing_cities.json"), "Alias and unresolved-location normalization hints"),
)
