from sales_channels.integrations.ebay.constants import EBAY_DOCUMENT_TYPE_DEFAULTS
from sales_channels.integrations.ebay.flows.document_types import (
    ensure_ebay_document_types_flow,
)
from sales_channels.integrations.ebay.models import EbayDocumentType
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    TestCaseEbayMixin,
)


class EbayDocumentTypeFlowTestCase(TestCaseEbayMixin):
    def test_flow_creates_all_default_document_types(self):
        EbayDocumentType.objects.filter(sales_channel=self.sales_channel).delete()

        ensure_ebay_document_types_flow(sales_channel=self.sales_channel)

        self.assertEqual(
            EbayDocumentType.objects.filter(sales_channel=self.sales_channel).count(),
            len(EBAY_DOCUMENT_TYPE_DEFAULTS),
        )

        for definition in EBAY_DOCUMENT_TYPE_DEFAULTS:
            doc_type = EbayDocumentType.objects.get(
                sales_channel=self.sales_channel,
                remote_id=definition["value"],
            )
            self.assertEqual(doc_type.multi_tenant_company_id, self.multi_tenant_company.id)
            self.assertEqual(doc_type.name, definition["name"])
            self.assertEqual(doc_type.description, definition["description"])

    def test_flow_is_idempotent_and_updates_existing_values(self):
        ensure_ebay_document_types_flow(sales_channel=self.sales_channel)

        first_definition = EBAY_DOCUMENT_TYPE_DEFAULTS[0]
        doc_type = EbayDocumentType.objects.get(
            sales_channel=self.sales_channel,
            remote_id=first_definition["value"],
        )
        doc_type.name = "Wrong Name"
        doc_type.description = "Wrong Description"
        doc_type.save(update_fields=["name", "description"])

        ensure_ebay_document_types_flow(sales_channel=self.sales_channel)

        self.assertEqual(
            EbayDocumentType.objects.filter(sales_channel=self.sales_channel).count(),
            len(EBAY_DOCUMENT_TYPE_DEFAULTS),
        )
        doc_type.refresh_from_db()
        self.assertEqual(doc_type.name, first_definition["name"])
        self.assertEqual(doc_type.description, first_definition["description"])
