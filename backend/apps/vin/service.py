from apps.catalog.services.queries import car_ref

from .decoder import decode
from .matching import match_generations


def decode_and_match(vin: str) -> dict:
    """Decode a VIN and attach up to three matching catalog generations (as CarRef dicts)."""
    info = decode(vin)
    data = info.as_dict()
    data["valid"] = True
    data["matches"] = [car_ref(g) for g in match_generations(info)]
    return data
