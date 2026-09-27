"""Category hierarchy helpers shared by pricing and search."""

from collections import defaultdict

from ..models import Category


def category_children() -> dict[int | None, list[int]]:
    children = defaultdict(list)
    for category_id, parent_id in Category.objects.order_by().values_list("id", "parent_id"):
        children[parent_id].append(category_id)
    return children


def category_and_descendant_ids(category_ids, *, children=None) -> set[int]:
    result = set(category_ids)
    if not result:
        return result
    if children is None:
        children = category_children()
    pending = list(result)
    while pending:
        for child_id in children[pending.pop()]:
            if child_id not in result:
                result.add(child_id)
                pending.append(child_id)
    return result
