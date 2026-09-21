"""Recognize car makes/models inside free text in Latin or Cyrillic («пасат б7» -> Passat B7)."""

import itertools
import re
import threading
from dataclasses import dataclass, field

from django.db.models import Count, Max

from apps.catalog.models import CarModel, Generation, Make

_DIGRAPHS = [
    ("sch", ["ш"]), ("sh", ["ш"]), ("ch", ["ч"]), ("zh", ["ж"]), ("ts", ["ц"]), ("kh", ["х"]),
    ("ph", ["ф"]), ("th", ["т"]), ("ya", ["я"]), ("yu", ["ю"]), ("yo", ["йо"]), ("ee", ["і"]),
    ("oo", ["у"]), ("ou", ["у"]), ("ck", ["к"]), ("qu", ["кв"]),
]
_SINGLE = {
    "a": ["а"], "b": ["б"], "d": ["д"], "e": ["е"], "f": ["ф"], "g": ["г"], "h": ["х"], "i": ["і", "и"],
    "j": ["дж"], "k": ["к"], "l": ["л"], "m": ["м"], "n": ["н"], "o": ["о"], "p": ["п"], "q": ["к"],
    "r": ["р"], "s": ["с"], "t": ["т"], "u": ["у"], "v": ["в"], "w": ["в"], "x": ["кс"], "z": ["з"],
}
_VOWELS = set("aeiouy")
_MAX_VARIANTS = 12

# Cyrillic letters people type inside model codes («б7», «в124», «е90»)
_CODE_MAP = {
    "а": ["a"], "б": ["b"], "в": ["v", "w", "b"], "г": ["g"], "д": ["d"], "е": ["e"], "є": ["e"], "ж": ["zh"],
    "з": ["z"], "и": ["i", "y"], "і": ["i"], "ї": ["i"], "й": ["y"], "к": ["k"], "л": ["l"], "м": ["m"],
    "н": ["n", "h"], "о": ["o"], "п": ["p"], "р": ["r", "p"], "с": ["s", "c"], "т": ["t"], "у": ["u", "y"],
    "ф": ["f"], "х": ["x", "h"], "ц": ["c"], "ч": ["ch"], "ш": ["sh"], "щ": ["sch"], "ю": ["yu"], "я": ["ya"],
    "ь": [""], "ы": ["y"], "э": ["e"],
}


def translit_variants(word: str) -> set[str]:
    """Plausible Cyrillic spellings of a Latin car name: 'passat' -> {'пассат', 'пасат'}."""
    word = word.lower()
    if not word.isascii() or not re.fullmatch(r"[a-z]+", word):
        return set()
    options: list[list[str]] = []
    i = 0
    while i < len(word):
        ch = word[i]
        nxt = word[i + 1] if i + 1 < len(word) else ""
        prev = word[i - 1] if i else ""
        if ch in "aeo" and nxt == "i" and i + 2 == len(word):  # «qashqai» -> «кашкай»
            options.append([_SINGLE[ch][0] + "й"])
            i += 2
            continue
        for dg, repl in _DIGRAPHS:
            if word.startswith(dg, i):
                options.append(repl)
                i += len(dg)
                break
        else:
            if ch == "c":
                options.append(["ц"] if nxt in ("e", "i", "y") else ["к"])
            elif ch == "y":
                if prev in _VOWELS or (not prev and nxt in _VOWELS):
                    options.append(["й"])
                else:
                    options.append(["і", "и"])
            else:
                options.append(_SINGLE.get(ch, [ch]))
            i += 1
    variants = set()
    for combo in itertools.islice(itertools.product(*options), _MAX_VARIANTS):
        spelled = "".join(combo)
        variants.add(spelled)
        variants.add(re.sub(r"(.)\1", r"\1", spelled))  # «пассат» -> «пасат»
    return variants


def code_variants(token: str) -> set[str]:
    """Latin readings of a short model code typed in Cyrillic: 'б7' -> {'b7'}, 'в124' -> {'v124','w124','b124'}."""
    token = token.lower()
    if token.isascii():
        return {token}
    options = [_CODE_MAP.get(ch, [ch]) for ch in token]
    return {"".join(c) for c in itertools.islice(itertools.product(*options), 16)}


@dataclass
class CarMatch:
    make_id: int | None = None
    model_ids: list[int] = field(default_factory=list)
    generation_ids: list[int] = field(default_factory=list)
    year: int | None = None
    consumed: set[int] = field(default_factory=set)  # token positions


