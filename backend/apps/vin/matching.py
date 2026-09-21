"""Map a decoded VIN onto catalog generations (make -> model family -> years)."""

import re

from apps.catalog.models import CarModel, Generation, Make, Market
from apps.importer.loader import canonical_make_name

from .decoder import VinInfo


def _find_make(name: str | None) -> Make | None:
    if not name:
        return None
    canonical = canonical_make_name(name.title() if name.isupper() else name)
    return (
        Make.objects.filter(name__iexact=canonical).first()
        or Make.objects.filter(name__iexact=name).first()
        or Make.objects.filter(name__icontains=name.split()[0]).first()
    )


def _model_keys(info: VinInfo) -> list[str]:
    keys = []
    for value in (info.model, info.series):
        if value:
            keys.append(value.strip())
            keys.append(re.sub(r"[\s\-]+", " ", value).strip())
            keys.append(value.split()[0])
    return list(dict.fromkeys(k for k in keys if k))


def match_generations(info: VinInfo, limit: int = 3) -> list[Generation]:
    make = _find_make(info.make)
    if not make or not info.model:
        return []
    models = []
    for key in _model_keys(info):
        models = list(
            CarModel.objects.filter(make=make).filter(family__iexact=key)
        ) or list(CarModel.objects.filter(make=make, name__istartswith=key))
        if models:
            break
    if not models:
        return []
    gens = Generation.objects.filter(model__in=models).select_related("model__make")
    if info.year:
        gens = [g for g in gens if g.covers_year(info.year) and (g.year_from or g.year_to)]
    else:
        gens = list(gens)

    def rank(g: Generation):
        market_score = 0
        if info.market == Market.USA:
            market_score = 0 if g.model.market == Market.USA else 1
        elif g.model.market == Market.USA:
            market_score = 1
        span = (g.year_to or 2100) - (g.year_from or 1900)
        return (market_score, span, g.model.name)

    return sorted(gens, key=rank)[:limit]
