from media.models import Media, Image, MediaProductThrough, DocumentType
from products.models import Product, ConfigurableVariation
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.models import (
    RemoteDocument,
    RemoteDocumentProductAssociation,
    RemoteProduct,
    SalesChannel,
)
from core.models import MultiTenantCompany
from core.tests import TestCase
from model_bakery import baker
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.conf import settings
from pathlib import Path
from unittest.mock import patch

from .helpers import CreateImageMixin

import os
import base64
import logging

logger = logging.getLogger(__name__)


class MediaTestCase(CreateImageMixin, TestCase):

    def _get_tenant_upload_path_parts(self):
        """How many parts does this upload path create?"""
        multi_tenant_company_id = 1
        real_folder = 1
        complex_folder = settings.UPLOAD_TENANT_PATH_DEPTH
        filename = 1
        return sum([multi_tenant_company_id, real_folder, complex_folder, filename])

    def test_image_web_url_none(self):
        image = baker.make(Media, image=None, multi_tenant_company=self.multi_tenant_company, type=Media.IMAGE)
        url = image.image_web_url
        self.assertTrue(url is None)

    def test_image_web_url(self):
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        url = image.image_web_url
        self.assertTrue(url.endswith('.jpg'))
        self.assertTrue(url.startswith('http'))

    def test_onesila_thumbnail_url(self):
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        url = image.onesila_thumbnail_url()
        # Cached images are converted to jpg, no matter what the source.
        self.assertTrue(url.endswith('.jpg'))
        self.assertTrue(url.startswith('http'))

    def test_create_duplicate_media_file_returns_initial_id(self):
        image_file = self.get_image_file('red.png')
        image_file_duplicate = self.get_image_file('red.png')

        media1 = Media.objects.create(type=Media.IMAGE, image=image_file, multi_tenant_company=self.multi_tenant_company)
        media2 = Media.objects.create(type=Media.IMAGE, image=image_file_duplicate, multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(media1.id, media2.id)

        image1 = Image.objects.create(image=image_file, multi_tenant_company=self.multi_tenant_company)
        image2 = Image.objects.create(image=image_file_duplicate, multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(image1.id, image2.id)

    def test_image_get_or_create_handles_duplicate_insert(self):
        image_file = self.get_image_file('red.png')
        existing = Image.objects.create(
            image=image_file,
            multi_tenant_company=self.multi_tenant_company,
        )

        duplicate_file = self.get_image_file('red.png')
        with patch(
            "media.managers.ImageManager.get",
            side_effect=[Image.DoesNotExist, existing],
        ):
            instance, created = Image.objects.get_or_create(
                image=duplicate_file,
                multi_tenant_company=self.multi_tenant_company,
            )

        self.assertEqual(instance.id, existing.id)
        self.assertFalse(created)

    def test_image_upload_path(self):
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        parts = image.image.name.split('/')
        expected_parts = self._get_tenant_upload_path_parts()
        self.assertEqual(parts[0], str(self.multi_tenant_company.id))
        self.assertEqual(parts[1], 'images')
        self.assertEqual(len(parts), expected_parts)

    def test_file_upload_path(self):
        media = Media.objects.create(multi_tenant_company=self.multi_tenant_company, type=Media.FILE)
        media.file.save('test.pdf', ContentFile(b'test'))
        parts = media.file.name.split('/')
        expected_parts = self._get_tenant_upload_path_parts()
        self.assertEqual(parts[0], str(self.multi_tenant_company.id))
        self.assertEqual(parts[1], 'files')
        logger.debug(f"Parts look like this: {parts}")
        self.assertEqual(len(parts), expected_parts)

    def test_shared_file_not_deleted(self):
        """Test that a shared file is not deleted when one media instance is deleted."""
        # Create a shared image file
        shared_image_file = self.get_image_file('red.png')

        # Create two media instances sharing the same file
        media1 = Media.objects.create(type=Media.FILE, file=shared_image_file, multi_tenant_company=self.multi_tenant_company)
        media2 = Media.objects.create(type=Media.FILE, file=shared_image_file, multi_tenant_company=self.multi_tenant_company)

        media1.refresh_from_db()
        media2.refresh_from_db()

        # Ensure ids are different:
        self.assertNotEqual(media1.id, media2.id)

        # Verify that we can find the media instances in the database
        media1_absolute_path = media1.file.path
        media2_absolute_path = media2.file.path
        rel_path_media1 = str(Path(media1_absolute_path).relative_to(settings.MEDIA_ROOT))
        rel_path_media2 = str(Path(media2_absolute_path).relative_to(settings.MEDIA_ROOT))

        # These rel paths should not be the same.
        # So the there should never be share files.
        self.assertNotEqual(rel_path_media1, rel_path_media2)

        # Tests continuation below are a non-issue.
        # media1_qs = Media.objects.filter(file__endswith=rel_path_media1)
        # media2_qs = Media.objects.filter(file__endswith=rel_path_media1)

        # self.assertEqual(media1_qs.count(), 2)
        # self.assertEqual(media2_qs.count(), 2)

        # # Ensure the the files are truly shared
        # shared_image_path1 = media1.file.path
        # logger.debug(f"About to investigate shared_image_path1 {shared_image_path1}")
        # shared_image_path2 = media2.file.path
        # logger.debug(f"About to investigate shared_image_path2 {shared_image_path2}")
        # self.assertEqual(shared_image_path1, shared_image_path2)

        # # And that they exist
        # self.assertTrue(os.path.exists(shared_image_path1))
        # self.assertTrue(os.path.exists(shared_image_path2))

        # # Delete one media instance
        # media1.delete()

        # # Verify that the shared image file is still present
        # self.assertTrue(os.path.exists(shared_image_path2))

        # # Clean up by deleting the second media instance
        # media2.delete()


class DocumentTypeTestCase(TestCase):
    def test_code_is_generated_from_name(self):
        document_type = DocumentType.objects.create(
            name="Kid certificate",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertEqual(document_type.code, "KID_CERTIFICATE")

    def test_code_generation_is_unique_per_company(self):
        DocumentType.objects.create(
            name="Kid certificate",
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = DocumentType.objects.create(
            name="Kid certificate",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertEqual(document_type.code, "KID_CERTIFICATE_1")

    def test_internal_document_type_is_created_for_new_companies(self):
        self.assertTrue(
            DocumentType.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                code=DocumentType.INTERNAL_CODE,
            ).exists()
        )

        another_company = baker.make(MultiTenantCompany)
        internal_document_type = DocumentType.objects.get(
            multi_tenant_company=another_company,
            code=DocumentType.INTERNAL_CODE,
        )

        self.assertEqual(internal_document_type.name, DocumentType.INTERNAL_NAME)
        self.assertEqual(internal_document_type.description, DocumentType.INTERNAL_DESCRIPTION)

    def test_internal_document_type_cannot_be_deleted(self):
        internal_document_type = DocumentType.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            code=DocumentType.INTERNAL_CODE,
        )

        with self.assertRaises(ValidationError):
            internal_document_type.delete()

    def test_internal_document_type_cannot_be_bulk_deleted(self):
        with self.assertRaises(ValidationError):
            DocumentType.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                code=DocumentType.INTERNAL_CODE,
            ).delete()


class MediaDocumentTypeTestCase(TestCase):
    def test_file_requires_document_type_on_clean(self):
        media = Media(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )

        with self.assertRaises(ValidationError):
            media.full_clean()

    def test_file_media_defaults_to_internal_document_type_on_save(self):
        media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertIsNotNone(media.document_type_id)
        self.assertEqual(media.document_type.code, DocumentType.INTERNAL_CODE)

    def test_file_document_type_constraint_is_enforced_in_database(self):
        media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Media.objects.filter(id=media.id).update(document_type=None)

    def test_document_language_defaults_to_company_language(self):
        self.multi_tenant_company.language = "de"
        self.multi_tenant_company.save(update_fields=["language"])

        media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertEqual(media.document_language, "de")

    def test_document_language_keeps_explicit_value(self):
        explicit_language = next(
            (
                code
                for code, _ in settings.LANGUAGES
                if code != self.multi_tenant_company.language
            ),
            self.multi_tenant_company.language,
        )
        internal_document_type = DocumentType.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            code=DocumentType.INTERNAL_CODE,
        )

        media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
            document_type=internal_document_type,
            document_language=explicit_language,
        )

        self.assertEqual(media.document_language, explicit_language)

    def test_file_image_mime_sets_document_image_and_populates_image(self):
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
        )

        media = Media.objects.create(
            type=Media.FILE,
            file=ContentFile(png_bytes, name="document_image.png"),
            multi_tenant_company=self.multi_tenant_company,
        )
        media.refresh_from_db()

        self.assertTrue(media.is_document_image)
        self.assertIsNotNone(media.image)

    def test_document_type_can_be_changed_when_no_remote_document_usage_exists(self):
        media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )
        new_document_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Public Safety Document",
        )

        media.document_type = new_document_type
        media.save()
        media.refresh_from_db()

        self.assertEqual(media.document_type_id, new_document_type.id)

    def test_document_type_change_is_blocked_when_remote_document_exists(self):
        sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://doc-guard-remote.test",
        )
        media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )
        new_document_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Public Compliance Document",
        )
        RemoteDocument.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=media,
        )

        media.document_type = new_document_type
        with self.assertRaises(ValidationError):
            media.save()

    def test_document_type_change_is_blocked_when_remote_document_association_exists(self):
        sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://doc-guard-association.test",
        )
        product = baker.make(
            Product,
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )
        new_document_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Public User Guide Document",
        )

        media_through = MediaProductThrough.objects.create(
            product=product,
            media=media,
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=product,
        )
        remote_document = RemoteDocument.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=None,
        )
        RemoteDocumentProductAssociation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=media_through,
            remote_product=remote_product,
            remote_document=remote_document,
        )

        media.document_type = new_document_type
        with self.assertRaises(ValidationError):
            media.save()


