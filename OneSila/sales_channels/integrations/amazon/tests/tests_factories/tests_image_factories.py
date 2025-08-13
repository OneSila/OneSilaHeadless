import json
import base64
from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from media.models import Media, MediaProductThrough
from imports_exports.models import Import
from imports_exports.factories.products import ImportProductInstance
from sales_channels.integrations.amazon.factories.imports.products_imports import (
    AmazonProductsImportProcessor,
)
from properties.models import PropertySelectValue, PropertySelectValueTranslation, ProductPropertiesRule, Property, \
    ProductProperty
from sales_channels.integrations.amazon.models import AmazonProductType
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
)
from sales_channels.integrations.amazon.models.products import (
    AmazonProduct,
    AmazonImageProductAssociation,
)
from sales_channels.integrations.amazon.factories.products.images import (
    AmazonMediaProductThroughCreateFactory,
    AmazonMediaProductThroughUpdateFactory,
    AmazonMediaProductThroughDeleteFactory,
    AmazonMediaProductThroughBase,
)


class AmazonProductImageFactoryTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            api_region_code="EU_UK",
            remote_id="GB",
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_code="en",
        )

        # Local product
        self.product = baker.make(
            "products.Product",
            sku="TESTSKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )

        # Remote product
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="AMZSKU",
        )
        self.product_type_property = Property.objects.filter(is_product_type=True, multi_tenant_company=self.multi_tenant_company).first()

        self.product_type_value = baker.make(
            PropertySelectValue,
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            language=self.multi_tenant_company.language,
            value="Chair",
        )
        self.rule = ProductPropertiesRule.objects.filter(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        ).first()
        ProductProperty.objects.create(
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="CHAIR",
        )

        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

        # Create two image throughs
        self.throughs = []
        for idx in range(2):
            media = Media.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Media.IMAGE,
                owner=self.user,
            )
            through = MediaProductThrough.objects.create(
                product=self.product,
                media=media,
                sort_order=idx,
                multi_tenant_company=self.multi_tenant_company,
            )
            self.throughs.append(through)

    def test_image_create_factory_value_only(self):
        urls = ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
        expected_attrs = {}
        for idx, key in enumerate(AmazonMediaProductThroughBase.OFFER_KEYS):
            expected_attrs[key] = (
                [{"media_location": urls[idx]}] if idx < len(urls) else None
            )
        for idx, key in enumerate(AmazonMediaProductThroughBase.PRODUCT_KEYS):
            expected_attrs[key] = (
                [{"media_location": urls[idx]}] if idx < len(urls) else None
            )

        with patch.object(
            AmazonMediaProductThroughBase, "_get_images", return_value=urls
        ):
            fac = AmazonMediaProductThroughCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.throughs[0],
                remote_product=self.remote_product,
                view=self.view,
                get_value_only=True,
            )
            body = fac.build_body()
            self.assertEqual(body["attributes"], expected_attrs)
            fac.run()

            # run for the second image as well
            fac = AmazonMediaProductThroughCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.throughs[1],
                remote_product=self.remote_product,
                view=self.view,
                get_value_only=True,
            )
            fac.run()

        cnt = AmazonImageProductAssociation.objects.filter(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
        ).count()
        self.assertEqual(cnt, 2)

    def test_image_update_factory_value_only(self):
        remote_instance = AmazonImageProductAssociation.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.throughs[0],
            remote_product=self.remote_product,
        )

        urls = ["https://example.com/updated1.jpg", "https://example.com/updated2.jpg"]
        expected_attrs = {}
        for idx, key in enumerate(AmazonMediaProductThroughBase.OFFER_KEYS):
            expected_attrs[key] = (
                [{"media_location": urls[idx]}] if idx < len(urls) else None
            )
        for idx, key in enumerate(AmazonMediaProductThroughBase.PRODUCT_KEYS):
            expected_attrs[key] = (
                [{"media_location": urls[idx]}] if idx < len(urls) else None
            )

        with patch.object(
            AmazonMediaProductThroughBase, "_get_images", return_value=urls
        ):
            fac = AmazonMediaProductThroughUpdateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.throughs[0],
                remote_product=self.remote_product,
                remote_instance=remote_instance,
                view=self.view,
                get_value_only=True,
            )
            body = fac.build_body()
            self.assertEqual(body["attributes"], expected_attrs)
            fac.run()

        cnt = AmazonImageProductAssociation.objects.filter(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
        ).count()
        self.assertEqual(cnt, 1)

    def test_delete_factory_value_only(self):
        remote_instance = AmazonImageProductAssociation.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.throughs[0],
            remote_product=self.remote_product,
        )

        keys = (
            list(AmazonMediaProductThroughBase.OFFER_KEYS)
            + list(AmazonMediaProductThroughBase.PRODUCT_KEYS)
        )
        expected_attrs = {key: None for key in keys}

        with patch.object(
            AmazonMediaProductThroughBase, "_get_images", return_value=[]
        ):
            fac = AmazonMediaProductThroughDeleteFactory(
                sales_channel=self.sales_channel,
                local_instance=self.throughs[0],
                remote_product=self.remote_product,
                remote_instance=remote_instance,
                view=self.view,
                get_value_only=True,
            )
            body = fac.build_body()
            self.assertEqual(body["attributes"], expected_attrs)
            fac.run()

        exists = AmazonImageProductAssociation.objects.filter(id=remote_instance.id).exists()
        self.assertFalse(exists)

    def test_get_images_prefers_imported_url(self):
        urls = ["https://amazon.com/img1.jpg", "https://amazon.com/img2.jpg"]
        for idx, through in enumerate(self.throughs):
            AmazonImageProductAssociation.objects.create(
                sales_channel=self.sales_channel,
                local_instance=through,
                remote_product=self.remote_product,
                imported_url=urls[idx],
            )

        fac = AmazonMediaProductThroughCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.throughs[0],
            remote_product=self.remote_product,
            view=self.view,
        )

        self.assertEqual(fac._get_images(), urls)

    def test_handle_images_sets_imported_url(self):
        img_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAOaoSn0AAAAASUVORK5CYII="
        )

        import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        data = {
            "name": "Prod",
            "sku": "TESTSKU2",
            "type": "SIMPLE",
            "images": [
                {
                    "image_url": "https://amazon.com/original.jpg",
                    "image_content": img_b64,
                    "sort_order": 0,
                    "is_main_image": True,
                }
            ],
        }

        import_instance = ImportProductInstance(data, import_process=import_process)
        import_instance.instance = self.product
        import_instance.set_images()
        import_instance.remote_instance = self.remote_product

        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None):
            processor = AmazonProductsImportProcessor(import_process, self.sales_channel)

        processor.handle_images(import_instance)

        assoc = AmazonImageProductAssociation.objects.get(
            local_instance=import_instance.images_associations_instances[0],
            remote_product=self.remote_product,
        )

        self.assertEqual(assoc.imported_url, "https://amazon.com/original.jpg")
