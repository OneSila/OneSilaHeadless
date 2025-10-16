from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Iterable, Optional

from django.template import engines
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import format_html

from currencies.models import Currency
from media.models import Media, MediaProductThrough
from products.models import Product
from properties.models import ProductProperty, PropertySelectValue
from sales_channels.models.sales_channels import SalesChannel, SalesChannelContentTemplate

from get_absolute_url.helpers import generate_absolute_url


@dataclass(frozen=True)
class SerializedMedia:
    url: Optional[str]
    thumbnail: Optional[str]
    is_main: bool
    title: Optional[str]

    def to_dict(self) -> dict[str, Optional[str] | bool]:
        return {
            "url": self.url,
            "thumbnail": self.thumbnail,
            "is_main": self.is_main,
            "title": self.title,
        }


@dataclass(frozen=True)
class SerializedProperty:
    name: str
    internal_name: Optional[str]
    type: str
    value: object

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ContentTemplateDataBuilder:
    def __init__(
        self,
        *,
        product: Product,
        sales_channel: SalesChannel,
        description: Optional[str],
        language: str,
        title: str,
        media_assignments: Optional[Iterable[MediaProductThrough]] = None,
        product_properties: Optional[Iterable[ProductProperty]] = None,
        price: Optional[Decimal] = None,
        discount_price: Optional[Decimal] = None,
        currency: Optional[str] = None,
    ) -> None:
        self.product = product
        self.sales_channel = sales_channel
        self.description = description or ""
        self.language = language
        self.title = title or ""
        self._media_assignments = list(media_assignments) if media_assignments is not None else None
        self._product_properties = list(product_properties) if product_properties is not None else None
        self._price_override = price
        self._discount_price_override = discount_price
        self._currency_override = currency

    @cached_property
    def media_assignments(self) -> list[MediaProductThrough]:
        if self._media_assignments is not None:
            return list(self._media_assignments)
        return list(
            MediaProductThrough.objects.get_product_images(
                product=self.product,
                sales_channel=self.sales_channel,
            )
            .filter(media__type=Media.IMAGE)
            .order_by("-is_main_image", "sort_order")
        )

    @cached_property
    def properties(self) -> list[ProductProperty]:
        if self._product_properties is not None:
            return list(self._product_properties)
        return list(
            ProductProperty.objects.filter(
                product=self.product,
                property__is_public_information=True,
            )
            .select_related("property", "value_select")
            .prefetch_related("value_multi_select")
        )

    def _serialize_media(self) -> dict[str, object]:
        serialized = [
            SerializedMedia(
                url=assignment.media.image_url(),
                thumbnail=assignment.media.onesila_thumbnail_url(),
                is_main=assignment.is_main_image,
                title=assignment.media.title,
            )
            for assignment in self.media_assignments
        ]

        main_url = next((item.url for item in serialized if item.url), None)
        if main_url is None and serialized:
            main_url = serialized[0].url

        return {
            "main": main_url,
            "all": [item.url for item in serialized if item.url],
            "items": [item.to_dict() for item in serialized],
        }

    def _serialize_property_value(self, *, product_property: ProductProperty) -> object:
        value = product_property.get_serialised_value(language=self.language)

        if isinstance(value, PropertySelectValue):
            return value.value_by_language_code(language=self.language)

        if hasattr(value, "all"):
            return [
                item.value_by_language_code(language=self.language)
                if isinstance(item, PropertySelectValue)
                else item
                for item in value.all()
            ]

        return value

    def _serialize_properties(self) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
        serialized: list[dict[str, object]] = []
        mapped: dict[str, dict[str, object]] = {}

        for product_property in self.properties:
            name = product_property.property._get_translated_value(
                field_name="name",
                related_name="propertytranslation_set",
                language=self.language,
            )
            internal_name = product_property.property.internal_name
            serialized_value = self._serialize_property_value(product_property=product_property)

            entry = SerializedProperty(
                name=name or "",
                internal_name=internal_name,
                type=product_property.property.type,
                value=serialized_value,
            ).to_dict()

            serialized.append(entry)
            if internal_name:
                mapped[internal_name] = entry

        return serialized, mapped

    def _serialize_price(self) -> tuple[Optional[Decimal], Optional[Decimal], Optional[str]]:
        price = self._price_override
        discount = self._discount_price_override
        currency_code = self._currency_override

        if price is not None and currency_code is not None and discount is not None:
            return price, discount, currency_code

        currency = Currency.objects.filter(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            is_default_currency=True,
        ).first()

        computed_price, computed_discount = self.product.get_price_for_sales_channel(
            self.sales_channel,
            currency=currency,
        )

        if price is None:
            price = computed_price

        if discount is None:
            discount = computed_discount

        if currency_code is None:
            currency_code = currency.iso_code if currency else None

        return price, discount, currency_code

    def build(self) -> dict[str, object]:
        properties, mapped_properties = self._serialize_properties()
        price, discount, currency_code = self._serialize_price()

        brand = None
        if "brand" in mapped_properties:
            brand_value = mapped_properties["brand"]["value"]
            if isinstance(brand_value, list):
                brand = ", ".join(str(value) for value in brand_value if value)
            else:
                brand = brand_value

        return {
            "content": self.description,
            "title": self.title,
            "sku": self.product.sku,
            "price": price,
            "discount_price": discount,
            "currency": currency_code,
            "brand": brand,
            "language": self.language,
            "images": self._serialize_media(),
            "product_properties": properties,
            "product_properties_map": mapped_properties,
        }


