"""Facade for Shein product import parsing helpers."""

from __future__ import annotations

from typing import Any

from .product_attributes import SheinProductImportAttributeParser
from .product_values import SheinProductImportValueParser


class SheinProductImportPayloadParser:
    def __init__(self, *, sales_channel) -> None:
        self.values = SheinProductImportValueParser(sales_channel=sales_channel)
        self.attributes = SheinProductImportAttributeParser(sales_channel=sales_channel)

    def parse_translations(self, *, **kwargs: Any):
        return self.values.parse_translations(**kwargs)

    def parse_images(self, *, **kwargs: Any):
        return self.values.parse_images(**kwargs)

    def parse_prices(self, *, **kwargs: Any):
        return self.values.parse_prices(**kwargs)

    def parse_attributes(self, *, **kwargs: Any):
        return self.attributes.parse_attributes(**kwargs)
