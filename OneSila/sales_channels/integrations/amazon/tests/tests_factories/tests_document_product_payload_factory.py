import json

import base64
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile

from core.tests import TransactionTestCase
from media.models import DocumentType, Media, MediaProductThrough
from sales_channels.exceptions import PreFlightCheckError
from sales_channels.integrations.amazon.factories.products import AmazonProductCreateFactory
from sales_channels.integrations.amazon.factories.products.images import AmazonMediaProductThroughBase
from sales_channels.integrations.amazon.factories.products.documents import AmazonDocumentThroughProductDeleteFactory
from sales_channels.integrations.amazon.models.documents import (
    AmazonDocumentThroughProduct,
    AmazonDocumentType,
)
from sales_channels.integrations.amazon.models.products import AmazonExternalProductId
from sales_channels.integrations.amazon.models.sales_channels import AmazonRemoteLanguage
from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_channels.integrations.amazon.tests.tests_factories.tests_product_factories import (
    AmazonProductTestMixin,
)


class AmazonDocumentFactoryTestBase(
    DisableWooCommerceSignalsMixin,
    TransactionTestCase,
    AmazonProductTestMixin,
):
    PNG_BYTES = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAOaoSn0AAAAASUVORK5CYII="
    )
    PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
    DOCX_BYTES = b"PK\x03\x04INVALID"

    def setUp(self):
        super().setUp()
        self.setup_product()
        # Keep the listing as product_owner in create-flow tests.
        # If created_asin is empty, AmazonProductCreateFactory flips product_owner=False
        # for ASIN-based listings and document payloads are then filtered by listing-offer rules.
        AmazonExternalProductId.objects.filter(
            product=self.product,
            view=self.view,
            type=AmazonExternalProductId.TYPE_ASIN,
        ).update(created_asin="ASIN123")

    def _mock_amazon_response(self, *, attributes=None):
        response = MagicMock(spec=["submissionId", "processingStatus", "issues", "status"])
        response.submissionId = "mock-submission-id"
        response.processingStatus = "VALID"
        response.status = "VALID"
        response.issues = []
        if attributes is not None:
            response.attributes = attributes
        return response

    def _create_public_definition(self, *, code, usage_definition, raw_schema=None):
        return AmazonPublicDefinition.objects.create(
            api_region_code=self.view.api_region_code,
            product_type_code="CHAIR",
            code=code,
            name=code,
            usage_definition=usage_definition,
            raw_schema=raw_schema,
        )

    def _create_local_document_type(self, *, name):
        return DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name=name,
            description=f"{name} description",
        )

    def _map_document_type(self, *, local_document_type, remote_id, name="Mapped Amazon Document Type"):
        return AmazonDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_document_type,
            remote_id=remote_id,
            name=name,
        )

    def _create_document_media_through(
        self,
        *,
        local_document_type,
        sort_order=0,
        sales_channel=None,
        document_language=None,
        as_image_document=False,
        file_extension="pdf",
    ):
        if as_image_document:
            file_upload = SimpleUploadedFile("document.jpg", self.PNG_BYTES, content_type="image/jpeg")
            image_upload = SimpleUploadedFile("document_image.png", self.PNG_BYTES, content_type="image/png")
            media = Media.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Media.FILE,
                file=file_upload,
                image=image_upload,
                is_document_image=True,
                document_type=local_document_type,
                document_language=document_language,
            )
        else:
            content = self.PDF_BYTES if file_extension == "pdf" else self.DOCX_BYTES
            content_type = "application/pdf" if file_extension == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            file_upload = SimpleUploadedFile(f"document.{file_extension}", content, content_type=content_type)
            media = Media.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Media.FILE,
                file=file_upload,
                is_document_image=False,
                document_type=local_document_type,
                document_language=document_language,
            )

        return MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=media,
            sort_order=sort_order,
            sales_channel=sales_channel,
        )

    def _run_create_factory(self):
        with patch(
            "sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client",
            return_value=None,
        ), patch.object(
            AmazonMediaProductThroughBase,
            "_get_images",
            return_value=[],
        ), patch(
            "sales_channels.integrations.amazon.factories.mixins.ListingsApi"
        ) as mock_listings:
            mock_instance = mock_listings.return_value
            mock_instance.put_listings_item.return_value = self._mock_amazon_response()
            mock_instance.patch_listings_item.return_value = self._mock_amazon_response()
            mock_instance.get_listings_item.return_value = SimpleNamespace(attributes={})

            factory = AmazonProductCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                remote_instance=self.remote_product,
                view=self.view,
            )
            factory.run()
            return factory, mock_instance

    def _collect_attribute_patches(self, *, mock_instance):
        attribute_patches = {}
        for call in mock_instance.patch_listings_item.call_args_list:
            body = call.kwargs.get("body", {}) or {}
            for patch_item in body.get("patches", []):
                path = patch_item.get("path", "")
                if not isinstance(path, str) or not path.startswith("/attributes/"):
                    continue
                attribute_code = path.replace("/attributes/", "", 1)
                attribute_patches[attribute_code] = patch_item.get("value")
        return attribute_patches

