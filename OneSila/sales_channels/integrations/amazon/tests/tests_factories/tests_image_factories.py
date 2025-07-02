import json
from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from media.models import Media, MediaProductThrough
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


class AmazonProductImageFactoryTest(TestCase):
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
        # set remote_type attribute used by factories
        self.remote_product.remote_type = "PRODUCT"

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

    def test_create_factory_value_only(self):
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

    def test_update_factory_value_only(self):
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
