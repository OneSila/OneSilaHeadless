from __future__ import annotations

from collections import defaultdict
from typing import Any

from eancodes.models import EanCode
from media.models import Media, MediaProductThrough
from products.models import Product, ProductTranslation
from properties.models import ProductProperty
from sales_channels.models import SalesChannelIntegrationPricelist
from sales_channels.models.products import RemoteProduct
from sales_prices.models import SalesPriceListItem


class SalesChannelFeedProductPayloadFactory:
    """Build a normalized product payload for feed-style integrations."""

    def __init__(self, *, remote_product: RemoteProduct) -> None:
        self.remote_product = remote_product
        self.sales_channel = remote_product.sales_channel
        self.local_product = remote_product.local_instance
        self.language = getattr(self.sales_channel.multi_tenant_company, "language", None)

    def build(self) -> list[dict[str, Any]]:
        if self.local_product is None:
            return []

        products = self._resolve_products()
        translations = self._load_translations(products=products)
        product_properties = self._load_properties(products=products)
        prices = self._load_prices(products=products)
        media = self._load_media(products=products)
        eans = self._load_eans(products=products)

        parent_sku = getattr(self.local_product, "sku", "") or ""
        variant_group_code = parent_sku if self.local_product.is_configurable() else ""

        payloads: list[dict[str, Any]] = []
        for product in products:
            translation = self._select_translation(translations=translations.get(product.id, []))
            product_payload = {
                "local_product_id": product.id,
                "action": self._determine_action(remote_product=self.remote_product, product=product),
                "sku": getattr(product, "sku", "") or "",
                "parent_sku": parent_sku if product.id != self.local_product.id else "",
                "variant_group_code": variant_group_code if product.id != self.local_product.id else "",
                "type": getattr(product, "type", "") or "",
                "active": bool(getattr(product, "active", False)),
                "name": getattr(translation, "name", None) or getattr(product, "name", ""),
                "short_description": getattr(translation, "short_description", None) or "",
                "description": getattr(translation, "description", None) or "",
                "url_key": getattr(translation, "url_key", None) or "",
                "ean": eans.get(product.id, ""),
                "brand": self._extract_brand(product_properties=product_properties.get(product.id, [])),
                "category": self._extract_category(),
                "attributes": self._serialize_attributes(product_properties=product_properties.get(product.id, [])),
                "images": media.get(product.id, []),
                "prices": prices.get(product.id, []),
            }
            payloads.append(product_payload)

        return payloads

    def _resolve_products(self) -> list[Product]:
        if not self.local_product.is_configurable():
            return [self.local_product]
        variations = list(self.local_product.get_configurable_variations(active_only=False))
        return [self.local_product, *variations] if variations else [self.local_product]

    def _load_translations(self, *, products: list[Product]) -> dict[int, list[ProductTranslation]]:
        queryset = ProductTranslation.objects.filter(product_id__in=[product.id for product in products]).order_by("id")
        results: dict[int, list[ProductTranslation]] = defaultdict(list)
        for translation in queryset.iterator():
            results[translation.product_id].append(translation)
        return results

    def _load_properties(self, *, products: list[Product]) -> dict[int, list[ProductProperty]]:
        queryset = (
            ProductProperty.objects.filter(product_id__in=[product.id for product in products])
            .select_related("property", "value_select")
            .prefetch_related("value_multi_select")
            .order_by("product_id", "id")
        )
        results: dict[int, list[ProductProperty]] = defaultdict(list)
        for item in queryset.iterator():
            results[item.product_id].append(item)
        return results

    def _load_prices(self, *, products: list[Product]) -> dict[int, list[dict[str, Any]]]:
        product_ids = [product.id for product in products]
        channel_pricelists = list(
            SalesChannelIntegrationPricelist.objects.filter(sales_channel=self.sales_channel).select_related("price_list__currency")
        )
        if not channel_pricelists:
            return {}

        queryset = (
            SalesPriceListItem.objects.filter(product_id__in=product_ids, salespricelist__in=[item.price_list for item in channel_pricelists])
            .select_related("salespricelist__currency")
            .order_by("product_id", "id")
        )
        results: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for item in queryset.iterator():
            currency = getattr(getattr(item.salespricelist, "currency", None), "iso_code", "") or ""
            price = getattr(item, "price", None)
            discount = getattr(item, "discount", None)
            if price is None and discount is None:
                continue
            results[item.product_id].append(
                {
                    "currency": currency,
                    "price": price,
                    "discount": discount,
                }
            )
        return results

    def _load_media(self, *, products: list[Product]) -> dict[int, list[dict[str, Any]]]:
        queryset = (
            MediaProductThrough.objects.filter(product_id__in=[product.id for product in products])
            .select_related("media", "sales_channel")
            .order_by("product_id", "-is_main_image", "sort_order", "id")
        )
        results: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for item in queryset.iterator():
            if item.sales_channel_id not in (None, self.sales_channel.id):
                continue
            media = item.media
            if media.type != Media.IMAGE:
                continue
            url = media.image_url()
            if not url:
                continue
            results[item.product_id].append(
                {
                    "url": url,
                    "is_main": bool(item.is_main_image),
                    "sort_order": item.sort_order,
                }
            )
        return results

    def _load_eans(self, *, products: list[Product]) -> dict[int, str]:
        queryset = EanCode.objects.filter(product_id__in=[product.id for product in products]).order_by("id")
        return {ean.product_id: ean.ean_code for ean in queryset.iterator() if ean.ean_code}

    def _select_translation(self, *, translations: list[ProductTranslation]) -> ProductTranslation | None:
        if not translations:
            return None
        if self.language:
            for translation in translations:
                if translation.language == self.language and translation.sales_channel_id in (None, self.sales_channel.id):
                    return translation
            for translation in translations:
                if translation.language == self.language:
                    return translation
        for translation in translations:
            if translation.sales_channel_id in (None, self.sales_channel.id):
                return translation
        return translations[0]

    def _determine_action(self, *, remote_product: RemoteProduct, product: Product) -> str:
        if not getattr(product, "active", False):
            return "delete"
        if getattr(remote_product, "remote_id", None):
            return "update"
        return "create"

    def _extract_brand(self, *, product_properties: list[ProductProperty]) -> str:
        for product_property in product_properties:
            prop = product_property.property
            internal_name = str(getattr(prop, "internal_name", "") or "").lower()
            name = str(getattr(prop, "name", "") or "").lower()
            if internal_name == "brand" or name == "brand":
                value = product_property.get_serialised_value(self.language)
                return str(value or "")
        return ""

    def _extract_category(self) -> dict[str, Any]:
        product_category = (
            self.remote_product.local_instance.miraklproductcategory_set.filter(sales_channel=self.sales_channel)
            .first()
            if self.remote_product.local_instance_id
            else None
        )
        if not product_category:
            return {}
        return {
            "remote_id": getattr(product_category, "remote_id", "") or "",
            "name": "",
        }

    def _serialize_attributes(self, *, product_properties: list[ProductProperty]) -> list[dict[str, Any]]:
        attributes: list[dict[str, Any]] = []
        for product_property in product_properties:
            prop = product_property.property
            if getattr(prop, "is_product_type", False):
                continue
            attributes.append(
                {
                    "code": getattr(prop, "internal_name", None) or getattr(prop, "name", ""),
                    "name": getattr(prop, "name", ""),
                    "type": getattr(prop, "type", ""),
                    "value": product_property.get_serialised_value(self.language),
                }
            )
        return attributes
