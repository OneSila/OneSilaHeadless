from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from properties.models import ProductProperty, ProductPropertyTextTranslation, Property
from sales_channels.integrations.shein.factories.products import SheinProductCreateFactory
from sales_channels.integrations.shein.models import SheinInternalProperty, SheinSalesChannel
from sales_channels.models import SalesChannelView, SalesChannelViewAssign
from sales_channels.models.products import RemoteProduct


class SheinProductDimensionMappingTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
        )
        self.remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="REMOTE-SKU-1",
            remote_sku="REMOTE-SKU-1",
        )
        self.view = SalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

    def _make_property(
        self,
        code: str,
        *,
        prop_type: str,
        float_value: float | None = None,
        int_value: int | None = None,
        text_value: str | None = None,
    ):
        prop = baker.make(
            Property,
            type=prop_type,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=prop,
            value_float=float_value,
            value_int=int_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        if prop_type == Property.TYPES.TEXT and text_value is not None:
            ProductPropertyTextTranslation.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product_property=product_property,
                language=self.multi_tenant_company.language,
                value_text=text_value,
            )
        SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code=code,
            name=code,
            type=prop_type,
            payload_field=code,
            local_instance=prop,
        )

    def test_dimensions_and_weight_come_from_internal_properties(self):
        self._make_property("height", prop_type=Property.TYPES.FLOAT, float_value=12.3)
        self._make_property("length", prop_type=Property.TYPES.FLOAT, float_value=14.5)
        self._make_property("width", prop_type=Property.TYPES.FLOAT, float_value=9.8)
        self._make_property("weight", prop_type=Property.TYPES.INT, int_value=750)
        self._make_property("supplier_code", prop_type=Property.TYPES.TEXT, text_value="SUP-DIM-1")

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )

        assigns = list(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.product,
            ).select_related("sales_channel_view")
        )
        sku_list = factory._build_sku_list(assigns=assigns)
        sku = sku_list[0]

        self.assertEqual(sku["height"], "12.3")
        self.assertEqual(sku["length"], "14.5")
        self.assertEqual(sku["width"], "9.8")
        self.assertEqual(sku["weight"], 750)
