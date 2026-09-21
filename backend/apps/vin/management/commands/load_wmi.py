import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.vin.models import Wmi

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "wmi.json"


class Command(BaseCommand):
    help = "Load World Manufacturer Identifier codes (VIN positions 1–3)"

    def handle(self, *args, **opts):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        count = 0
        for make, codes in data.items():
            for code, country in codes.items():
                Wmi.objects.update_or_create(code=code, defaults={"make_name": make, "country": country})
                count += 1
        self.stdout.write(self.style.SUCCESS(f"WMI кодів: {count}"))
