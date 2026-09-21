"""VIN validation and decoding: check digit, model year, WMI table, NHTSA with cache."""

import re
from dataclasses import asdict, dataclass, field
from datetime import date

from . import nhtsa
from .models import VinDecodeCache, Wmi

VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
_TRANSLIT = {
    **{str(d): d for d in range(10)},
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}
_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"  # 1980..2009, then the cycle repeats
_COUNTRY_BY_PREFIX = {
    "1": "США", "4": "США", "5": "США", "2": "Канада", "3": "Мексика", "J": "Японія", "K": "Південна Корея",
    "L": "Китай", "W": "Німеччина", "Z": "Італія", "S": "Велика Британія", "Y": "Швеція / Фінляндія",
    "X": "Росія / СНД", "U": "Румунія", "9": "Бразилія", "N": "Туреччина", "M": "Індія / Таїланд",
    "T": "Чехія / Угорщина / Словаччина", "A": "ПАР", "V": "Франція / Іспанія",
}
NORTH_AMERICA = set("12345")


class VinError(ValueError):
    pass


@dataclass
class VinInfo:
    vin: str
    make: str | None = None
    model: str | None = None
    series: str | None = None
    year: int | None = None
    body: str | None = None
    engine: str | None = None
    country: str | None = None
    market: str = "other"
    source: str = "wmi"
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def check_digit_ok(vin: str) -> bool:
    total = sum(_TRANSLIT[ch] * w for ch, w in zip(vin, _WEIGHTS))
    remainder = total % 11
    expected = "X" if remainder == 10 else str(remainder)
    return vin[8] == expected


def validate_vin(raw: str) -> tuple[str, list[str]]:
    vin = re.sub(r"[\s\-]", "", raw or "").upper()
    if len(vin) != 17:
        raise VinError("VIN має містити 17 символів")
    if not VIN_RE.fullmatch(vin):
        raise VinError("VIN може містити лише латинські літери (без I, O, Q) та цифри")
    warnings = []
    if not check_digit_ok(vin):
        warnings.append("Контрольна цифра не збігається — перевірте VIN (для авто не з Північної Америки це нормально)")
    return vin, warnings


def model_year(vin: str, today: date | None = None) -> int | None:
    code = vin[9]
    if code not in _YEAR_CODES:
        return None
    offset = _YEAR_CODES.index(code)
    first, second = 1980 + offset, 2010 + offset
    if vin[0] in NORTH_AMERICA:
        return second if vin[6].isalpha() else first
    limit = (today or date.today()).year + 1
    return second if second <= limit else first


def _from_wmi(vin: str, warnings: list[str]) -> VinInfo:
    wmi = Wmi.objects.filter(code=vin[:3]).first() or Wmi.objects.filter(code=vin[:2]).first()
    return VinInfo(
        vin=vin,
        make=wmi.make_name if wmi else None,
        year=model_year(vin),
        country=(wmi.country if wmi and wmi.country else _COUNTRY_BY_PREFIX.get(vin[0])),
        market="usa" if vin[0] in NORTH_AMERICA else "other",
        source="wmi",
        warnings=warnings,
    )


def _clean(value) -> str | None:
    value = (value or "").strip()
    return value or None


def decode(raw: str) -> VinInfo:
    vin, warnings = validate_vin(raw)
    cached = VinDecodeCache.objects.filter(vin=vin).first()
    if cached:
        return VinInfo(**cached.payload)

    info = _from_wmi(vin, warnings)
    row = nhtsa.decode_values(vin)
    if row and _clean(row.get("Model")):
        try:
            nhtsa_year = int(row.get("ModelYear") or 0) or None
        except ValueError:
            nhtsa_year = None
        make = _clean(row.get("Make"))
        info.make = info.make or (make.title() if make else None)
        info.model = _clean(row.get("Model"))
        info.series = _clean(row.get("Series"))
        info.year = nhtsa_year or info.year
        info.body = _clean(row.get("BodyClass"))
        displacement = _clean(row.get("DisplacementL"))
        info.engine = f"{float(displacement):.1f} л" if displacement else None
        info.source = "nhtsa"
        VinDecodeCache.objects.update_or_create(vin=vin, defaults={"payload": info.as_dict()})
    elif row is not None:
        # NHTSA answered but does not know this VIN (typical for EU cars) — WMI result is final
        VinDecodeCache.objects.update_or_create(vin=vin, defaults={"payload": info.as_dict()})
    return info
