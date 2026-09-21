"""Text helpers shared across apps: part-number normalization and Ukrainian slugs."""

import re

_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-\.]*[A-Za-z0-9]|[A-Za-z0-9]")
_YEAR = re.compile(r"^(19|20)\d{2}$")
_YEAR_RANGE = re.compile(r"^(19|20)\d{2}-((19|20)\d{2})?$")

# Official Ukrainian transliteration (КМУ 2010) + a few Russian letters found in legacy data.
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ie",
    "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ь": "", "ю": "iu",
    "я": "ia", "'": "", "’": "", "ʼ": "",
    "ы": "y", "э": "e", "ё": "io", "ъ": "",
}
_WORD_START = {"є": "ye", "ї": "yi", "й": "y", "ю": "yu", "я": "ya"}


def normalize_part_number(raw: str) -> str:
    """Uppercase and drop everything except A–Z and 0–9: ' 5619 41005-d ' -> '561941005D'."""
    return _NON_ALNUM.sub("", (raw or "").upper())


def transliterate_uk(text: str) -> str:
    out: list[str] = []
    prev_is_letter = False
    for ch in text:
        low = ch.lower()
        if low in _TRANSLIT:
            mapped = _WORD_START[low] if (not prev_is_letter and low in _WORD_START) else _TRANSLIT[low]
            out.append(mapped)
            prev_is_letter = True
        else:
            out.append(low)
            prev_is_letter = ch.isalpha()
    return "".join(out)


def slugify_uk(text: str) -> str:
    """'Фари передні' -> 'fary-peredni'; Latin text is kept, everything else becomes dashes."""
    latin = transliterate_uk(text or "")
    return re.sub(r"[^a-z0-9]+", "-", latin).strip("-")


def _looks_like_part_number(token: str) -> bool:
    if _YEAR.match(token) or _YEAR_RANGE.match(token):
        return False
    normalized = normalize_part_number(token)
    return len(normalized) >= 5 and any(c.isdigit() for c in normalized)


def split_part_numbers(text: str) -> list[str]:
    """Extract part-number-like tokens (>=5 chars, contain a digit, not years) in order, deduplicated."""
    seen: dict[str, None] = {}
    for token in _TOKEN.findall(text or ""):
        if _looks_like_part_number(token):
            seen.setdefault(normalize_part_number(token), None)
    return list(seen)


_PHONE_DIGITS = re.compile(r"\D")


def normalize_phone(raw: str) -> str | None:
    """Ukrainian mobile/landline to E.164: '063 420 39 93' / '0634203993' / '+38 (063)…' -> '+380634203993'."""
    digits = _PHONE_DIGITS.sub("", raw or "")
    if len(digits) == 10 and digits.startswith("0"):
        digits = "38" + digits
    elif len(digits) == 9:
        digits = "380" + digits
    if len(digits) == 12 and digits.startswith("380"):
        return "+" + digits
    return None