def build_content_template_context(
    *,
    product: Product,
    sales_channel: SalesChannel,
    description: Optional[str],
    language: str,
    title: str,
    media_assignments: Optional[Iterable[MediaProductThrough]] = None,
    product_properties: Optional[Iterable[ProductProperty]] = None,
    price: Optional[Decimal] = None,
    discount_price: Optional[Decimal] = None,
    currency: Optional[str] = None,
) -> dict[str, object]:
    builder = ContentTemplateDataBuilder(
        product=product,
        sales_channel=sales_channel,
        description=description,
        language=language,
        title=title,
        media_assignments=media_assignments,
        product_properties=product_properties,
        price=price,
        discount_price=discount_price,
        currency=currency,
    )
    return builder.build()


def get_sales_channel_content_template(
    *,
    sales_channel: SalesChannel,
    language: str,
) -> Optional[SalesChannelContentTemplate]:
    return SalesChannelContentTemplate.objects.filter(
        sales_channel=sales_channel,
        language=language,
    ).first()


def _render_iframe_markup(*, iframe_src: str) -> str:
    return format_html(
        '<iframe id="desc_ifr" title="Seller\'s description of item" '
        "sandbox=\"allow-scripts allow-popups allow-popups-to-escape-sandbox allow-same-origin\" "
        "height=\"2950px\" width=\"100%\" marginheight=\"0\" marginwidth=\"0\" frameborder=\"0\" "
        'src="{}" loading="lazy"></iframe>',
        iframe_src,
    )


def get_sales_channel_content_template_iframe(
    *,
    template: SalesChannelContentTemplate,
    product: Product,
) -> str | None:
    if not template.add_as_iframe:
        return None

    template_id = getattr(template, "id", None)
    product_id = getattr(product, "id", None)
    if not template_id or not product_id:
        return None

    iframe_path = reverse(
        "sales_channel_template_product",
        kwargs={
            "template_id": template_id,
            "product_id": product_id,
        },
    )
    iframe_src = f"{generate_absolute_url(trailing_slash=False)}{iframe_path}"

    return _render_iframe_markup(iframe_src=iframe_src)


def render_sales_channel_content_template(
    *,
    template_string: str,
    context: dict[str, object],
) -> str:
    iframe_markup = context.get("iframe")
    if iframe_markup:
        return iframe_markup

    iframe_src = context.get("iframe_src")
    if iframe_src:
        return _render_iframe_markup(iframe_src=str(iframe_src))

    template = engines["django"].from_string(template_string)
    return template.render(context)


__all__ = [
    "build_content_template_context",
    "get_sales_channel_content_template",
    "get_sales_channel_content_template_iframe",
    "render_sales_channel_content_template",
    "SalesChannelContentTemplate",
]
