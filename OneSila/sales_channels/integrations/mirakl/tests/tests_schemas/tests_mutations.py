from unittest.mock import patch

from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation
from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


VALIDATE_MIRAKL_CREDENTIALS_MUTATION = """
mutation ($instance: MiraklSalesChannelPartialInput!) {
  validateMiraklCredentials(instance: $instance) {
    __typename
    ... on MiraklSalesChannelType {
      id
      hostname
      rawData
    }
  }
}
"""

REFRESH_MIRAKL_METADATA_MUTATION = """
mutation ($instance: MiraklSalesChannelPartialInput!) {
  refreshMiraklMetadata(instance: $instance) {
    __typename
    ... on MiraklSalesChannelType {
      id
      hostname
    }
  }
}
"""

CREATE_SALES_IMPORT_PROCESS_MUTATION = """
mutation ($data: SalesChannelImportInput!) {
  createSalesImportProcess(data: $data) {
    __typename
    ... on SalesChannelImportType {
      id
      importId
      status
      percentage
    }
  }
}
"""

CREATE_MIRAKL_IMPORT_PROCESS_MUTATION = """
mutation ($data: MiraklSalesChannelImportInput!) {
  createMiraklImportProcess(data: $data) {
    __typename
    ... on MiraklSalesChannelImportType {
      id
      status
      type
    }
  }
}
"""

DUPLICATE_SALES_CHANNEL_SELECT_VALUE_MAPPING_MUTATION = """
mutation (
  $salesChannel: SalesChannelPartialInput!,
  $remotePropertySelectValue: RemotePropertySelectValuePartialInput!,
  $localInstance: PropertySelectValuePartialInput!
) {
  duplicateSalesChannelSelectValueMapping(
    salesChannel: $salesChannel,
    remotePropertySelectValue: $remotePropertySelectValue,
    localInstance: $localInstance
  ) {
    id
    remoteId
    code
    value
    localInstance { id }
    remoteProperty { id }
  }
}
"""

SUGGEST_MIRAKL_CATEGORY_MUTATION = """
mutation ($instance: MiraklSalesChannelPartialInput!) {
  suggestMiraklCategory(instance: $instance) {
    id
    remoteId
    name
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
        self.product_type_property = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
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

    def test_duplicate_mirakl_property_select_value_for_local_instance(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        first_local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        second_local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        remote_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_property,
            representation_type=MiraklProperty.REPRESENTATION_PROPERTY,
            code="occasion",
            type=Property.TYPES.SELECT,
        )
        source = baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=remote_property,
            local_instance=first_local_value,
            code="CASUAL",
            value="Casual",
            value_list_code="occasion",
            value_list_label="Occasion",
            raw_data={"code": "CASUAL"},
        )

        response = self.strawberry_test_client(
            query=DUPLICATE_SALES_CHANNEL_SELECT_VALUE_MAPPING_MUTATION,
            variables={
                "salesChannel": {
                    "id": self.to_global_id(self.sales_channel),
                },
                "remotePropertySelectValue": {
                    "id": self.to_global_id(source),
                },
                "localInstance": {
                    "id": self.to_global_id(second_local_value),
                },
            },
        )

        self.assertIsNone(response.errors)
        payload = response.data["duplicateSalesChannelSelectValueMapping"]
        duplicate = MiraklPropertySelectValue.objects.exclude(id=source.id).get()

        self.assertEqual(payload["id"], self.to_global_id(duplicate))
        self.assertEqual(payload["remoteId"], source.remote_id)
        self.assertEqual(payload["code"], source.code)
        self.assertEqual(payload["value"], source.value)
        self.assertEqual(duplicate.local_instance, second_local_value)
        self.assertEqual(duplicate.remote_property, remote_property)
        self.assertEqual(duplicate.raw_data, source.raw_data)

    def test_suggest_mirakl_category_returns_all_categories(self):
        parent = baker.make(
            "mirakl.MiraklCategory",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="ROOT",
            name="Root",
            level=0,
            is_leaf=False,
        )
        child = baker.make(
            "mirakl.MiraklCategory",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CHILD",
            name="Child",
            parent=parent,
            parent_code="ROOT",
            level=1,
            is_leaf=True,
        )

        response = self.strawberry_test_client(
            query=SUGGEST_MIRAKL_CATEGORY_MUTATION,
            variables={
                "instance": {
                    "id": self.to_global_id(self.sales_channel),
                },
            },
        )

        self.assertIsNone(response.errors)
        payload = response.data["suggestMiraklCategory"]
        self.assertEqual(len(payload), 2)
        remote_ids = {entry["remoteId"] for entry in payload}
        self.assertEqual(remote_ids, {"ROOT", "CHILD"})
        self.assertEqual(
            {entry["id"] for entry in payload},
            {self.to_global_id(parent), self.to_global_id(child)},
        )

    def test_duplicate_mirakl_property_select_value_rejects_non_property_representation(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        first_local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        second_local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        remote_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_property,
            representation_type=MiraklProperty.REPRESENTATION_DEFAULT_VALUE,
            code="occasion",
            type=Property.TYPES.SELECT,
        )
        source = baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=remote_property,
            local_instance=first_local_value,
            code="CASUAL",
            value="Casual",
        )

        response = self.strawberry_test_client(
            query=DUPLICATE_SALES_CHANNEL_SELECT_VALUE_MAPPING_MUTATION,
            variables={
                "salesChannel": {
                    "id": self.to_global_id(self.sales_channel),
                },
                "remotePropertySelectValue": {
                    "id": self.to_global_id(source),
                },
                "localInstance": {
                    "id": self.to_global_id(second_local_value),
                },
            },
        )

        self.assertIn("representation type 'property'", response.errors[0]['message'])