class AmazonDocumentProductPayloadFactoryTest(AmazonDocumentFactoryTestBase):
    def test_product_payload_includes_compliance_media_for_mapped_document(self):
        self._create_public_definition(
            code="compliance_media",
            usage_definition=json.dumps(
                {
                    "compliance_media": [
                        {
                            "content_type": "%document_type%",
                            "marketplace_id": "%auto:marketplace_id%",
                            "source_location": "%document_url%",
                            "content_language": "%document_language%",
                        }
                    ]
                }
            ),
            raw_schema={"items": {"properties": {"content_type": {"enum": ["application_guide"]}}}},
        )
        local_type = self._create_local_document_type(name="Compliance Doc")
        self._map_document_type(local_document_type=local_type, remote_id="compliance_media__application_guide")
        self._create_document_media_through(local_document_type=local_type, document_language="en")

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)

        self.assertIn("compliance_media", attrs)
        self.assertEqual(attrs["compliance_media"][0]["content_type"], "application_guide")
        self.assertEqual(attrs["compliance_media"][0]["marketplace_id"], self.view.remote_id)
        self.assertEqual(attrs["compliance_media"][0]["content_language"], "en")
        self.assertTrue(attrs["compliance_media"][0]["source_location"].startswith("http"))

    def test_product_payload_includes_safety_data_sheet_for_mapped_document(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {
                    "safety_data_sheet_url": [
                        {
                            "value": "%document_url%",
                            "language_tag": "%document_language%",
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )
        local_type = self._create_local_document_type(name="SDS")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        self._create_document_media_through(local_document_type=local_type, document_language="en")

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)

        self.assertIn("safety_data_sheet_url", attrs)
        self.assertEqual(attrs["safety_data_sheet_url"][0]["language_tag"], "en")
        self.assertEqual(attrs["safety_data_sheet_url"][0]["marketplace_id"], self.view.remote_id)
        self.assertTrue(attrs["safety_data_sheet_url"][0]["value"].startswith("http"))

    def test_product_payload_includes_pf_image_locator_for_mapped_document(self):
        self._create_public_definition(
            code="image_locator_ukpf",
            usage_definition=json.dumps(
                {
                    "image_locator_ukpf": [
                        {
                            "marketplace_id": "%auto:marketplace_id%",
                            "media_location": "%document_url%",
                        }
                    ]
                }
            ),
        )
        local_type = self._create_local_document_type(name="PF Safety Image")
        self._map_document_type(local_document_type=local_type, remote_id="image_locator_pf")
        self._create_document_media_through(local_document_type=local_type, as_image_document=True)

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)

        self.assertIn("image_locator_ukpf", attrs)
        self.assertEqual(attrs["image_locator_ukpf"][0]["marketplace_id"], self.view.remote_id)
        self.assertTrue(attrs["image_locator_ukpf"][0]["media_location"].startswith("http"))

    def test_product_payload_includes_ps01_for_first_ps_document(self):
        self._create_public_definition(
            code="image_locator_ps01",
            usage_definition=json.dumps(
                {
                    "image_locator_ps01": [
                        {
                            "marketplace_id": "%auto:marketplace_id%",
                            "media_location": "%document_url%",
                        }
                    ]
                }
            ),
        )
        local_type = self._create_local_document_type(name="PS Safety Image")
        self._map_document_type(local_document_type=local_type, remote_id="image_locator_ps")
        self._create_document_media_through(local_document_type=local_type, sort_order=0, as_image_document=True)

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertIn("image_locator_ps01", attrs)

    def test_product_payload_assigns_ps_slots_in_sort_order_then_id_sequence(self):
        for index in range(1, 4):
            self._create_public_definition(
                code=f"image_locator_ps0{index}",
                usage_definition=json.dumps(
                    {
                        f"image_locator_ps0{index}": [
                            {
                                "marketplace_id": "%auto:marketplace_id%",
                                "media_location": "%document_url%",
                            }
                        ]
                    }
                ),
            )

        # Add another mapped document type that is not PS to ensure slot resolution
        # only considers document types mapped to `image_locator_ps`.
        compliance_type = self._create_local_document_type(name="Compliance Doc")
        self._map_document_type(
            local_document_type=compliance_type,
            remote_id="compliance_media__application_guide",
        )
        self._create_document_media_through(local_document_type=compliance_type, sort_order=0)

        local_type = self._create_local_document_type(name="PS Set")
        self._map_document_type(local_document_type=local_type, remote_id="image_locator_ps")
        self._create_document_media_through(local_document_type=local_type, sort_order=0, as_image_document=True)
        self._create_document_media_through(local_document_type=local_type, sort_order=0, as_image_document=True)
        self._create_document_media_through(local_document_type=local_type, sort_order=0, as_image_document=True)

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)

        self.assertIn("image_locator_ps01", attrs)
        self.assertIn("image_locator_ps02", attrs)
        self.assertIn("image_locator_ps03", attrs)
        self.assertNotIn("image_locator_ps04", attrs)

    def test_product_payload_skips_unmapped_document_types(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {"safety_data_sheet_url": [{"value": "%document_url%", "language_tag": "%document_language%", "marketplace_id": "%auto:marketplace_id%"}]}
            ),
        )
        mapped_type = self._create_local_document_type(name="Mapped")
        unmapped_type = self._create_local_document_type(name="Unmapped")
        self._map_document_type(local_document_type=mapped_type, remote_id="safety_data_sheet_url")
        mapped_through = self._create_document_media_through(local_document_type=mapped_type)
        unmapped_through = self._create_document_media_through(local_document_type=unmapped_type)

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)

        self.assertIn("safety_data_sheet_url", attrs)
        self.assertTrue(
            AmazonDocumentThroughProduct.objects.filter(
                local_instance=mapped_through,
                remote_product=self.remote_product,
                sales_channel=self.sales_channel,
            ).exists()
        )
        self.assertFalse(
            AmazonDocumentThroughProduct.objects.filter(
                local_instance=unmapped_through,
                remote_product=self.remote_product,
                sales_channel=self.sales_channel,
            ).exists()
        )

    def test_product_payload_skips_when_public_definition_missing_for_product_type(self):
        local_type = self._create_local_document_type(name="No Definition")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        through = self._create_document_media_through(local_document_type=local_type)

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertNotIn("safety_data_sheet_url", attrs)
        self.assertFalse(
            AmazonDocumentThroughProduct.objects.filter(
                local_instance=through,
                remote_product=self.remote_product,
                sales_channel=self.sales_channel,
            ).exists()
        )

    def test_product_payload_skips_when_usage_definition_is_empty(self):
        self._create_public_definition(code="safety_data_sheet_url", usage_definition="")
        local_type = self._create_local_document_type(name="Empty Usage")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        through = self._create_document_media_through(local_document_type=local_type)

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertNotIn("safety_data_sheet_url", attrs)
        self.assertFalse(
            AmazonDocumentThroughProduct.objects.filter(
                local_instance=through,
                remote_product=self.remote_product,
                sales_channel=self.sales_channel,
            ).exists()
        )

    def test_product_payload_excludes_internal_documents(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {"safety_data_sheet_url": [{"value": "%document_url%", "language_tag": "%document_language%", "marketplace_id": "%auto:marketplace_id%"}]}
            ),
        )
        mapped_type = self._create_local_document_type(name="Mapped Public")
        self._map_document_type(local_document_type=mapped_type, remote_id="safety_data_sheet_url")
        self._create_document_media_through(local_document_type=mapped_type)

        internal_type = DocumentType.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            code=DocumentType.INTERNAL_CODE,
        )
        self._create_document_media_through(local_document_type=internal_type)

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertIn("safety_data_sheet_url", attrs)
        self.assertEqual(
            AmazonDocumentThroughProduct.objects.filter(
                remote_product=self.remote_product,
                sales_channel=self.sales_channel,
            ).count(),
            1,
        )

    def test_product_payload_skips_document_when_not_owner_and_property_not_allowed(self):
        self._create_public_definition(
            code="compliance_media",
            usage_definition=json.dumps(
                {
                    "compliance_media": [
                        {
                            "content_type": "%document_type%",
                            "marketplace_id": "%auto:marketplace_id%",
                            "source_location": "%document_url%",
                            "content_language": "%document_language%",
                        }
                    ]
                }
            ),
            raw_schema={"items": {"properties": {"content_type": {"enum": ["application_guide"]}}}},
        )
        local_type = self._create_local_document_type(name="Compliance")
        self._map_document_type(local_document_type=local_type, remote_id="compliance_media__application_guide")
        self._create_document_media_through(local_document_type=local_type)

        self.remote_product.product_owner = False
        self.remote_product.save(update_fields=["product_owner"])
        remote_rule = self.remote_product.get_remote_rule()
        remote_rule.listing_offer_required_properties = {self.view.api_region_code: []}
        remote_rule.save(update_fields=["listing_offer_required_properties"])

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertNotIn("compliance_media", attrs)

    def test_product_payload_includes_document_when_not_owner_and_property_allowed(self):
        self._create_public_definition(
            code="compliance_media",
            usage_definition=json.dumps(
                {
                    "compliance_media": [
                        {
                            "content_type": "%document_type%",
                            "marketplace_id": "%auto:marketplace_id%",
                            "source_location": "%document_url%",
                            "content_language": "%document_language%",
                        }
                    ]
                }
            ),
            raw_schema={"items": {"properties": {"content_type": {"enum": ["application_guide"]}}}},
        )
        local_type = self._create_local_document_type(name="Compliance")
        self._map_document_type(local_document_type=local_type, remote_id="compliance_media__application_guide")
        self._create_document_media_through(local_document_type=local_type)

        self.remote_product.product_owner = False
        self.remote_product.save(update_fields=["product_owner"])
        remote_rule = self.remote_product.get_remote_rule()
        remote_rule.listing_offer_required_properties = {self.view.api_region_code: ["compliance_media"]}
        remote_rule.save(update_fields=["listing_offer_required_properties"])

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertIn("compliance_media", attrs)

    def test_product_payload_raises_for_pf_when_media_not_document_image(self):
        self._create_public_definition(
            code="image_locator_ukpf",
            usage_definition=json.dumps({"image_locator_ukpf": [{"marketplace_id": "%auto:marketplace_id%", "media_location": "%document_url%"}]}),
        )
        local_type = self._create_local_document_type(name="PF")
        self._map_document_type(local_document_type=local_type, remote_id="image_locator_pf")
        self._create_document_media_through(local_document_type=local_type, as_image_document=False)

        with self.assertRaises(PreFlightCheckError):
            self._run_create_factory()
    def test_product_payload_raises_for_ps_when_media_not_document_image(self):
        self._create_public_definition(
            code="image_locator_ps01",
            usage_definition=json.dumps({"image_locator_ps01": [{"marketplace_id": "%auto:marketplace_id%", "media_location": "%document_url%"}]}),
        )
        local_type = self._create_local_document_type(name="PS")
        self._map_document_type(local_document_type=local_type, remote_id="image_locator_ps")
        self._create_document_media_through(local_document_type=local_type, as_image_document=False)

        with self.assertRaises(PreFlightCheckError):
            self._run_create_factory()

    def test_product_payload_raises_for_non_pdf_non_image_document(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {"safety_data_sheet_url": [{"value": "%document_url%", "language_tag": "%document_language%", "marketplace_id": "%auto:marketplace_id%"}]}
            ),
        )
        local_type = self._create_local_document_type(name="SDS")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        self._create_document_media_through(local_document_type=local_type, as_image_document=False, file_extension="docx")

        with self.assertRaises(PreFlightCheckError):
            self._run_create_factory()

    def test_product_payload_accepts_image_document_for_compliance_media(self):
        self._create_public_definition(
            code="compliance_media",
            usage_definition=json.dumps(
                {
                    "compliance_media": [
                        {
                            "content_type": "%document_type%",
                            "marketplace_id": "%auto:marketplace_id%",
                            "source_location": "%document_url%",
                            "content_language": "%document_language%",
                        }
                    ]
                }
            ),
            raw_schema={"items": {"properties": {"content_type": {"enum": ["application_guide"]}}}},
        )
        local_type = self._create_local_document_type(name="Compliance Image")
        self._map_document_type(local_document_type=local_type, remote_id="compliance_media__application_guide")
        self._create_document_media_through(local_document_type=local_type, as_image_document=True)

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertIn("compliance_media", attrs)

    def test_product_payload_uses_exact_document_language_mapping(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {"safety_data_sheet_url": [{"value": "%document_url%", "language_tag": "%document_language%", "marketplace_id": "%auto:marketplace_id%"}]}
            ),
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance="fr",
            remote_code="fr_FR",
        )
        local_type = self._create_local_document_type(name="French SDS")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        self._create_document_media_through(local_document_type=local_type, document_language="fr")

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertEqual(attrs["safety_data_sheet_url"][0]["language_tag"], "fr_FR")

    def test_product_payload_uses_root_language_mapping_fallback(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {"safety_data_sheet_url": [{"value": "%document_url%", "language_tag": "%document_language%", "marketplace_id": "%auto:marketplace_id%"}]}
            ),
        )
        local_type = self._create_local_document_type(name="Root Language SDS")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        self._create_document_media_through(local_document_type=local_type, document_language="en-GB")

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertEqual(attrs["safety_data_sheet_url"][0]["language_tag"], "en")

    def test_product_payload_falls_back_to_view_language_when_no_language_mapping_exists(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {"safety_data_sheet_url": [{"value": "%document_url%", "language_tag": "%document_language%", "marketplace_id": "%auto:marketplace_id%"}]}
            ),
        )
        AmazonRemoteLanguage.objects.filter(sales_channel_view=self.view).delete()
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance="de",
            remote_code="de_DE",
        )
        local_type = self._create_local_document_type(name="Fallback Language SDS")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        self._create_document_media_through(local_document_type=local_type, document_language="it")

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)
        self.assertEqual(attrs["safety_data_sheet_url"][0]["language_tag"], "de_DE")

    def test_product_payload_raises_for_unsupported_remote_document_type(self):
        local_type = self._create_local_document_type(name="Unsupported")
        self._map_document_type(local_document_type=local_type, remote_id="unknown_type")
        self._create_document_media_through(local_document_type=local_type)

        with self.assertRaises(PreFlightCheckError):
            self._run_create_factory()

    def test_product_payload_raises_when_compliance_type_not_allowed_by_definition(self):
        self._create_public_definition(
            code="compliance_media",
            usage_definition=json.dumps(
                {
                    "compliance_media": [
                        {
                            "content_type": "%document_type%",
                            "marketplace_id": "%auto:marketplace_id%",
                            "source_location": "%document_url%",
                            "content_language": "%document_language%",
                        }
                    ]
                }
            ),
            raw_schema={"items": {"properties": {"content_type": {"enum": ["application_guide"]}}}},
        )
        local_type = self._create_local_document_type(name="Disallowed Compliance")
        self._map_document_type(local_document_type=local_type, remote_id="compliance_media__warranty")
        self._create_document_media_through(local_document_type=local_type)

        with self.assertRaises(PreFlightCheckError):
            self._run_create_factory()

    def test_product_payload_creates_assignment_with_require_document_false(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {"safety_data_sheet_url": [{"value": "%document_url%", "language_tag": "%document_language%", "marketplace_id": "%auto:marketplace_id%"}]}
            ),
        )
        local_type = self._create_local_document_type(name="SDS")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        through = self._create_document_media_through(local_document_type=local_type)

        self._run_create_factory()

        association = AmazonDocumentThroughProduct.objects.get(
            local_instance=through,
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
        )
        self.assertFalse(association.require_document)
        self.assertIsNone(association.remote_document)
        self.assertEqual(association.remote_id, "safety_data_sheet_url")

    def test_product_payload_updates_existing_assignment_remote_id_to_resolved_property(self):
        self._create_public_definition(
            code="image_locator_ukpf",
            usage_definition=json.dumps(
                {"image_locator_ukpf": [{"marketplace_id": "%auto:marketplace_id%", "media_location": "%document_url%"}]}
            ),
        )
        local_type = self._create_local_document_type(name="PF")
        self._map_document_type(local_document_type=local_type, remote_id="image_locator_pf")
        through = self._create_document_media_through(local_document_type=local_type, as_image_document=True)

        association = AmazonDocumentThroughProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=through,
            remote_product=self.remote_product,
            require_document=False,
            remote_document=None,
            remote_id="legacy_code",
        )
        self._run_create_factory()
        association.refresh_from_db()
        self.assertEqual(association.remote_id, "image_locator_ukpf")

    def test_product_payload_prefers_existing_remote_url_then_falls_back_to_local_document_url(self):
        self._create_public_definition(
            code="safety_data_sheet_url",
            usage_definition=json.dumps(
                {
                    "safety_data_sheet_url": [
                        {
                            "value": "%document_url%",
                            "language_tag": "%document_language%",
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )
        self._create_public_definition(
            code="compliance_media",
            usage_definition=json.dumps(
                {
                    "compliance_media": [
                        {
                            "content_type": "%document_type%",
                            "marketplace_id": "%auto:marketplace_id%",
                            "source_location": "%document_url%",
                            "content_language": "%document_language%",
                        }
                    ]
                }
            ),
            raw_schema={"items": {"properties": {"content_type": {"enum": ["application_guide"]}}}},
        )

        sds_type = self._create_local_document_type(name="SDS")
        compliance_type = self._create_local_document_type(name="Compliance")
        self._map_document_type(local_document_type=sds_type, remote_id="safety_data_sheet_url")
        self._map_document_type(local_document_type=compliance_type, remote_id="compliance_media__application_guide")

        sds_through = self._create_document_media_through(local_document_type=sds_type)
        compliance_through = self._create_document_media_through(local_document_type=compliance_type)

        cached_remote_url = "https://cdn.example.com/sds-cached.pdf"
        AmazonDocumentThroughProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=sds_through,
            remote_product=self.remote_product,
            require_document=False,
            remote_document=None,
            remote_id="safety_data_sheet_url",
            remote_url=cached_remote_url,
        )
        AmazonDocumentThroughProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=compliance_through,
            remote_product=self.remote_product,
            require_document=False,
            remote_document=None,
            remote_id="compliance_media",
            remote_url=None,
        )

        _, mock_instance = self._run_create_factory()
        attrs = self._collect_attribute_patches(mock_instance=mock_instance)

        self.assertEqual(attrs["safety_data_sheet_url"][0]["value"], cached_remote_url)
        compliance_source_url = attrs["compliance_media"][0]["source_location"]
        self.assertTrue(compliance_source_url.startswith("http"))
        self.assertNotEqual(compliance_source_url, cached_remote_url)

    def test_delete_assignment_sends_none_patch_for_resolved_property(self):
        local_type = self._create_local_document_type(name="Delete SDS")
        self._map_document_type(local_document_type=local_type, remote_id="safety_data_sheet_url")
        through = self._create_document_media_through(local_document_type=local_type)
        association = AmazonDocumentThroughProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=through,
            remote_product=self.remote_product,
            require_document=False,
            remote_document=None,
            remote_id="safety_data_sheet_url",
        )

        factory = AmazonDocumentThroughProductDeleteFactory(
            sales_channel=self.sales_channel,
            local_instance=through,
            remote_product=self.remote_product,
            remote_instance=association,
            view=self.view,
            remote_rule=self.remote_product.get_remote_rule(),
            get_value_only=True,
        )
        payload = factory.delete_remote()
        self.assertEqual(payload, {"safety_data_sheet_url": None})
