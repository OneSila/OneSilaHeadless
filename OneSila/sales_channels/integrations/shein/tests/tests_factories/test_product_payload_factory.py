from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from eancodes.models import EanCode
from products.models import Product
from properties.models import ProductProperty, Property, PropertySelectValue
from sales_channels.integrations.shein.factories.products import (
    SheinProductCreateFactory,
    SheinProductUpdateFactory,
)
from sales_channels.integrations.shein.models import (
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.products import RemoteProduct


class SheinProductPayloadFactoryTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
            starting_stock=5,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SKU-1",
        )
        self.remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="SPU-1",
            remote_sku="SKU-1",
        )
        self.view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
            is_default=True,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

    def test_build_sku_list_includes_supplier_barcode_and_package_type(self) -> None:
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="123-456-7890123",
        )

        package_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        package_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=package_property,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=package_property,
            value_select=package_value,
        )
        internal_property = SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="package_type",
            name="Package type",
            type=Property.TYPES.SELECT,
            payload_field="package_type",
            local_instance=package_property,
        )
        SheinInternalPropertyOption.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_property=internal_property,
            sales_channel=self.sales_channel,
            local_instance=package_value,
            value="3",
            label="Hard packaging",
            sort_order=0,
            raw_data={},
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        sku = factory._build_sku_list(assigns=[])[0]

        self.assertEqual(sku["supplier_barcode"]["barcode"], "1234567890123")
        self.assertEqual(sku["supplier_barcode"]["barcode_type"], "EAN")
        self.assertEqual(sku["package_type"], "3")

    def test_create_payload_omits_spu_name_and_includes_site_list(self) -> None:
        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": "1727", "remote_id": "1080"})()

        with (
            patch.object(SheinProductCreateFactory, "_build_property_payloads"),
            patch.object(SheinProductCreateFactory, "_build_prices"),
            patch.object(SheinProductCreateFactory, "_build_media"),
            patch.object(SheinProductCreateFactory, "_build_translations"),
            patch.object(SheinProductCreateFactory, "_build_skc_list"),
        ):
            payload = factory.build_payload()

        self.assertNotIn("spu_name", payload)
        self.assertIn("site_list", payload)

    def test_update_payload_includes_spu_name_and_omits_site_list(self) -> None:
        factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": "1727", "remote_id": "1080"})()

        with (
            patch.object(SheinProductUpdateFactory, "_build_property_payloads"),
            patch.object(SheinProductUpdateFactory, "_build_prices"),
            patch.object(SheinProductUpdateFactory, "_build_media"),
            patch.object(SheinProductUpdateFactory, "_build_translations"),
            patch.object(SheinProductUpdateFactory, "_build_skc_list"),
        ):
            payload = factory.build_payload()

        self.assertEqual(payload["spu_name"], "SPU-1")
        self.assertNotIn("site_list", payload)
