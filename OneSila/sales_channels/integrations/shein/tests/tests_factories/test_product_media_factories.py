from unittest.mock import PropertyMock, patch

from core.tests import TestCase
from media.models import Media, MediaProductThrough
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.shein.factories.products import (
    SheinMediaProductThroughCreateFactory,
    SheinMediaProductThroughUpdateFactory,
    SheinMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.models.products import RemoteImageProductAssociation, RemoteProduct


class SheinMediaProductThroughFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)

        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = RemoteProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-1",
        )

    def _make_image(self, url: str, *, sort: int, is_main: bool) -> MediaProductThrough:
        media = baker.make(
            Media,
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
            description=url,
        )
        media.image_url = lambda: url  # type: ignore[attr-defined]

        return MediaProductThrough.objects.create(
            product=self.product,
            media=media,
            sort_order=sort,
            is_main_image=is_main,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_builds_image_info_payload(self):
        self._make_image("https://example.com/main.jpg", sort=0, is_main=True)
        self._make_image("https://example.com/detail.jpg", sort=1, is_main=False)

        factory = SheinMediaProductThroughCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=MediaProductThrough.objects.first(),
            remote_product=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.run()

        assoc = RemoteImageProductAssociation.objects.get(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
        )
        payload = factory.value

        self.assertEqual(len(payload["image_info"]["image_info_list"]), 2)
        first = payload["image_info"]["image_info_list"][0]
        self.assertEqual(first["image_type"], 1)
        self.assertEqual(first["image_url"], "https://example.com/main.jpg")
        self.assertEqual(first["image_sort"], 1)

        self.assertEqual(assoc.local_instance.product, self.product)

    def test_update_factory_reuses_payload(self):
        through = self._make_image("https://example.com/main.jpg", sort=0, is_main=True)
        RemoteImageProductAssociation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=through,
            remote_product=self.remote_product,
        )

        factory = SheinMediaProductThroughUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=through,
            remote_product=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.run()

        self.assertEqual(factory.value["image_info"]["image_info_list"][0]["image_url"], "https://example.com/main.jpg")

    def test_delete_factory_returns_payload(self):
        through = self._make_image("https://example.com/main.jpg", sort=0, is_main=True)
        RemoteImageProductAssociation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=through,
            remote_product=self.remote_product,
        )

        factory = SheinMediaProductThroughDeleteFactory(
            sales_channel=self.sales_channel,
            local_instance=through,
            remote_product=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.run()

        self.assertIn("image_info", factory.value)
