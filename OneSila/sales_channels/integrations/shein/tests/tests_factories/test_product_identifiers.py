from unittest.mock import MagicMock, patch

from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.shein.factories.products import (
    SheinProductCreateFactory,
    SheinProductUpdateFactory,
)
from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel
from sales_channels.models.logs import RemoteLog
from sales_channels.models.products import RemoteProduct


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

    def _build_publish_response(self) -> MagicMock:
        response = MagicMock()
        response.json.return_value = {
            "code": "0",
            "msg": "Filtered attribute values",
            "info": {
                "success": True,
                "spu_name": "k2603260107694591",
                "skc_list": [
                    {
                        "skc_name": "sk260326010769459125787",
                        "sku_list": [
                            {
                                "sku_code": "I5mn6aqurfimd0",
                                "supplier_sku": "SKU-ID-1",
                            }
                        ],
                    }
                ],
                "version": "SPMP260326016592032",
                "filtered_result": [
                    {
                        "scene": "attribute_filter",
                        "message": "Filtered attribute value",
                    }
                ],
            },
        }
        return response

    @patch.object(SheinProductCreateFactory, "shein_post")
    def test_create_success_with_filtered_result_keeps_pending_approval(self, shein_post: MagicMock) -> None:
        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-ID-1",
        )
        shein_post.return_value = self._build_publish_response()

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=remote_product,
        )
        factory.payload = {"source_system": "openapi"}

        factory.perform_remote_action()
        factory.finalize_progress()

        remote_product.refresh_from_db()
        self.assertEqual(remote_product.remote_id, "k2603260107694591")
        self.assertEqual(remote_product.spu_name, "k2603260107694591")
        self.assertEqual(remote_product.skc_name, "sk260326010769459125787")
        self.assertEqual(remote_product.sku_code, "I5mn6aqurfimd0")
        self.assertEqual(remote_product.status, RemoteProduct.STATUS_PENDING_APPROVAL)

    @patch.object(SheinProductUpdateFactory, "shein_post")
    def test_update_success_with_filtered_result_persists_identifiers(self, shein_post: MagicMock) -> None:
        self.remote_product.remote_id = None
        self.remote_product.spu_name = ""
        self.remote_product.skc_name = ""
        self.remote_product.sku_code = ""
        self.remote_product.status = RemoteProduct.STATUS_COMPLETED
        self.remote_product.save(
            update_fields=["remote_id", "spu_name", "skc_name", "sku_code", "status"],
            skip_status_check=False,
        )
        shein_post.return_value = self._build_publish_response()

        factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
        )
        factory.payload = {"source_system": "openapi"}

        factory.perform_remote_action()
        factory.finalize_progress()

        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.remote_id, "k2603260107694591")
        self.assertEqual(self.remote_product.spu_name, "k2603260107694591")
        self.assertEqual(self.remote_product.skc_name, "sk260326010769459125787")
        self.assertEqual(self.remote_product.sku_code, "I5mn6aqurfimd0")
        self.assertEqual(self.remote_product.status, RemoteProduct.STATUS_PENDING_APPROVAL)
