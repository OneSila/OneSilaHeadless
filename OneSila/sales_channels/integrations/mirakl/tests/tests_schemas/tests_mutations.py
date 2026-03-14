from unittest.mock import patch

from django.db import transaction
from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelImport


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

START_MIRAKL_SCHEMA_IMPORT_MUTATION = """
mutation ($instance: MiraklSalesChannelPartialInput!) {
  startMiraklSchemaImport(instance: $instance) {
    id
    type
    status
    name
  }
}
"""

class MiraklMutationTests(TransactionTestCaseMixin, TransactionTestCase):
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

    @patch("sales_channels.integrations.mirakl.tasks.mirakl_import_db_task")
    def test_start_schema_import_creates_import_and_dispatches_task(self, import_task_mock):
        response = self.strawberry_test_client(
            query=START_MIRAKL_SCHEMA_IMPORT_MUTATION,
            variables={
                "instance": {
                    "id": self.to_global_id(self.sales_channel),
                },
            },
        )

        self.assertIsNone(response.errors)
        transaction.on_commit(lambda: None)
        import_process = MiraklSalesChannelImport.objects.get(
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelImport.TYPE_SCHEMA,
        )
        self.assertEqual(response.data["startMiraklSchemaImport"]["type"], MiraklSalesChannelImport.TYPE_SCHEMA)
        self.assertEqual(response.data["startMiraklSchemaImport"]["status"], MiraklSalesChannelImport.STATUS_NEW)
        self.assertTrue(MiraklSalesChannelImport.objects.filter(id=import_process.id).exists())
