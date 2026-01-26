from core.tests import TestCase
from products.models import Product
from sales_channels.exceptions import InspectorMissingInformationError
from sales_channels.factories.products.products import RemoteProductSyncFactory
from unittest.mock import patch

from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.models import RemoteProduct


class DummyRemoteProductSyncFactory(RemoteProductSyncFactory):
    remote_model_class = RemoteProduct

    def __init__(self, *, sales_channel, local_instance, remote_instance, fail_validate: bool = False):
        self.fail_validate = fail_validate
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            remote_instance=remote_instance,
        )
        self.prices_data = {}

    def preflight_check(self):
        return True

    def set_api(self):
        self.api = object()

    def set_type(self):
        self.local_type = Product.SIMPLE

    def initialize_remote_product(self):
        return

    def set_remote_product_for_logging(self):
        self.remote_product = self.remote_instance

    def sanity_check(self):
        return

    def precalculate_progress_step_increment(self, *_args):
        return

    def set_local_assigns(self):
        return

    def validate(self):
        if self.fail_validate:
            raise InspectorMissingInformationError("Missing required information.")

    def set_rule(self):
        return

    def set_product_properties(self):
        self.product_properties = []

    def build_payload(self):
        self.payload = {}

    def process_product_properties(self):
        return

    def customize_payload(self):
        return

    def pre_action_process(self):
        return

    def update_progress(self):
        return

    def perform_remote_action(self):
        return

    def set_discount(self):
        return

    def set_ean_code(self):
        return

    def post_action_process(self):
        return

    def set_content_translations(self):
        return

    def assign_images(self):
        return

    def assign_ean_code(self):
        return

    def assign_saleschannels(self):
        return

    def update_multi_currency_prices(self):
        return

    def create_or_update_children(self):
        return

    def add_variation_to_parent(self):
        return

    def final_process(self):
        return

    def log_action(self, *_args, **_kwargs):
        return

    def finalize_progress(self):
        return


class RemoteProductSuccessfullyCreatedTests(TestCase):
    def setUp(self):
        super().setUp()
        self._sales_channel_created_patcher = patch(
            "sales_channels.signals.sales_channel_created.send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self._connect_patcher = patch.object(
            MagentoSalesChannel,
            "connect",
            return_value=None,
        )
        self._connect_patcher.start()
        self.addCleanup(self._connect_patcher.stop)

        self.sales_channel = MagentoSalesChannel.objects.create(
            hostname="https://magento.example.com",
            host_api_username="api-user",
            host_api_key="api-key",
            authentication_method=MagentoSalesChannel.AUTH_METHOD_CHOICES[0][0],
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="SYNC-001",
        )
        self.remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            successfully_created=True,
        )

    def test_sets_successfully_created_false_on_validation_error(self):
        factory = DummyRemoteProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            fail_validate=True,
        )

        with self.assertRaises(InspectorMissingInformationError):
            factory.run()

        self.remote_product.refresh_from_db()
        self.assertFalse(self.remote_product.successfully_created)

    def test_sets_successfully_created_true_on_success(self):
        self.remote_product.successfully_created = False
        self.remote_product.save(update_fields=["successfully_created"])

        factory = DummyRemoteProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
        )
        factory.run()

        self.remote_product.refresh_from_db()
        self.assertTrue(self.remote_product.successfully_created)
