"""Utility helpers for Amazon integration."""

from products.product_types import CONFIGURABLE, SIMPLE


def infer_product_type(data) -> str:
    """Infer local product type from Amazon relationships data."""
    relationships = data.relationships

    for relation in relationships:
        for rel in relation.relationships:
            if rel.child_skus:
                return CONFIGURABLE

    return SIMPLE


def extract_description_and_bullets(attributes: list[dict]) -> tuple[str | None, list[str]]:
    """Extract description and bullet points from a list of attribute dicts."""
    description = None
    bullets: list[str] = []

    for attr in attributes:
        code = attr.get("attribute_name")
        values = attr.get("values", [])

        if code == "product_description" and values:
            description = values[0].get("value")

        if code == "bullet_point":
            for val in values:
                value = val.get("value")
                if value:
                    bullets.append(value)

    return description, bullets


def get_is_product_variation(data):
    """Return whether the product is a variation and its parent SKUs if present."""
    relationships = getattr(data, 'relationships', []) or []
    parent_skus = []

    for relation in relationships:
        for rel in getattr(relation, 'relationships', []) or []:
            parent_sku = getattr(rel, 'parent_sku', None)
            if parent_sku:
                parent_skus.append(parent_sku)

    if parent_skus:
        return True, parent_skus
    else:
        return False, []
