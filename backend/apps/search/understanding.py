"""Turn a raw query into intent: VIN, part number, or text with a car / category / side."""

import re
from dataclasses import asdict, dataclass, field
from typing import Literal

from apps.catalog.models import Category
from apps.core.normalize import normalize_part_number

from .car_aliases import get_index

VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
_TOKEN = re.compile(r"[0-9a-zа-яіїєґ][0-9a-zа-яіїєґ\-']*", re.IGNORECASE)
_CYRILLIC = re.compile(r"[а-яіїєґ]", re.IGNORECASE)

# (stems that must all be present, category slug) — most specific first
CATEGORY_RULES: list[tuple[tuple[str, ...], str]] = [
    (("протитум",), "protivotumannye-fary"),
    (("птф",), "protivotumannye-fary"),
    (("поворот",), "ukazateli-povorotov"),
    (("повторювач",), "ukazateli-povorotov"),
    (("ліхтар",), "fonari-zadnie"),
    (("фонар",), "fonari-zadnie"),
    (("стоп",), "fonari-zadnie"),
    (("фар",), "fary-perednie"),
    (("оптик",), "optika"),
    (("амортизатор", "капот"), "amortizatory-kapota-bagazhnika"),
    (("амортизатор", "багажн"), "amortizatory-kapota-bagazhnika"),
    (("кришк", "дзеркал"), "vkladysh-zerkala-zerkalnyj-element"),
    (("вкладиш",), "vkladysh-zerkala"),
    (("дзеркальн", "елемент"), "vkladysh-zerkala"),
    (("кришк", "багажн"), "kryshki-bagazhnika"),
    (("кришк",), "kryshki-bagazhnika"),
    (("багажник",), "kryshki-bagazhnika"),
    (("капот",), "kapoty"),
    (("телевізор",), "panel-radiatora-ustanovochnaya-panel-televizor"),
    (("окуляр",), "panel-radiatora-ustanovochnaya-panel-televizor"),
    (("підсилювач",), "pidsilyuvach-absorber-bampera"),
    (("абсорбер",), "pidsilyuvach-absorber-bampera"),
    (("підкрил",), "pidkrilki-avtomobilni-lokeri"),
    (("локер",), "pidkrilki-avtomobilni-lokeri"),
    (("крил",), "krylya-perednie"),
    (("склопідйомник",), "steklopodemniki"),
    (("двер",), "dveri"),
    (("решітк",), "reshetki-ramki-nakladki"),
    (("решетк",), "reshetki-ramki-nakladki"),
    (("гриль",), "reshetki-ramki-nakladki"),
    (("поріг",), "arki-krylev-porogi-remchasti"),
    (("пороги",), "arki-krylev-porogi-remchasti"),
    (("арк",), "arki-krylev-porogi-remchasti"),
    (("бампер",), "bamper-komplektuyushie"),
    (("захист",), "zashita-dvigatelya-zashita-bampera-plastik"),
    (("підрамник",), "balki-podramniki"),
    (("балк",), "balki-podramniki"),
    (("бачок",), "bachki-rasshiritelnye-i-omyvatelya"),
    (("бачк",), "bachki-rasshiritelnye-i-omyvatelya"),
    (("радіатор", "кондиціонер"), "radiatory-kondicionera"),
    (("конденсер",), "radiatory-kondicionera"),
    (("радіатор", "печ"), "radiatory-pechki"),
    (("радіатор", "пічк"), "radiatory-pechki"),
    (("пічк",), "radiatory-pechki"),
    (("інтеркулер",), "interkuler"),
    (("масля", "радіатор"), "maslyanye-radiatory-teploobmenniki"),
    (("теплообмінник",), "maslyanye-radiatory-teploobmenniki"),
    (("вентилятор",), "ventilyatory-ohlazhdeniya-radiatora"),
    (("дифузор",), "ventilyatory-ohlazhdeniya-radiatora"),
    (("осушувач",), "osushiteli-kondicionera"),
    (("радіатор", "охолод"), "radiatory-ohlazhdeniya"),
    (("радіатор",), "radiatory-avtomobilnye"),
    (("дзеркал",), "zerkala-bokovye"),
    (("зеркал",), "zerkala-bokovye"),
    (("лобов",), "steklo-lobovoe"),
    (("скло", "задн"), "steklo-zadnee"),
    (("скло", "бічн"), "steklo-bokovoe-dver-kuzov"),
    (("скло",), "avtostekla"),
    (("двірник",), "derzhateli-shetki-dvornikov"),
    (("щітк",), "derzhateli-shetki-dvornikov"),
    (("глушник",), "vyhlopna_systema"),
    (("вихлоп",), "vyhlopna_systema"),
    (("резонатор",), "vyhlopna_systema"),
    (("кузов",), "kuzov"),
]

