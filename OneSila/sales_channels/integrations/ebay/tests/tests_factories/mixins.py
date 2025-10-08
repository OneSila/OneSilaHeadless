from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.utils import timezone
from model_bakery import baker

from core.tests import TransactionTestCase
from media.models import Media, MediaProductThrough
from products.models import ProductTranslation
from properties.models import ProductProperty, Property, PropertySelectValue
from sales_channels.integrations.ebay.models import EbayProduct, EbaySalesChannel
from sales_channels.integrations.ebay.models.properties import (
    EbayInternalProperty,
    EbayProperty,
    EbayPropertySelectValue,
)
from sales_channels.integrations.ebay.models.sales_channels import (
    EbayRemoteLanguage,
    EbaySalesChannelView,
)
from sales_channels.models.sales_channels import SalesChannelViewAssign


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


class EbayProductPushFactoryTestBase(TestCaseEbayMixin):
    """Shared setup for eBay product push factory tests."""

    def setUp(self):
        super().setUp()

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

        self.remote_product = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="REMOTE-SKU",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
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
