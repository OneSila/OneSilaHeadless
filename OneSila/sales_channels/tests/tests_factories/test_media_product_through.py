from unittest.mock import Mock, patch

from core.tests import TestCase
from model_bakery import baker

from media.models import Media, MediaProductThrough
from products.models import Product
from integrations.models import IntegrationObjectMixin
from sales_channels.integrations.shopify.models.products import (
    ShopifyImageProductAssociation,
    ShopifyProduct,
)
from sales_channels.integrations.shopify.models.sales_channels import (
    ShopifySalesChannel,
    ShopifySalesChannelView,
)
from sales_channels.integrations.shopify.factories.products.images import (
    ShopifyMediaProductThroughCreateFactory,
)
from sales_channels.models.products import RemoteImage
from sales_channels.models.sales_channels import SalesChannelViewAssign


def _integration_save_without_checks(self, *args, **kwargs):
    return super(IntegrationObjectMixin, self).save(*args, **kwargs)


class RemoteMediaProductThroughCreateFactoryTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            ShopifySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://store.example.com",
        )
        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.media = baker.make(
            Media,
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
        )
        self.default_assignment = MediaProductThrough.objects.create(
            product=self.product,
            media=self.media,
            sort_order=5,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product = baker.make(
            ShopifyProduct,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.sales_channel_view = baker.make(
            ShopifySalesChannelView,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            url="https://store.example.com",
        )
        self.view_assign = SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel_view=self.sales_channel_view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _make_channel_assignment(self, **kwargs):
        defaults = {
            "product": self.product,
            "media": self.media,
            "sales_channel": self.sales_channel,
            "sort_order": 15,
            "is_main_image": True,
            "multi_tenant_company": self.multi_tenant_company,
        }
        defaults.update(kwargs)
        return MediaProductThrough.objects.create(**defaults)

    def test_reuses_existing_default_remote_assignment(self):
        remote_image = baker.make(
            RemoteImage,
            sales_channel=self.sales_channel,
            local_instance=self.media,
            remote_id="gid://shopify/MediaImage/1",
            multi_tenant_company=self.multi_tenant_company,
        )
        existing_remote_assignment = baker.make(
            ShopifyImageProductAssociation,
            sales_channel=self.sales_channel,
            local_instance=self.default_assignment,
            remote_product=self.remote_product,
            remote_image=remote_image,
            remote_id="gid://shopify/ProductImage/1",
            successfully_created=False,
            current_position=3,
            multi_tenant_company=self.multi_tenant_company,
        )
        channel_assignment = self._make_channel_assignment()
        factory = ShopifyMediaProductThroughCreateFactory(
            self.sales_channel,
            channel_assignment,
            remote_product=self.remote_product,
            api=Mock(),
        )

        with patch(
            "sales_channels.factories.products.images.remote_instance_post_create.send"
        ) as mock_signal, patch.object(
            IntegrationObjectMixin,
            "save",
            _integration_save_without_checks,
        ):
            factory.run()

        mock_signal.assert_called_once()
        remote_instance = ShopifyImageProductAssociation.objects.get(
            local_instance=channel_assignment,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        self.assertEqual(factory.remote_instance, remote_instance)
        self.assertEqual(remote_instance.remote_id, existing_remote_assignment.remote_id)
        self.assertEqual(remote_instance.remote_image, remote_image)
        self.assertFalse(remote_instance.successfully_created)
        self.assertEqual(remote_instance.current_position, channel_assignment.sort_order)

    def test_returns_existing_remote_assignment_for_channel(self):
        channel_assignment = self._make_channel_assignment(sort_order=22)
        existing_remote_assignment = baker.make(
            ShopifyImageProductAssociation,
            sales_channel=self.sales_channel,
            local_instance=channel_assignment,
            remote_product=self.remote_product,
            remote_id="gid://shopify/ProductImage/2",
            current_position=9,
            multi_tenant_company=self.multi_tenant_company,
        )
        factory = ShopifyMediaProductThroughCreateFactory(
            self.sales_channel,
            channel_assignment,
            remote_product=self.remote_product,
            api=Mock(),
        )

        with patch(
            "sales_channels.factories.products.images.remote_instance_post_create.send"
        ) as mock_signal, patch.object(
            IntegrationObjectMixin,
            "save",
            _integration_save_without_checks,
        ):
            factory.run()

        mock_signal.assert_not_called()
        self.assertEqual(factory.remote_instance, existing_remote_assignment)
        # No new remote assignments created
        self.assertEqual(
            ShopifyImageProductAssociation.objects.filter(
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            ).count(),
            1,
        )
