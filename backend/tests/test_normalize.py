from apps.core.normalize import normalize_part_number, slugify_uk, split_part_numbers


def test_normalize_strips_separators_and_case():
    assert normalize_part_number(" 5619 41005-d ") == "561941005D"
    assert normalize_part_number("fp7439-r1t") == "FP7439R1T"
    assert normalize_part_number("A 124 880 40 70") == "A1248804070"
    assert normalize_part_number("") == ""


def test_slugify_uk_transliterates_ukrainian():
    assert slugify_uk("Фари передні") == "fary-peredni"
    assert slugify_uk("Volkswagen Passat B7 USA") == "volkswagen-passat-b7-usa"
    assert slugify_uk("Підкрилки (локери)") == "pidkrylky-lokery"
    assert slugify_uk("Щітки, ґрати, Їжак") == "shchitky-graty-yizhak"


def test_split_part_numbers_ignores_years_and_ranges():
    assert split_part_numbers("Фара ліва Volkswagen Passat B7 USA 2010-2014 (561941005D)") == ["561941005D"]
    assert split_part_numbers("GHK151160 GHK151160A") == ["GHK151160", "GHK151160A"]
    assert split_part_numbers("Mercedes W124 1984-1996 A1248804070") == ["A1248804070"]


def test_split_part_numbers_deduplicates_and_skips_short_tokens():
    assert split_part_numbers("B7 B7 12345 12345") == ["12345"]
