from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.shein.factories.products import (
    SheinProductCreateFactory,
    SheinProductUpdateFactory,
)
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel
from sales_channels.models.logs import RemoteLog


class SheinProductIdentifierTestCase(TestCase):
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
            sku="SKU-ID-1",
        )
        self.remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="SPU-ID-1",
            remote_sku="SKU-ID-1",
            spu_name="SPU-ID-1",
            syncing_current_percentage=100,
        )

    def test_identifiers_use_shein_base_factory(self) -> None:
        create_factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        update_factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
        )

        create_identifier, create_fixing = create_factory.get_identifiers()
        update_identifier, update_fixing = update_factory.get_identifiers()

        self.assertTrue(create_identifier.startswith("SheinProductBaseFactory:"))
        self.assertTrue(update_identifier.startswith("SheinProductBaseFactory:"))
        self.assertEqual(create_fixing, "SheinProductBaseFactory:run")
        self.assertEqual(update_fixing, "SheinProductBaseFactory:run")

    def test_create_failure_is_cleared_by_update_success(self) -> None:
        create_factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        update_factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
        )

        create_identifier, create_fixing = create_factory.get_identifiers()
        update_identifier, _ = update_factory.get_identifiers()

        self.remote_product.add_admin_error(
            action=RemoteLog.ACTION_CREATE,
            response="Create failed",
            payload={},
            error_traceback="traceback",
            identifier=create_identifier,
            fixing_identifier=create_fixing,
            remote_product=self.remote_product,
        )
        self.assertTrue(self.remote_product.has_errors)

        self.remote_product.add_log(
            action=RemoteLog.ACTION_UPDATE,
            response={},
            payload={},
            identifier=update_identifier,
            remote_product=self.remote_product,
        )

        self.assertFalse(self.remote_product.has_errors)
