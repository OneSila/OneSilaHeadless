from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional, Tuple
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone

from llm.exceptions import ProductFeedConfigurationError
from llm.factories import ProductFeedPayloadFactory
from media.models import Media


@dataclass
class DummyCompany:
    language: str = "en"


@dataclass
class DummySalesChannel:
    id: int
    gpt_enable: bool
    gpt_enable_checkout: bool
    gpt_seller_name: str
    gpt_seller_url: Optional[str]
    gpt_seller_privacy_policy: str
    gpt_seller_tos: str
    gpt_return_policy: str
    gpt_return_window: int
    starting_stock: Optional[int]
    hostname: str
    multi_tenant_company: DummyCompany


@dataclass
class DummyProduct:
    id: int
    sku: str
    name: str
    ean_code: Optional[str]
    active: bool
    allow_backorder: bool
    price: Decimal
    sale_price: Optional[Decimal]
    product_rule: Optional[str]
    configurable: bool = False
    url_key: str = ""

    def is_configurable(self) -> bool:
        return self.configurable

    def get_price_for_sales_channel(self, sales_channel: DummySalesChannel) -> Tuple[Decimal, Optional[Decimal]]:
        return self.price, self.sale_price

    def get_product_rule(self) -> Optional[SimpleNamespace]:
        if self.product_rule is None:
            return None
        return SimpleNamespace(value=self.product_rule)


class DummyProductProperty:
    def __init__(self, *, value: Any = None, value_select_id: Optional[int] = None) -> None:
        self._value = value
        self.value_select_id = value_select_id

    def get_serialised_value(self, *, language: str) -> Any:  # noqa: D401 - mimic real signature
        return self._value


@dataclass
class DummyConfiguratorItem:
    property_id: int
    property: SimpleNamespace


class DummyMedia:
    def __init__(
        self,
        *,
        media_type: str,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        video: Optional[str] = None,
    ) -> None:
        self.type = media_type
        self._thumbnail = thumbnail
        self._image = image
        self.video_url = video

    def onesila_thumbnail_url(self) -> Optional[str]:
        return self._thumbnail

    def image_url(self) -> Optional[str]:
        return self._image


@dataclass
class DummyMediaAssignment:
    media: DummyMedia
    is_main_image: bool = False
    sort_order: int = 0
    id: int = 0


class StubSalesChannelViewAssign:
    def __init__(
        self,
        *,
        product: DummyProduct,
        sales_channel_view: SimpleNamespace,
        sales_channel: DummySalesChannel,
        multi_tenant_company: DummyCompany,
    ) -> None:
        self.product = product
        self.sales_channel_view = sales_channel_view
        self.sales_channel = sales_channel
        self.multi_tenant_company = multi_tenant_company
        base_url = getattr(sales_channel_view, "base_url", f"https://{sales_channel.hostname}")
        self.remote_url = f"{base_url.rstrip('/')}/{product.sku}"


class _DummySalesChannelViewAssignManager:
    def __init__(self, assignments: List[SimpleNamespace]) -> None:
        self._assignments = assignments

    def order_by(self, *args: str) -> "_DummySalesChannelViewAssignManager":
        return self

    def first(self) -> Optional[SimpleNamespace]:
        if not self._assignments:
            return None
        return self._assignments[0]


@dataclass
class DummyRemoteProduct:
    sales_channel: DummySalesChannel
    multi_tenant_company: DummyCompany
    local_instance: DummyProduct
    cached_assignments: List[SimpleNamespace]
    saleschannelviewassign_set: _DummySalesChannelViewAssignManager = field(init=False)

    def __post_init__(self) -> None:
        self.saleschannelviewassign_set = _DummySalesChannelViewAssignManager(self.cached_assignments)