class MediaProductThroughManagerTestCase(TestCase):
    def test_get_product_images_excludes_color_type(self):
        product = baker.make(Product, type="SIMPLE", multi_tenant_company=self.multi_tenant_company)
        image_media = baker.make(
            Media,
            type=Media.IMAGE,
            image_type=Media.PACK_SHOT,
            multi_tenant_company=self.multi_tenant_company,
        )
        color_media = baker.make(
            Media,
            type=Media.IMAGE,
            image_type=Media.COLOR_SHOT,
            multi_tenant_company=self.multi_tenant_company,
        )
        image_through = MediaProductThrough.objects.create(
            product=product,
            media=image_media,
            multi_tenant_company=self.multi_tenant_company,
        )
        MediaProductThrough.objects.create(
            product=product,
            media=color_media,
            multi_tenant_company=self.multi_tenant_company,
        )

        images_queryset = MediaProductThrough.objects.get_product_images(
            product=product,
            sales_channel=None,
        )

        self.assertTrue(images_queryset.filter(pk=image_through.pk).exists())
        self.assertFalse(images_queryset.filter(media=color_media).exists())

    def test_get_product_color_image_fallback(self):
        product = baker.make(Product,type="SIMPLE", multi_tenant_company=self.multi_tenant_company)
        default_media_one = baker.make(
            Media,
            type=Media.IMAGE,
            image_type=Media.COLOR_SHOT,
            multi_tenant_company=self.multi_tenant_company,
        )
        default_media_two = baker.make(
            Media,
            type=Media.IMAGE,
            image_type=Media.COLOR_SHOT,
            multi_tenant_company=self.multi_tenant_company,
        )
        channel_media = baker.make(
            Media,
            type=Media.IMAGE,
            image_type=Media.COLOR_SHOT,
            multi_tenant_company=self.multi_tenant_company,
        )

        default_through_one = MediaProductThrough.objects.create(
            product=product,
            media=default_media_one,
            sort_order=1,
            multi_tenant_company=self.multi_tenant_company,
        )
        MediaProductThrough.objects.create(
            product=product,
            media=default_media_two,
            sort_order=2,
            multi_tenant_company=self.multi_tenant_company,
        )

        sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://channel.test",
        )
        channel_through = MediaProductThrough.objects.create(
            product=product,
            media=channel_media,
            sort_order=1,
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        other_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://other.test",
        )

        self.assertEqual(
            MediaProductThrough.objects.get_product_color_image(
                product=product,
                sales_channel=sales_channel,
            ),
            channel_through,
        )
        self.assertEqual(
            MediaProductThrough.objects.get_product_color_image(
                product=product,
                sales_channel=other_channel,
            ),
            default_through_one,
        )
        self.assertEqual(
            MediaProductThrough.objects.get_product_color_image(
                product=product,
                sales_channel=None,
            ),
            default_through_one,
        )

    def test_get_public_product_documents_excludes_internal_document_type(self):
        product = baker.make(Product, type="SIMPLE", multi_tenant_company=self.multi_tenant_company)
        sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://documents.test",
        )

        internal_document_type = DocumentType.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            code=DocumentType.INTERNAL_CODE,
        )
        public_document_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Safety Certificate",
        )

        internal_media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
            document_type=internal_document_type,
        )
        public_media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
            document_type=public_document_type,
        )

        MediaProductThrough.objects.create(
            product=product,
            media=internal_media,
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        public_assignment = MediaProductThrough.objects.create(
            product=product,
            media=public_media,
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

        queryset = MediaProductThrough.objects.get_public_product_documents(
            product=product,
            sales_channel=sales_channel,
        )

        self.assertEqual(list(queryset.values_list("id", flat=True)), [public_assignment.id])


class MediaProductThroughDocumentPropagationTestCase(TestCase):
    def _create_configurable_product_with_children(self):
        parent = baker.make(
            Product,
            type=Product.CONFIGURABLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        variation_one = baker.make(
            Product,
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        variation_two = baker.make(
            Product,
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )

        ConfigurableVariation.objects.create(
            parent=parent,
            variation=variation_one,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent,
            variation=variation_two,
            multi_tenant_company=self.multi_tenant_company,
        )

        return parent, variation_one, variation_two

    def test_file_assignment_on_configurable_is_propagated_to_children_for_same_sales_channel(self):
        parent, variation_one, variation_two = self._create_configurable_product_with_children()
        sales_channel_a = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://docs-a.test",
        )
        sales_channel_b = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://docs-b.test",
        )
        file_media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )

        MediaProductThrough.objects.create(
            product=variation_one,
            media=file_media,
            sales_channel=sales_channel_b,
            multi_tenant_company=self.multi_tenant_company,
        )

        MediaProductThrough.objects.create(
            product=parent,
            media=file_media,
            sales_channel=sales_channel_a,
            multi_tenant_company=self.multi_tenant_company,
        )

        propagated_ids = set(
            MediaProductThrough.objects.filter(
                product_id__in=[variation_one.id, variation_two.id],
                media=file_media,
                sales_channel=sales_channel_a,
            ).values_list("product_id", flat=True)
        )
        self.assertSetEqual(propagated_ids, {variation_one.id, variation_two.id})

        self.assertEqual(
            MediaProductThrough.objects.filter(
                product=variation_one,
                media=file_media,
                sales_channel=sales_channel_b,
            ).count(),
            1,
        )

    def test_file_assignment_delete_on_configurable_removes_children_only_for_same_sales_channel(self):
        parent, variation_one, variation_two = self._create_configurable_product_with_children()
        sales_channel_a = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://docs-delete-a.test",
        )
        sales_channel_b = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://docs-delete-b.test",
        )
        file_media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )

        parent_assignment = MediaProductThrough.objects.create(
            product=parent,
            media=file_media,
            sales_channel=sales_channel_a,
            multi_tenant_company=self.multi_tenant_company,
        )

        MediaProductThrough.objects.create(
            product=variation_one,
            media=file_media,
            sales_channel=sales_channel_b,
            multi_tenant_company=self.multi_tenant_company,
        )
        MediaProductThrough.objects.create(
            product=variation_two,
            media=file_media,
            sales_channel=sales_channel_b,
            multi_tenant_company=self.multi_tenant_company,
        )

        parent_assignment.delete()

        self.assertFalse(
            MediaProductThrough.objects.filter(
                product_id__in=[variation_one.id, variation_two.id],
                media=file_media,
                sales_channel=sales_channel_a,
            ).exists()
        )
        self.assertEqual(
            MediaProductThrough.objects.filter(
                product_id__in=[variation_one.id, variation_two.id],
                media=file_media,
                sales_channel=sales_channel_b,
            ).count(),
            2,
        )


class ImageCleanupTestCase(CreateImageMixin, TestCase):
    def test_image_cleanup(self):
        """This test will create and remove an image. Then verify if both the image file and cached files have been removed from storage."""
        # Create an image
        image = self.create_image(fname='red.png', multi_tenant_company=self.multi_tenant_company)
        image_path = image.image.path
        cached_image_path = image.image_web.path

        # Ensure the image and cached image exist
        self.assertTrue(os.path.exists(image_path))
        self.assertTrue(os.path.exists(cached_image_path))

        # Delete the image
        image.delete()

        # Verify that the image and cached image files are removed
        self.assertFalse(os.path.exists(image_path))
        self.assertFalse(os.path.exists(cached_image_path))
