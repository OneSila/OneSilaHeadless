from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.utils import timezone
from model_bakery import baker

from core.tests import TransactionTestCase
from media.models import Media, MediaProductThrough
from products.models import ProductTranslation
from properties.models import (
    ProductProperty,
    Property,
    PropertySelectValue,
    ProductPropertiesRule,
)
from sales_channels.integrations.ebay.models import (
    EbayProduct,
    EbayProductOffer,
    EbaySalesChannel,
)
from sales_channels.integrations.ebay.models.properties import EbayProductType
from sales_channels.integrations.ebay.models.properties import (
    EbayInternalProperty,
    EbayProperty,
    EbayPropertySelectValue,
)
from sales_channels.integrations.ebay.models.sales_channels import (
    EbayRemoteLanguage,
    EbaySalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign


def _defer_patch(patcher):
    """Ensure started patchers are stopped via addCleanup."""
    return patcher.start()


class TestCaseEbayMixin(TransactionTestCase):
    def setUp(self):
        super().setUp()
        refresh_expiration = timezone.now() + timedelta(days=1)
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname='test.ebay',
            environment=EbaySalesChannel.PRODUCTION,
            active=True,
            multi_tenant_company=self.multi_tenant_company,
            refresh_token='test-refresh-token',
            refresh_token_expiration=refresh_expiration,
        )

        product_type_rule_task_patcher = patch(
            "sales_channels.integrations.ebay.tasks.ebay_product_type_rule_sync_task",
        )
        self.ebay_product_type_rule_sync_task = product_type_rule_task_patcher.start()
        self.ebay_product_type_rule_sync_task.delay = MagicMock()
        self.addCleanup(product_type_rule_task_patcher.stop)


class EbayProductPushFactoryTestBase(TestCaseEbayMixin):
    """Shared setup for eBay product push factory tests."""

    def setUp(self):
        super().setUp()

        signal_names = [
            "create_remote_product",
            "delete_remote_product",
            "update_remote_product",
            "sync_remote_product",
            "manual_sync_remote_product",
            "create_remote_product_property",
            "update_remote_product_property",
            "delete_remote_product_property",
            "update_remote_price",
            "update_remote_product_content",
            "update_remote_product_eancode",
            "add_remote_product_variation",
            "remove_remote_product_variation",
            "create_remote_image_association",
            "update_remote_image_association",
            "delete_remote_image_association",
            "delete_remote_image",
            "sales_view_assign_updated",
        ]

        from sales_channels import signals as sc_signals

        self._signal_patchers = [
            patch.object(getattr(sc_signals, name), "send", return_value=[])
            for name in signal_names
        ]
        for patcher in self._signal_patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

        api_patcher = patch(
            "sales_channels.integrations.ebay.factories.products.mixins.GetEbayAPIMixin.get_api",
            return_value=MagicMock(),
        )
        self._api_patcher = api_patcher
        self._api_patcher.start()
        self.addCleanup(self._api_patcher.stop)

        translate_property_patcher = patch(
            "sales_channels.integrations.ebay.tasks.ebay_translate_property_task"
        )
        translate_property = _defer_patch(translate_property_patcher)
        translate_property.delay = MagicMock()
        self.addCleanup(translate_property_patcher.stop)

        translate_select_value_patcher = patch(
            "sales_channels.integrations.ebay.tasks.ebay_translate_select_value_task"
        )
        translate_select_value = _defer_patch(translate_select_value_patcher)
        translate_select_value.delay = MagicMock()
        self.addCleanup(translate_select_value_patcher.stop)

        populate_media_title_patcher = patch("media.tasks.populate_media_title_task")
        populate_media_title = _defer_patch(populate_media_title_patcher)
        populate_media_title.delay = MagicMock()
        self.addCleanup(populate_media_title_patcher.stop)

        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            remote_id="EBAY_GB",
            is_default=True,
            length_unit="CENTIMETER",
            weight_unit="KILOGRAM",
        )
        EbayRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance="en-us",
            remote_code="en_US",
        )

        self.product = baker.make(
            "products.Product",
            sku="TEST-SKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslation.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            language="en-us",
            name="Test Product",
            subtitle="Short subtitle",
            description="Full description",
            short_description="Listing description",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.brand_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.brand_value = baker.make(
            PropertySelectValue,
            property=self.brand_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.brand_product_property = ProductProperty.objects.create(
            product=self.product,
            property=self.brand_property,
            value_select=self.brand_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_brand = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=self.brand_property,
            localized_name="Brand",
        )
        EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            ebay_property=self.remote_brand,
            local_instance=self.brand_value,
            localized_value="Acme",
        )

        self.weight_property = baker.make(
            Property,
            type=Property.TYPES.FLOAT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.weight_product_property = ProductProperty.objects.create(
            product=self.product,
            property=self.weight_property,
            value_float=2.5,
            multi_tenant_company=self.multi_tenant_company,
        )
        EbayInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.weight_property,
            code="packageWeightAndSize__weight__value",
            name="Weight",
            type=Property.TYPES.FLOAT,
            is_root=True,
        )

        self.product_type_property = Property.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
        ).first()
        if self.product_type_property is None:
            self.product_type_property = baker.make(
                Property,
                type=Property.TYPES.SELECT,
                is_product_type=True,
                multi_tenant_company=self.multi_tenant_company,
            )

        self.product_type_value = PropertySelectValue.objects.filter(
            property=self.product_type_property,
        ).first()
        if self.product_type_value is None:
            self.product_type_value = baker.make(
                PropertySelectValue,
                property=self.product_type_property,
                multi_tenant_company=self.multi_tenant_company,
            )

        self.product_rule, _ = ProductPropertiesRule.objects.update_or_create(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
            defaults={"require_ean_code": False},
        )
        self._assign_product_type(self.product)

        self.ebay_product_type, _ = EbayProductType.objects.update_or_create(
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=self.product_rule,
            multi_tenant_company=self.multi_tenant_company,
            defaults={
                "remote_id": "123456",
                "name": "Home & Garden",
            },
        )
        self.category_id = self.ebay_product_type.remote_id

        self.remote_product = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="REMOTE-SKU",
        )
        self.offer = EbayProductOffer.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
            remote_id="OFFER-123",
        )

        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
        )
        self.media_through = MediaProductThrough.objects.create(
            product=self.product,
            media=media,
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )

        SalesChannelViewAssign.objects.create(
            sales_channel=self.sales_channel,
            product=self.product,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel_view=self.view
        )

    def _assign_product_type(self, product) -> None:
        ProductProperty.objects.update_or_create(
            product=product,
            property=self.product_type_property,
            defaults={
                "multi_tenant_company": self.multi_tenant_company,
                "value_select": self.product_type_value,
            },
        )

    def _build_image_factory(self, *, get_value_only: bool):
        from sales_channels.integrations.ebay.factories.products.images import (
            EbayMediaProductThroughCreateFactory,
        )

        return EbayMediaProductThroughCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=get_value_only,
        )