@dataclass
class _Model:
    id: int
    make_id: int
    family: str
    tokens: set[str]


class CarAliasIndex:
    def __init__(self):
        self.make_aliases: dict[str, int] = {}
        self.family_aliases: dict[str, set[int]] = {}
        self.models: dict[int, _Model] = {}

    @classmethod
    def build(cls) -> "CarAliasIndex":
        from .models import SearchSynonym

        idx = cls()
        synonyms: dict[str, set[str]] = {}
        for syn in SearchSynonym.objects.filter(is_active=True):
            group = {syn.term.lower(), *syn.synonym_list()}
            for word in group:
                synonyms.setdefault(word, set()).update(group)

        def aliases(name: str) -> set[str]:
            low = name.lower()
            result = {low, low.replace("-", ""), low.replace("-", " ")}
            result |= translit_variants(low.replace("-", ""))
            result |= synonyms.get(low, set())
            return {a for a in result if a}

        for make in Make.objects.all():
            for alias in aliases(make.name):
                idx.make_aliases[alias] = make.id
        for model in CarModel.objects.all():
            family = (model.family or model.name).lower()
            idx.models[model.id] = _Model(model.id, model.make_id, family, set(re.split(r"[\s\-()/]+", model.name.lower())))
            for alias in aliases(family):
                idx.family_aliases.setdefault(alias, set()).add(model.id)
        return idx

    def match(self, tokens: list[str]) -> CarMatch:
        result = CarMatch()
        # makes
        for pos, token in enumerate(tokens):
            if token in self.make_aliases:
                result.make_id = self.make_aliases[token]
                result.consumed.add(pos)
                break
        # families (single words and two-word names like «grand vitara»)
        candidates: set[int] = set()
        for size in (2, 1):
            for pos in range(len(tokens) - size + 1):
                span = set(range(pos, pos + size))
                if span & result.consumed:
                    continue
                phrase = " ".join(tokens[pos : pos + size])
                ids = self.family_aliases.get(phrase)
                if ids and not result.make_id and (phrase.isdigit() or len(phrase) <= 2):
                    continue  # «3», «6», «x5» are only model names once the make is known
                if ids:
                    if result.make_id:
                        ids = {i for i in ids if self.models[i].make_id == result.make_id}
                    if ids:
                        candidates |= ids
                        result.consumed |= span
            if candidates:
                break
        if candidates and not result.make_id:
            makes = {self.models[i].make_id for i in candidates}
            if len(makes) == 1:
                result.make_id = makes.pop()
        # narrow by model codes: «b7», «usa», «70»
        for pos, token in enumerate(tokens):
            if pos in result.consumed or not candidates or _YEAR.fullmatch(token):
                continue
            readings = code_variants(token)
            narrowed = {i for i in candidates if readings & (self.models[i].tokens - {self.models[i].family})}
            if narrowed:
                candidates = narrowed
                result.consumed.add(pos)
        result.model_ids = sorted(candidates)
        # years
        for pos, token in enumerate(tokens):
            if pos not in result.consumed and _YEAR.fullmatch(token) and 1980 <= int(token) <= 2035:
                result.year = int(token)
                result.consumed.add(pos)
                gens = Generation.objects.all()
                if result.model_ids:
                    gens = gens.filter(model_id__in=result.model_ids)
                elif result.make_id:
                    gens = gens.filter(model__make_id=result.make_id)
                else:
                    break
                result.generation_ids = sorted(g.id for g in gens if g.covers_year(result.year))
                break
        return result


_YEAR = re.compile(r"(19|20)\d{2}")
_cache_lock = threading.Lock()
_cache: dict[str, object] = {"stamp": None, "index": None}


def _stamp():
    from .models import SearchSynonym

    return (
        Make.objects.aggregate(n=Count("id"), m=Max("id")),
        CarModel.objects.aggregate(n=Count("id"), m=Max("id")),
        SearchSynonym.objects.aggregate(n=Count("id"), m=Max("id")),
    )


def get_index() -> CarAliasIndex:
    stamp = _stamp()
    with _cache_lock:
        if _cache["stamp"] != stamp:
            _cache["index"] = CarAliasIndex.build()
            _cache["stamp"] = stamp
        return _cache["index"]
