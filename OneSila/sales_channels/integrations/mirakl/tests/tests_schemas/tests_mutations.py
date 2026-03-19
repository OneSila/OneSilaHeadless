from unittest.mock import patch

from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelImport
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


VALIDATE_MIRAKL_CREDENTIALS_MUTATION = """
mutation ($instance: MiraklSalesChannelPartialInput!) {
  validateMiraklCredentials(instance: $instance) {
    id
    hostname
    rawData
  }
}
"""

REFRESH_MIRAKL_METADATA_MUTATION = """
mutation ($instance: MiraklSalesChannelPartialInput!) {
  refreshMiraklMetadata(instance: $instance) {
    id
    hostname
  }
}
"""

CREATE_SALES_IMPORT_PROCESS_MUTATION = """
mutation ($data: SalesChannelImportInput!) {
  createSalesImportProcess(data: $data) {
    id
    importId
    status
    percentage
    __typename
  }
}
"""

CREATE_MIRAKL_IMPORT_PROCESS_MUTATION = """
mutation ($data: MiraklSalesChannelImportInput!) {
  createMiraklImportProcess(data: $data) {
    id
    status
    type
    __typename
  }
}
"""

class MiraklMutationTests(
    DisableMiraklConnectionMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.product_type_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            is_product_type=True,
        )
        self.product_type = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type,
            language=self.multi_tenant_company.language,
            value="Clothing",
        )

    @patch("sales_channels.integrations.mirakl.schema.mutations.refresh_website_pull_models.send")
    @patch("sales_channels.integrations.mirakl.schema.mutations.ValidateMiraklCredentialsFactory")
    def test_validate_credentials_mutation_runs_factory_and_refreshes_metadata(
        self,
        factory_cls,
        signal_send_mock,
    ):
        response = self.strawberry_test_client(
            query=VALIDATE_MIRAKL_CREDENTIALS_MUTATION,
            variables={
                "instance": {
                    "id": self.to_global_id(self.sales_channel),
                },
            },
        )

        self.assertIsNone(response.errors)
        factory_cls.assert_called_once_with(sales_channel=self.sales_channel)
        factory_cls.return_value.run.assert_called_once_with()
        signal_send_mock.assert_called_once_with(
            sender=self.sales_channel.__class__,
            instance=self.sales_channel,
        )

    @patch("sales_channels.integrations.mirakl.schema.mutations.refresh_website_pull_models.send")
    def test_refresh_metadata_mutation_dispatches_refresh_signal(self, signal_send_mock):
        response = self.strawberry_test_client(
            query=REFRESH_MIRAKL_METADATA_MUTATION,
            variables={
                "instance": {
                    "id": self.to_global_id(self.sales_channel),
                },
            },
        )

        self.assertIsNone(response.errors)
        signal_send_mock.assert_called_once_with(
            sender=self.sales_channel.__class__,
            instance=self.sales_channel,
        )

    def test_create_sales_import_process_creates_mirakl_products_import(self):
        response = self.strawberry_test_client(
            query=CREATE_SALES_IMPORT_PROCESS_MUTATION,
            variables={
                "data": {
                    "salesChannel": {
                        "id": self.to_global_id(self.sales_channel),
                    },
                    "name": MiraklSalesChannelImport.TYPE_PRODUCTS,
                    "status": MiraklSalesChannelImport.STATUS_PENDING,
                    "skipBrokenRecords": True,
                    "updateOnly": True,
                },
            },
        )

        self.assertIsNone(response.errors)
        created_import = MiraklSalesChannelImport.objects.latest("id")
        self.assertEqual(created_import.type, MiraklSalesChannelImport.TYPE_PRODUCTS)
        self.assertTrue(created_import.skip_broken_records)
        self.assertTrue(created_import.update_only)

    def test_create_mirakl_import_process_creates_typed_import(self):
        response = self.strawberry_test_client(
            query=CREATE_MIRAKL_IMPORT_PROCESS_MUTATION,
            variables={
                "data": {
                    "salesChannel": {
                        "id": self.to_global_id(self.sales_channel),
                    },
                    "name": MiraklSalesChannelImport.TYPE_PRODUCTS,
                    "status": MiraklSalesChannelImport.STATUS_PENDING,
                    "type": MiraklSalesChannelImport.TYPE_PRODUCTS,
                },
            },
        )

        self.assertIsNone(response.errors)
        self.assertEqual(
            response.data["createMiraklImportProcess"]["type"],
            MiraklSalesChannelImport.TYPE_PRODUCTS,
        )
        created_import = MiraklSalesChannelImport.objects.latest("id")
        self.assertEqual(created_import.type, MiraklSalesChannelImport.TYPE_PRODUCTS)
