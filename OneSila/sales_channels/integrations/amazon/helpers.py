"""Utility helpers for Amazon integration."""

from products.product_types import CONFIGURABLE, SIMPLE


def infer_product_type(data: dict) -> str:
    """Infer local product type from Amazon relationships data."""
    relationships = data.get("relationships", [])

    for relation in relationships:
        for rel in relation.get("relationships", []):
            if rel.get("child_skus"):
                return CONFIGURABLE

    return SIMPLE


def extract_description_and_bullets(attributes: dict) -> tuple[str | None, list[str]]:
    """Extract description and bullet points from attribute data."""
    description = None
    bullets: list[str] = []

    description_data = attributes.get("product_description") or []
    if description_data:
        description = description_data[0].get("value")

    bullet_data = attributes.get("bullet_point") or []
    for bullet in bullet_data:
        value = bullet.get("value")
        if value:
            bullets.append(value)

    return description, bullets

