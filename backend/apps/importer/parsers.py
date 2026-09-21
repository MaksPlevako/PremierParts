"""Pure HTML -> data parsers for the legacy premier-parts.com.ua site (no network, no DB)."""

import json
import re
from dataclasses import dataclass, field
from decimal import Decimal
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

BASE = "https://premier-parts.com.ua"
_YEARS = re.compile(r"((?:19|20)\d{2})\s*-\s*((?:19|20)\d{2})?")
_SINGLE_YEAR = re.compile(r"((?:19|20)\d{2})")


@dataclass
class CategoryNode:
    name: str
    slug: str | None
    icon_url: str | None = None
    children: list["CategoryNode"] = field(default_factory=list)


@dataclass(frozen=True)
class ModelLink:
    make_legacy_id: int
    model_legacy_id: int
    series_legacy_id: int
    model_name: str
    years: tuple[int | None, int | None]


@dataclass
class ParsedProduct:
    url: str
    slug: str
    name: str
    sku: str = ""
    manufacturer: str | None = None
    make: str | None = None
    model: str | None = None
    series: str | None = None
    condition: str | None = None
    price: Decimal = Decimal("0")
    in_stock: bool = False
    description: str = ""
    image_urls: list[str] = field(default_factory=list)
    breadcrumbs: list[tuple[str, str]] = field(default_factory=list)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _category_slug(href: str) -> str | None:
    m = re.search(r"/category/([^/?#]+)", href or "")
    return m.group(1) if m else None


def parse_years(label: str) -> tuple[int | None, int | None]:
    label = label or ""
    if m := _YEARS.search(label):
        return int(m.group(1)), int(m.group(2)) if m.group(2) else None
    if m := _SINGLE_YEAR.search(label):
        return int(m.group(1)), None
    return None, None


def parse_side_position(name: str) -> tuple[str, str]:
    low = (name or "").lower()
    side = "none"
    if re.search(r"\b(ліва|лівий|ліве|лів\.|левая|левый)", low):
        side = "left"
    elif re.search(r"\b(права|правий|праве|прав\.|правая|правый)", low):
        side = "right"
    position = "none"
    if re.search(r"\b(передн|передній)", low):
        position = "front"
    elif re.search(r"\b(задн|задній)", low):
        position = "rear"
    return side, position


def parse_home_categories(html: str) -> list[CategoryNode]:
    soup = _soup(html)
    nodes: list[CategoryNode] = []
    for item in soup.select("li.nav-horizontal__item"):
        text = item.select_one(".nav-horizontal__text")
        if not text:
            continue
        icon = item.select_one(".nav-horizontal__ico img")
        node = CategoryNode(
            name=text.get_text(strip=True),
            slug=None,
            icon_url=urljoin(BASE, icon["src"]) if icon and icon.get("src") else None,
        )
        for a in item.select(".nav-horizontal__sub-list a[href]"):
            slug = _category_slug(a["href"])
            if slug:
                node.children.append(CategoryNode(name=a.get_text(strip=True), slug=slug))
        nodes.append(node)
    return nodes


def parse_home_makes(html: str) -> list[tuple[int, str]]:
    seen: dict[int, str] = {}
    for a in _soup(html).select('a[href^="/mark/"]'):
        m = re.match(r"^/mark/(\d+)$", a["href"])
        name = a.get_text(strip=True)
        if m and name:
            seen.setdefault(int(m.group(1)), name)
    return list(seen.items())


def parse_mark_models(html: str, make_legacy_id: int) -> list[ModelLink]:
    links: dict[tuple[int, int], ModelLink] = {}
    pattern = re.compile(rf"^/model/{make_legacy_id}/(\d+)/(\d+)$")
    for a in _soup(html).select('a[href^="/model/"]'):
        m = pattern.match(a["href"])
        if not m:
            continue
        text = a.get_text(" ", strip=True)
        model_name = re.sub(r"\(.*?\)", "", text).strip()
        if not model_name:
            continue
        key = (int(m.group(1)), int(m.group(2)))
        links.setdefault(
            key,
            ModelLink(
                make_legacy_id=make_legacy_id,
                model_legacy_id=key[0],
                series_legacy_id=key[1],
                model_name=model_name,
                years=parse_years(text),
            ),
        )
    return list(links.values())


def parse_category_page(html: str) -> tuple[list[str], int]:
    soup = _soup(html)
    urls: dict[str, None] = {}
    for a in soup.select('.single-shop-product a[href*="/product/"]'):
        urls.setdefault(urljoin(BASE, a["href"]), None)
    last = 0
    for a in soup.select("ul.pagination a[href]"):
        if m := re.search(r"/category/[^/]+/(\d+)$", a["href"]):
            last = max(last, int(m.group(1)))
    return list(urls), last


def _json_ld_product(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            return data
    return {}


def _spec_table(soup: BeautifulSoup) -> dict[str, str]:
    specs: dict[str, str] = {}
    for row in soup.select("table.table tr"):
        cells = row.find_all("td")
        if len(cells) == 2:
            specs[cells[0].get_text(strip=True)] = cells[1].get_text(" ", strip=True)
    return specs


def parse_product(html: str, url: str) -> ParsedProduct:
    soup = _soup(html)
    ld = _json_ld_product(soup)
    specs = _spec_table(soup)
    offer = ld.get("offers") or {}
    h1 = soup.find("h1")

    images: dict[str, None] = {}
    for a in soup.select('a[href^="/uploads/product/"]'):
        images.setdefault(urljoin(BASE, a["href"]), None)
    if not images and ld.get("image"):
        images[urljoin(BASE, ld["image"])] = None

    crumbs: list[tuple[str, str]] = []
    for item in soup.select('[itemtype="http://schema.org/ListItem"]'):
        link = item.find("a", href=True)
        slug = _category_slug(link["href"]) if link else None
        name = item.find(itemprop="name")
        if slug and name:
            crumbs.append((name.get_text(strip=True), slug))

    return ParsedProduct(
        url=url,
        slug=urlparse(url).path.rstrip("/").rsplit("/", 1)[-1],
        name=h1.get_text(" ", strip=True) if h1 else ld.get("name", ""),
        sku=specs.get("Артикул") or ld.get("sku", ""),
        manufacturer=specs.get("Виробник") or ld.get("brand") or None,
        make=specs.get("Марка"),
        model=specs.get("Модель"),
        series=specs.get("Серія"),
        condition=specs.get("Стан"),
        price=Decimal(str(offer.get("price") or 0)),
        in_stock=str(offer.get("availability", "")).endswith("InStock"),
        description=(ld.get("description") or "").strip(),
        image_urls=list(images),
        breadcrumbs=crumbs,
    )


def parse_page_body(html: str) -> tuple[str, str]:
    soup = _soup(html)
    h1 = soup.find("h1")
    container = soup.select_one(".single-product-area .col-md-12") or soup.select_one(".single-product-area")
    if not container:
        return (h1.get_text(strip=True) if h1 else ""), ""
    for tag in container.find_all(["script", "style", "iframe", "form"]):
        tag.decompose()
    for tag in container.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in {"href", "src", "alt"}}
    body = "".join(str(c) for c in container.contents).strip()
    return (h1.get_text(strip=True) if h1 else ""), body