class ProductFeedPayloadFactoryTests(SimpleTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.company = DummyCompany(language="en")
        self.config = SimpleNamespace(
            condition_property_id=1,
            brand_property_id=2,
            material_property_id=3,
            mpn_property_id=4,
            length_property_id=5,
            width_property_id=6,
            height_property_id=7,
            weight_property_id=8,
            age_group_property_id=9,
            expiration_date_property_id=10,
            pickup_method_property_id=11,
            color_property_id=12,
            size_property_id=13,
            size_system_property_id=14,
            gender_property_id=15,
            popularity_score_property_id=16,
            warning_property_id=17,
            age_restriction_property_id=18,
            length_unit="in",
            weight_unit="lb",
            condtion_new_value=SimpleNamespace(id=101),
            condtion_refurbished_value=SimpleNamespace(id=102),
            condtion_usd_value=SimpleNamespace(id=103),
            age_group_newborn_value=SimpleNamespace(id=201),
            age_group_infant_value=SimpleNamespace(id=202),
            age_group_todler_value=SimpleNamespace(id=203),
            age_group_kids_value=SimpleNamespace(id=204),
            age_group_adult_value=SimpleNamespace(id=205),
            pickup_method_in_store_value=SimpleNamespace(id=301),
            pickup_method_reserve_value=SimpleNamespace(id=302),
            pickup_method_not_supported_value=SimpleNamespace(id=303),
        )

    def _build_sales_channel(self, **overrides: object) -> DummySalesChannel:
        defaults = dict(
            id=10,
            gpt_enable=True,
            gpt_enable_checkout=True,
            gpt_seller_name="Blue",
            gpt_seller_url="https://seller.example.com",
            gpt_seller_privacy_policy="https://seller.example.com/privacy",
            gpt_seller_tos="https://seller.example.com/tos",
            gpt_return_policy="https://seller.example.com/returns",
            gpt_return_window=30,
            starting_stock=7,
            hostname="channel.example.com",
            multi_tenant_company=self.company,
        )
        defaults.update(overrides)
        return DummySalesChannel(**defaults)

    def _build_assign(
        self,
        *,
        sales_channel: DummySalesChannel,
        product: DummyProduct,
        remote_url: str,
        sales_channel_view: Optional[SimpleNamespace] = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            sales_channel=sales_channel,
            product=product,
            remote_url=remote_url,
            product_id=product.id,
            sales_channel_view=sales_channel_view or SimpleNamespace(base_url="https://shop.example.com"),
            multi_tenant_company=self.company,
        )

    def _build_remote_product(
        self,
        *,
        sales_channel: DummySalesChannel,
        product: DummyProduct,
        remote_url: str,
        sales_channel_view: Optional[SimpleNamespace] = None,
    ) -> DummyRemoteProduct:
        assign = self._build_assign(
            sales_channel=sales_channel,
            product=product,
            remote_url=remote_url,
            sales_channel_view=sales_channel_view,
        )
        return DummyRemoteProduct(
            sales_channel=sales_channel,
            multi_tenant_company=self.company,
            local_instance=product,
            cached_assignments=[assign],
        )

    def _property_cache(self, entries: Iterable[Tuple[Tuple[int, int], DummyProductProperty]]) -> Dict[Tuple[int, int], DummyProductProperty]:
        return {key: value for key, value in entries}

    def test_build_payload_for_simple_product(self) -> None:
        sales_channel = self._build_sales_channel()
        product = DummyProduct(
            id=1,
            sku="SKU123",
            name="Product Name",
            ean_code="0123456789012",
            active=True,
            allow_backorder=False,
            price=Decimal("100"),
            sale_price=Decimal("80"),
            product_rule="Shoes",
            url_key="SKU123",
        )
        remote_product = self._build_remote_product(
            sales_channel=sales_channel,
            product=product,
            remote_url="https://shop.example.com/SKU123",
        )

        translation = SimpleNamespace(
            language="en",
            sales_channel_id=sales_channel.id,
            name="Translated name",
            description="Translated description",
        )

        property_cache = self._property_cache(
            [
                ((product.id, self.config.mpn_property_id), DummyProductProperty(value="MPN-001")),
                ((product.id, self.config.brand_property_id), DummyProductProperty(value="Acme")),
                ((product.id, self.config.material_property_id), DummyProductProperty(value="Cotton")),
                ((product.id, self.config.length_property_id), DummyProductProperty(value="10")),
                ((product.id, self.config.width_property_id), DummyProductProperty(value="5")),
                ((product.id, self.config.height_property_id), DummyProductProperty(value="2")),
                ((product.id, self.config.weight_property_id), DummyProductProperty(value="2")),
                ((product.id, self.config.age_group_property_id), DummyProductProperty(value_select_id=self.config.age_group_kids_value.id)),
                ((product.id, self.config.expiration_date_property_id), DummyProductProperty(value="2025-12-01")),
                ((product.id, self.config.pickup_method_property_id), DummyProductProperty(value_select_id=self.config.pickup_method_in_store_value.id)),
                ((product.id, self.config.color_property_id), DummyProductProperty(value="Red")),
                ((product.id, self.config.size_property_id), DummyProductProperty(value="L")),
                ((product.id, self.config.size_system_property_id), DummyProductProperty(value="US")),
                ((product.id, self.config.gender_property_id), DummyProductProperty(value="unisex")),
                ((product.id, self.config.popularity_score_property_id), DummyProductProperty(value="9.5")),
                ((product.id, self.config.warning_property_id), DummyProductProperty(value="Choking hazard")),
                ((product.id, self.config.age_restriction_property_id), DummyProductProperty(value="18+")),
                ((product.id, self.config.condition_property_id), DummyProductProperty(value_select_id=self.config.condtion_new_value.id)),
            ]
        )

        main_image = DummyMediaAssignment(
            media=DummyMedia(
                media_type=Media.IMAGE,
                thumbnail="https://cdn.example.com/thumb.jpg",
                image="https://cdn.example.com/main.jpg",
            ),
            is_main_image=True,
            sort_order=0,
            id=1,
        )
        extra_image = DummyMediaAssignment(
            media=DummyMedia(
                media_type=Media.IMAGE,
                image="https://cdn.example.com/additional.jpg",
            ),
            sort_order=1,
            id=2,
        )
        video = DummyMediaAssignment(
            media=DummyMedia(
                media_type=Media.VIDEO,
                video="https://cdn.example.com/video.mp4",
            ),
            sort_order=0,
            id=3,
        )

        translations_map = {product.id: [translation]}
        media_map = {product.id: {"channel": [main_image, extra_image, video]}}

        with patch.object(ProductFeedPayloadFactory, "_load_config", return_value=self.config), patch.object(
            ProductFeedPayloadFactory, "_load_configurator_items", return_value=[]
        ):
            factory = ProductFeedPayloadFactory(remote_product=remote_product)

        with patch.object(ProductFeedPayloadFactory, "_resolve_products", return_value=[product]), patch.object(
            ProductFeedPayloadFactory, "_prepare_property_cache", return_value=property_cache
        ), patch.object(
            ProductFeedPayloadFactory, "_prepare_translations", return_value=translations_map
        ), patch.object(
            ProductFeedPayloadFactory, "_prepare_media", return_value=media_map
        ):
            payloads = factory.build()

        self.assertEqual(len(payloads), 1)
        payload = payloads[0]
        expected = {
            "enable_search": True,
            "enable_checkout": True,
            "id": "SKU123",
            "gtin": "0123456789012",
            "mpn": "MPN-001",
            "title": "Translated name",
            "description": "Translated description",
            "link": "https://shop.example.com/SKU123",
            "condition": "new",
            "product_category": "Shoes",
            "brand": "Acme",
            "material": "Cotton",
            "length": "10",
            "width": "5",
            "height": "2",
            "weight": "2 lb",
            "dimensions": "10x5x2 in",
            "age_group": "kids",
            "image_link": "https://cdn.example.com/thumb.jpg",
            "additional_image_link": ["https://cdn.example.com/additional.jpg"],
            "video_link": "https://cdn.example.com/video.mp4",
            "price": "100.00",
            "sale_price": "80.00",
            "availability": "in_stock",
            "availability_date": None,
            "inventory_quantity": 7,
            "expiration_date": "2025-12-01",
            "pickup_method": "in_store",
            "item_group_id": None,
            "item_group_title": None,
            "color": "Red",
            "size": "L",
            "size_system": "US",
            "gender": "unisex",
            "offer_id": "SKU123-Blue-100.00",
            "custom_variant1_category": None,
            "custom_variant1_option": None,
            "custom_variant2_category": None,
            "custom_variant2_option": None,
            "custom_variant3_category": None,
            "custom_variant3_option": None,
            "seller_name": "Blue",
            "seller_url": "https://seller.example.com",
            "seller_privacy_policy": "https://seller.example.com/privacy",
            "seller_tos": "https://seller.example.com/tos",
            "return_policy": "https://seller.example.com/returns",
            "return_window": 30,
            "popularity_score": "9.5",
            "warning": "Choking hazard",
            "age_restriction": "18+",
        }

        for key, value in expected.items():
            self.assertEqual(payload[key], value, msg=f"Mismatch for key '{key}'")

    def test_preorder_product_uses_mpn_and_default_stock(self) -> None:
        sales_channel = self._build_sales_channel(starting_stock=None, gpt_seller_url="https://channel.example.com")
        product = DummyProduct(
            id=2,
            sku="SKU999",
            name="Backorder Product",
            ean_code=None,
            active=False,
            allow_backorder=True,
            price=Decimal("120"),
            sale_price=None,
            product_rule=None,
            url_key="SKU999",
        )
        remote_product = self._build_remote_product(
            sales_channel=sales_channel,
            product=product,
            remote_url="https://shop.example.com/SKU999",
        )

        translation = SimpleNamespace(
            language="en",
            sales_channel_id=sales_channel.id,
            name="Backorder Product",
            description="Preorder item",
        )

        property_cache = self._property_cache(
            [
                ((product.id, self.config.mpn_property_id), DummyProductProperty(value="MPN-ONLY")),
            ]
        )

        with patch.object(ProductFeedPayloadFactory, "_load_config", return_value=self.config), patch.object(
            ProductFeedPayloadFactory, "_load_configurator_items", return_value=[]
        ):
            factory = ProductFeedPayloadFactory(remote_product=remote_product)

        preorder_date = timezone.now().date().isoformat()
        with patch.object(ProductFeedPayloadFactory, "_resolve_products", return_value=[product]), patch.object(
            ProductFeedPayloadFactory, "_prepare_property_cache", return_value=property_cache
        ), patch.object(
            ProductFeedPayloadFactory, "_prepare_translations", return_value={product.id: [translation]}
        ), patch.object(
            ProductFeedPayloadFactory, "_prepare_media", return_value={}
        ):
            payload = factory.build()[0]

        self.assertEqual(payload["availability"], "preorder")
        self.assertEqual(payload["availability_date"], preorder_date)
        self.assertIsNone(payload["gtin"])
        self.assertEqual(payload["mpn"], "MPN-ONLY")
        self.assertEqual(payload["inventory_quantity"], 1)
        self.assertEqual(payload["seller_url"], "https://channel.example.com")
        self.assertEqual(payload["offer_id"], "SKU999-Blue-120.00")
        self.assertIsNone(payload["sale_price"])

    def test_configurable_product_generates_payloads_for_variations(self) -> None:
        sales_channel = self._build_sales_channel()
        parent_product = DummyProduct(
            id=10,
            sku="PARENT",
            name="Parent",
            ean_code="1234567890123",
            active=True,
            allow_backorder=False,
            price=Decimal("0"),
            sale_price=None,
            product_rule="Shoes",
            configurable=True,
            url_key="parent",
        )
        variation_one = DummyProduct(
            id=11,
            sku="VAR-RED",
            name="Variant Red",
            ean_code="1111111111111",
            active=True,
            allow_backorder=False,
            price=Decimal("120"),
            sale_price=Decimal("90"),
            product_rule="Shoes",
            url_key="var-red",
        )
        variation_two = DummyProduct(
            id=12,
            sku="VAR-BLUE",
            name="Variant Blue",
            ean_code="9876543210987",
            active=False,
            allow_backorder=False,
            price=Decimal("150"),
            sale_price=None,
            product_rule="Shoes",
            url_key="var-blue",
        )

        sales_channel_view = SimpleNamespace(base_url="https://shop.example.com")
        remote_product = self._build_remote_product(
            sales_channel=sales_channel,
            product=parent_product,
            remote_url="https://shop.example.com/PARENT",
            sales_channel_view=sales_channel_view,
        )

        translations_map = {
            parent_product.id: [
                SimpleNamespace(
                    language="en",
                    sales_channel_id=sales_channel.id,
                    name="Parent Title",
                    description="Parent description",
                )
            ],
            variation_one.id: [
                SimpleNamespace(
                    language="en",
                    sales_channel_id=sales_channel.id,
                    name="Variant Red Title",
                    description="Variant Red description",
                )
            ],
            variation_two.id: [
                SimpleNamespace(
                    language="en",
                    sales_channel_id=sales_channel.id,
                    name="Variant Blue Title",
                    description="Variant Blue description",
                )
            ],
        }

        configurator_items = [
            DummyConfiguratorItem(property_id=self.config.color_property_id, property=SimpleNamespace(name="Color")),
            DummyConfiguratorItem(property_id=self.config.size_property_id, property=SimpleNamespace(name="Size")),
            DummyConfiguratorItem(property_id=50, property=SimpleNamespace(name="Capacity")),
        ]

        property_cache_entries: List[Tuple[Tuple[int, int], DummyProductProperty]] = [
            ((variation_one.id, self.config.mpn_property_id), DummyProductProperty(value="MPN-A")),
            ((variation_one.id, self.config.brand_property_id), DummyProductProperty(value="Acme")),
            ((variation_one.id, self.config.material_property_id), DummyProductProperty(value="Leather")),
            ((variation_one.id, self.config.length_property_id), DummyProductProperty(value="10")),
            ((variation_one.id, self.config.width_property_id), DummyProductProperty(value="5")),
            ((variation_one.id, self.config.height_property_id), DummyProductProperty(value="2")),
            ((variation_one.id, self.config.weight_property_id), DummyProductProperty(value="3")),
            ((variation_one.id, self.config.age_group_property_id), DummyProductProperty(value_select_id=self.config.age_group_adult_value.id)),
            ((variation_one.id, self.config.expiration_date_property_id), DummyProductProperty(value="2030-01-01")),
            ((variation_one.id, self.config.pickup_method_property_id), DummyProductProperty(value_select_id=self.config.pickup_method_in_store_value.id)),
            ((variation_one.id, self.config.color_property_id), DummyProductProperty(value="Red")),
            ((variation_one.id, self.config.size_property_id), DummyProductProperty(value="M")),
            ((variation_one.id, self.config.size_system_property_id), DummyProductProperty(value="US")),
            ((variation_one.id, self.config.gender_property_id), DummyProductProperty(value="unisex")),
            ((variation_one.id, self.config.popularity_score_property_id), DummyProductProperty(value="4.8")),
            ((variation_one.id, self.config.warning_property_id), DummyProductProperty(value="Keep away from fire")),
            ((variation_one.id, self.config.age_restriction_property_id), DummyProductProperty(value="13+")),
            ((variation_one.id, self.config.condition_property_id), DummyProductProperty(value_select_id=self.config.condtion_refurbished_value.id)),
            ((variation_one.id, 50), DummyProductProperty(value="128GB")),
            ((variation_two.id, self.config.mpn_property_id), DummyProductProperty(value="MPN-B")),
            ((variation_two.id, self.config.brand_property_id), DummyProductProperty(value="Acme")),
            ((variation_two.id, self.config.material_property_id), DummyProductProperty(value="Canvas")),
            ((variation_two.id, self.config.length_property_id), DummyProductProperty(value="12")),
            ((variation_two.id, self.config.weight_property_id), DummyProductProperty(value="3.5")),
            ((variation_two.id, self.config.pickup_method_property_id), DummyProductProperty(value_select_id=self.config.pickup_method_reserve_value.id)),
            ((variation_two.id, self.config.color_property_id), DummyProductProperty(value="Blue")),
            ((variation_two.id, self.config.size_property_id), DummyProductProperty(value="L")),
            ((variation_two.id, self.config.size_system_property_id), DummyProductProperty(value="US")),
            ((variation_two.id, self.config.gender_property_id), DummyProductProperty(value="unisex")),
            ((variation_two.id, self.config.popularity_score_property_id), DummyProductProperty(value="4.1")),
            ((variation_two.id, self.config.condition_property_id), DummyProductProperty(value_select_id=self.config.condtion_usd_value.id)),
            ((variation_two.id, 50), DummyProductProperty(value="256GB")),
        ]
        property_cache = self._property_cache(property_cache_entries)

        parent_media = DummyMediaAssignment(
            media=DummyMedia(
                media_type=Media.IMAGE,
                thumbnail="https://cdn.example.com/thumb.jpg",
                image="https://cdn.example.com/parent.jpg",
            ),
            is_main_image=True,
            sort_order=0,
            id=1,
        )
        parent_additional = DummyMediaAssignment(
            media=DummyMedia(
                media_type=Media.IMAGE,
                image="https://cdn.example.com/additional.jpg",
            ),
            sort_order=1,
            id=2,
        )
        media_map = {parent_product.id: {"channel": [parent_media, parent_additional]}}

        with patch("llm.factories.product_feed.SalesChannelViewAssign", StubSalesChannelViewAssign):
            with patch.object(ProductFeedPayloadFactory, "_load_config", return_value=self.config), patch.object(
                ProductFeedPayloadFactory, "_load_configurator_items", return_value=configurator_items
            ):
                factory = ProductFeedPayloadFactory(remote_product=remote_product)

            with patch.object(ProductFeedPayloadFactory, "_resolve_products", return_value=[variation_one, variation_two]), patch.object(
                ProductFeedPayloadFactory, "_prepare_property_cache", return_value=property_cache
            ), patch.object(
                ProductFeedPayloadFactory, "_prepare_translations", return_value=translations_map
            ), patch.object(
                ProductFeedPayloadFactory, "_prepare_media", return_value=media_map
            ):
                payloads = factory.build()

        self.assertEqual(len(payloads), 2)

        first, second = payloads
        self.assertEqual(first["item_group_id"], "PARENT")
        self.assertEqual(first["item_group_title"], "Parent Title")
        self.assertEqual(first["color"], "Red")
        self.assertEqual(first["size"], "M")
        self.assertEqual(first["custom_variant1_category"], "Capacity")
        self.assertEqual(first["custom_variant1_option"], "128GB")
        self.assertEqual(first["custom_variant2_category"], None)
        self.assertEqual(first["custom_variant3_category"], None)
        self.assertEqual(first["availability"], "in_stock")
        self.assertIsNone(first["availability_date"])
        self.assertEqual(first["link"], "https://shop.example.com/VAR-RED")
        self.assertEqual(first["condition"], "refurbished")
        self.assertEqual(first["dimensions"], "10x5x2 in")
        self.assertEqual(first["weight"], "3 lb")
        self.assertEqual(first["age_group"], "adult")
        self.assertEqual(first["pickup_method"], "in_store")
        self.assertEqual(first["price"], "120.00")
        self.assertEqual(first["sale_price"], "90.00")
        self.assertEqual(first["mpn"], "MPN-A")
        self.assertEqual(first["offer_id"], "VAR-RED-Blue-120.00")
        self.assertEqual(first["image_link"], "https://cdn.example.com/thumb.jpg")
        self.assertEqual(first["additional_image_link"], ["https://cdn.example.com/additional.jpg"])
        self.assertEqual(first["popularity_score"], "4.8")
        self.assertEqual(first["warning"], "Keep away from fire")
        self.assertEqual(first["age_restriction"], "13+")

        self.assertEqual(second["item_group_id"], "PARENT")
        self.assertEqual(second["item_group_title"], "Parent Title")
        self.assertEqual(second["color"], "Blue")
        self.assertEqual(second["size"], "L")
        self.assertEqual(second["custom_variant1_option"], "256GB")
        self.assertEqual(second["availability"], "out_of_stock")
        self.assertIsNone(second["availability_date"])
        self.assertEqual(second["link"], "https://shop.example.com/VAR-BLUE")
        self.assertEqual(second["condition"], "used")
        self.assertIsNone(second["dimensions"])
        self.assertEqual(second["weight"], "3.5 lb")
        self.assertIsNone(second["age_group"])
        self.assertEqual(second["pickup_method"], "reserve")
        self.assertEqual(second["price"], "150.00")
        self.assertIsNone(second["sale_price"])
        self.assertEqual(second["mpn"], "MPN-B")
        self.assertEqual(second["offer_id"], "VAR-BLUE-Blue-150.00")
        self.assertEqual(second["image_link"], "https://cdn.example.com/thumb.jpg")
        self.assertEqual(second["additional_image_link"], ["https://cdn.example.com/additional.jpg"])
        self.assertEqual(second["popularity_score"], "4.1")
        self.assertIsNone(second["warning"])
        self.assertIsNone(second["age_restriction"])

    def test_disabled_channel_raises_configuration_error(self) -> None:
        sales_channel = self._build_sales_channel(gpt_enable=False)
        product = DummyProduct(
            id=99,
            sku="DISABLED",
            name="Disabled",
            ean_code=None,
            active=True,
            allow_backorder=False,
            price=Decimal("10"),
            sale_price=None,
            product_rule=None,
            url_key="disabled",
        )
        remote_product = self._build_remote_product(
            sales_channel=sales_channel,
            product=product,
            remote_url="https://shop.example.com/DISABLED",
        )

        with self.assertRaises(ProductFeedConfigurationError):
            ProductFeedPayloadFactory(remote_product=remote_product)
