"""Utility helpers for Amazon integration."""

import logging

from products.product_types import CONFIGURABLE, SIMPLE


logger = logging.getLogger(__name__)


def infer_product_type(data) -> str:
    """Infer local product type from Amazon relationships data."""
    relationships = data.relationships

    for relation in relationships:
        for rel in relation.relationships:
            if rel.child_skus:
                return CONFIGURABLE

    return SIMPLE


def extract_description_and_bullets(attributes: dict) -> tuple[str | None, list[str]]:
    """Extract description and bullet points from an Amazon attribute dict."""
    description = None
    bullets: list[str] = []

    # Get the list of description entries, fallback to empty list
    desc_entries = attributes.get("product_description", [])
    if desc_entries:
        description = desc_entries[0].get("value")

    bullet_entries = attributes.get("bullet_point", [])
    for entry in bullet_entries:
        value = entry.get("value")
        if value:
            bullets.append(value)

    return description, bullets


def extract_amazon_attribute_value(entry: dict, code: str) -> str | None:
    """Extract a value from an Amazon attribute entry using a possibly nested code."""
    parts = code.split("__")
    current = entry
    original_entry = entry

    for part in parts:
        if isinstance(current, list):
            current = current[0] if current else None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            logger.debug(
                "extract_amazon_attribute_value failed at part '%s' for code '%s' with entry %s",
                part,
                code,
                original_entry,
            )
            return None

    if isinstance(current, list):
        current = current[0] if current else None
    if isinstance(current, dict):
        return current.get("value") or current.get("name")
    if isinstance(current, str):
        return current

    logger.debug(
        "extract_amazon_attribute_value returned None for code '%s' with entry %s",
        code,
        original_entry,
    )
    return None


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
