from django.core.exceptions import ValidationError
from model_bakery import baker

from core.tests import TestCase
from properties.models import Property
from sales_channels.integrations.ebay.models import (
    EbayInternalProperty,
    EbaySalesChannel,
    EbayCategory,
    EbayDocumentType,
    EbaySalesChannelView,
)


class EbayInternalPropertyModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_allowed_types_default_is_loaded_from_constants(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.INT,
        )

        internal_property = EbayInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="packageWeightAndSize__dimensions__length",
            name="Package Length",
            type=Property.TYPES.FLOAT,
            local_instance=local_property,
            is_root=True,
        )

        self.assertEqual(
            internal_property.allowed_types,
            [Property.TYPES.FLOAT, Property.TYPES.INT],
        )

    def test_type_must_be_in_allowed_types(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )

        with self.assertRaises(ValidationError):
            EbayInternalProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                code="packageWeightAndSize__dimensions__length",
                name="Package Length",
                type=Property.TYPES.TEXT,
                local_instance=local_property,
                is_root=True,
            )

    def test_local_instance_type_must_be_allowed(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.FLOAT,
        )

        with self.assertRaises(ValidationError):
            EbayInternalProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                code="isbn",
                name="ISBN",
                type=Property.TYPES.TEXT,
                local_instance=local_property,
                is_root=False,
            )


class EbayDocumentTypeModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="ebay-doc-types.test",
        )
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="EBAY_US",
            name="US",
            default_category_tree_id="0",
        )

    def test_save_accepts_existing_category_remote_ids(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="100",
            name="Leaf 100",
            full_name="Leaf 100",
            has_children=False,
        )
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="101",
            name="Leaf 101",
            full_name="Leaf 101",
            has_children=False,
        )

        document_type = EbayDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CERTIFICATE_OF_ANALYSIS",
            name="Certificate of Analysis",
            required_categories=["100"],
            optional_categories=[{"remote_id": "101"}],
        )

        self.assertEqual(document_type.required_categories, ["100"])
        self.assertEqual(document_type.optional_categories, ["101"])

    def test_save_rejects_unknown_category_remote_ids(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="0",
            remote_id="100",
            name="Leaf 100",
            full_name="Leaf 100",
            has_children=False,
        )

        with self.assertRaises(ValidationError):
            EbayDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_id="CERTIFICATE_OF_CONFORMITY",
                required_categories=["999"],
                optional_categories=[],
            )

    def test_save_rejects_remote_ids_not_in_channel_tree(self):
        EbayCategory.objects.create(
            marketplace_default_tree_id="999",
            remote_id="200",
            name="Other Tree Leaf",
            full_name="Other Tree Leaf",
            has_children=False,
        )

        with self.assertRaises(ValidationError):
            EbayDocumentType.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_id="DECLARATION_OF_CONFORMITY",
                required_categories=["200"],
                optional_categories=[],
            )
