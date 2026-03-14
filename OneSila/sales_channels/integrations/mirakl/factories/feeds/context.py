from __future__ import annotations

from collections import defaultdict
from typing import Any

from eancodes.models import EanCode
from media.models import Media, MediaProductThrough
from products.models import Product, ProductTranslation
from properties.models import ProductProperty
from sales_channels.models import SalesChannelIntegrationPricelist
from sales_prices.models import SalesPriceListItem


class MiraklProductSourceDataLoader:
    """Load local product data used by Mirakl feed payload resolvers."""

    def __init__(self, *, remote_product) -> None:
        self.remote_product = remote_product
        self.sales_channel = remote_product.sales_channel
        self.local_product = remote_product.local_instance
        self.language = getattr(self.sales_channel.multi_tenant_company, "language", None)

    def resolve_products(self) -> list[Product]:
        if self.local_product is None:
            return []
        if not self.local_product.is_configurable():
            return [self.local_product]
        variations = list(self.local_product.get_configurable_variations(active_only=False))
        return [self.local_product, *variations] if variations else [self.local_product]

    def load_translations(self, *, products: list[Product]) -> dict[int, list[ProductTranslation]]:
        queryset = ProductTranslation.objects.filter(product_id__in=[product.id for product in products]).order_by("id")
        results: dict[int, list[ProductTranslation]] = defaultdict(list)
        for translation in queryset.iterator():
            results[translation.product_id].append(translation)
        return results

    def load_properties(self, *, products: list[Product]) -> dict[int, list[ProductProperty]]:
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

    def load_prices(self, *, products: list[Product]) -> dict[int, list[dict[str, Any]]]:
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

    def load_media(self, *, products: list[Product]) -> dict[int, list[dict[str, Any]]]:
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

    def load_eans(self, *, products: list[Product]) -> dict[int, str]:
        queryset = EanCode.objects.filter(product_id__in=[product.id for product in products]).order_by("id")
        return {ean.product_id: ean.ean_code for ean in queryset.iterator() if ean.ean_code}

    def select_translation(self, *, translations: list[ProductTranslation]) -> ProductTranslation | None:
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