_SIDE_WORDS = {
    "left": ("лів", "left", "лев"),
    "right": ("прав", "right"),
}
_POSITION_WORDS = {"front": ("передн", "front"), "rear": ("задн", "rear")}


@dataclass
class Understood:
    kind: Literal["vin", "part_number", "text", "empty"]
    raw: str
    text: str = ""
    vin: str | None = None
    part_number: str | None = None
    make_id: int | None = None
    model_ids: list[int] = field(default_factory=list)
    generation_ids: list[int] = field(default_factory=list)
    year: int | None = None
    category_id: int | None = None
    side: str | None = None
    position: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def has_filters(self) -> bool:
        return bool(self.make_id or self.model_ids or self.generation_ids or self.category_id or self.side or self.position)


def _is_part_number(q: str) -> str | None:
    if _CYRILLIC.search(q):
        return None
    tokens = q.split()
    if not tokens or len(tokens) > 5:
        return None
    for token in tokens:
        if not any(ch.isdigit() for ch in token) and len(token) > 2:
            return None
    normalized = normalize_part_number(q)
    if len(normalized) < 5 or not re.fullmatch(r"[A-Z0-9]+", normalized):
        return None
    digits = sum(ch.isdigit() for ch in normalized)
    return normalized if digits / len(normalized) >= 0.4 else None


def _match_category(tokens: list[str], consumed: set[int]) -> tuple[int | None, set[int]]:
    for stems, slug in CATEGORY_RULES:
        hits: set[int] = set()
        for stem in stems:
            pos = next((i for i, t in enumerate(tokens) if i not in consumed and t.startswith(stem)), None)
            if pos is None:
                break
            hits.add(pos)
        else:
            category_id = Category.objects.filter(slug=slug, is_active=True).values_list("id", flat=True).first()
            if category_id:
                return category_id, hits
    return None, set()


def _match_word(tokens, consumed, groups) -> tuple[str | None, set[int]]:
    for value, stems in groups.items():
        for pos, token in enumerate(tokens):
            if pos not in consumed and any(token.startswith(s) for s in stems):
                return value, {pos}
    return None, set()


def understand(q: str) -> Understood:
    raw = (q or "").strip()
    if not raw:
        return Understood(kind="empty", raw=raw)

    compact = re.sub(r"[\s\-]", "", raw).upper()
    if VIN_RE.fullmatch(compact) and re.search(r"[A-Z]", compact) and re.search(r"\d", compact):
        return Understood(kind="vin", raw=raw, vin=compact)

    if number := _is_part_number(raw):
        return Understood(kind="part_number", raw=raw, part_number=number, text=raw)

    tokens = [t.lower().strip("-'") for t in _TOKEN.findall(raw)]
    tokens = [t for t in tokens if t]
    consumed: set[int] = set()

    category_id, used = _match_category(tokens, consumed)
    consumed |= used
    car = get_index().match(tokens)
    consumed |= car.consumed
    side, used = _match_word(tokens, consumed, _SIDE_WORDS)
    consumed |= used
    position, used = _match_word(tokens, consumed, _POSITION_WORDS)
    consumed |= used

    return Understood(
        kind="text",
        raw=raw,
        text=" ".join(t for i, t in enumerate(tokens) if i not in consumed),
        make_id=car.make_id,
        model_ids=car.model_ids,
        generation_ids=car.generation_ids,
        year=car.year,
        category_id=category_id,
        side=side,
        position=position,
    )
