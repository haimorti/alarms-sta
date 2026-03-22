from __future__ import annotations

import re
import unicodedata

DASH_TRANSLATION = str.maketrans({
    '־': '-',
    '–': '-',
    '—': '-',
    '‑': '-',
    '‒': '-',
    '/': ' ',
    '\\': ' ',
    '"': ' ',
    "'": ' ',
    '׳': ' ',
    '״': ' ',
    '(': ' ',
    ')': ' ',
})


PREFIX_VARIANTS: tuple[tuple[str, str], ...] = (
    ('חוות', 'חוה'),
    ('אזור תעשייה', 'א"ת'),
    ('אזור תעשיה', 'א"ת'),
)


def normalize_location_name(value: str) -> str:
    text = unicodedata.normalize('NFKC', value).strip()
    text = text.translate(DASH_TRANSLATION)
    text = re.sub(r'\s*-\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def compact_location_name(value: str) -> str:
    normalized = normalize_location_name(value)
    return re.sub(r'[\s\-]+', '', normalized)


def alias_variants(value: str) -> set[str]:
    normalized = normalize_location_name(value)
    if not normalized:
        return set()

    variants = {
        value.strip(),
        normalized,
        normalized.replace(' - ', '-'),
        normalized.replace(' ', '-'),
        normalized.replace('-', ' '),
        compact_location_name(normalized),
    }

    for source_prefix, target_prefix in PREFIX_VARIANTS:
        if normalized.startswith(source_prefix):
            suffix = normalized[len(source_prefix):].strip()
            if suffix:
                variants.add(f'{target_prefix} {suffix}'.strip())

    return {variant.strip() for variant in variants if variant and variant.strip()}
