"""Utility helpers for Amazon integration."""

import logging

from products.product_types import CONFIGURABLE, SIMPLE
from core.helpers import ensure_serializable


logger = logging.getLogger(__name__)


def infer_product_type(data) -> str:
    """Infer local product type from Amazon relationships data."""
    if isinstance(data, dict):
        relationships = data.get("relationships") or []
    else:
        relationships = getattr(data, "relationships", []) or []

    for relation in relationships:
        rels = relation.get("relationships", []) if isinstance(relation, dict) else getattr(relation, "relationships", []) or []

        for rel in rels:
            rel_type = rel.get("type") if isinstance(rel, dict) else getattr(rel, "type", None)

            # we only care about the type VARIATION
            if rel_type != "VARIATION":
                continue

            child_skus = rel.get("child_skus") if isinstance(rel, dict) else getattr(rel, "child_skus", None)
            if child_skus:
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


def is_safe_content(value: str | None) -> bool:
    """Return True if the value is considered valid content."""
    if value is None:
        return False
    value = str(value).strip()
    return value not in ("", "<p><br></p>")


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
        return current.get("value") if "value" in current else current.get("name")

    if isinstance(current, (str, int, float, bool)):
        return current

    logger.debug(
        "extract_amazon_attribute_value returned None for code '%s' with entry %s",
        code,
        original_entry,
    )
    return None


def get_is_product_variation(data):
    """Return whether the product is a variation and its parent SKUs if present."""
    if isinstance(data, dict):
        relationships = data.get("relationships") or []
    else:
        relationships = getattr(data, "relationships", []) or []

    parent_skus = []

    for relation in relationships:
        rels = relation.get("relationships", []) if isinstance(relation, dict) else getattr(relation, "relationships", []) or []
        for rel in rels:

            rel_type = rel.get("type") if isinstance(rel, dict) else getattr(rel, "type", None)
            if rel_type != "VARIATION":
                continue

            # Handle plural parent_skus list
            if isinstance(rel, dict):
                skus = rel.get("parent_skus") or []
            else:
                skus = getattr(rel, "parent_skus", []) or []
            parent_skus.extend(skus)

    if parent_skus:
        return True, parent_skus
    else:
        return False, []



def serialize_listing_item(item):
    """Return a serializable dictionary representation of an SP-API listing item."""
    if hasattr(item, "to_dict"):
        return item.to_dict()
    if hasattr(item, "__dict__"):
        return ensure_serializable(item.__dict__)
    return ensure_serializable(item)
