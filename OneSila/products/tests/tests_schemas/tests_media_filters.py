from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from media.models import Media, MediaProductThrough
from products.models import SimpleProduct
from sales_channels.integrations.amazon.models import AmazonSalesChannel


class ProductFilterMediaQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="media-main.example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.other_sales_channel = AmazonSalesChannel.objects.create(
            hostname="media-other.example.com",
            multi_tenant_company=self.multi_tenant_company,
        )

    def _query_ids(self, *, query: str, variables: dict) -> set[int]:
        resp = self.strawberry_test_client(
            query=query,
            variables=variables,
        )
        self.assertIsNone(resp.errors)
        return {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        }

    def _assert_media_filter(
        self,
        *,
        query: str,
        media_type: str,
        missing: bool,
        use_default_sales_channel: bool = False,
    ) -> None:
        with_media = SimpleProduct.objects.create(
            sku=f"media-with-{media_type}-{missing}-{use_default_sales_channel}",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_media = SimpleProduct.objects.create(
            sku=f"media-without-{media_type}-{missing}-{use_default_sales_channel}",
            multi_tenant_company=self.multi_tenant_company,
        )

        target_media = Media.objects.create(
            type=media_type,
            multi_tenant_company=self.multi_tenant_company,
        )
        other_media = Media.objects.create(
            type=media_type,
            multi_tenant_company=self.multi_tenant_company,
        )

        if use_default_sales_channel:
            MediaProductThrough.objects.create(
                product=with_media,
                media=target_media,
                sales_channel=None,
                multi_tenant_company=self.multi_tenant_company,
            )
            MediaProductThrough.objects.create(
                product=without_media,
                media=other_media,
                sales_channel=self.sales_channel,
                multi_tenant_company=self.multi_tenant_company,
            )
            sales_channel_value = "None"
        else:
            MediaProductThrough.objects.create(
                product=with_media,
                media=target_media,
                sales_channel=self.sales_channel,
                multi_tenant_company=self.multi_tenant_company,
            )
            MediaProductThrough.objects.create(
                product=without_media,
                media=other_media,
                sales_channel=self.other_sales_channel,
                multi_tenant_company=self.multi_tenant_company,
            )
            sales_channel_value = self.to_global_id(self.sales_channel)

        ids = self._query_ids(
            query=query,
            variables={"salesChannelId": sales_channel_value},
        )
        self.assertSetEqual(ids, {without_media.id} if missing else {with_media.id})

    def test_filter_by_has_images_in_sales_channel(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_IMAGES_IN_SALES_CHANNEL

        self._assert_media_filter(
            query=PRODUCTS_FILTER_BY_HAS_IMAGES_IN_SALES_CHANNEL,
            media_type=Media.IMAGE,
            missing=False,
        )

    def test_filter_by_missing_images_in_sales_channel(self):
        from .queries import PRODUCTS_FILTER_BY_MISSING_IMAGES_IN_SALES_CHANNEL

        self._assert_media_filter(
            query=PRODUCTS_FILTER_BY_MISSING_IMAGES_IN_SALES_CHANNEL,
            media_type=Media.IMAGE,
            missing=True,
        )

    def test_filter_by_has_documents_in_default_sales_channel(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_DOCUMENTS_IN_SALES_CHANNEL

        self._assert_media_filter(
            query=PRODUCTS_FILTER_BY_HAS_DOCUMENTS_IN_SALES_CHANNEL,
            media_type=Media.FILE,
            missing=False,
            use_default_sales_channel=True,
        )

    def test_filter_by_missing_documents_in_default_sales_channel(self):
        from .queries import PRODUCTS_FILTER_BY_MISSING_DOCUMENTS_IN_SALES_CHANNEL

        self._assert_media_filter(
            query=PRODUCTS_FILTER_BY_MISSING_DOCUMENTS_IN_SALES_CHANNEL,
            media_type=Media.FILE,
            missing=True,
            use_default_sales_channel=True,
        )

    def test_filter_by_has_videos_in_sales_channel(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_VIDEOS_IN_SALES_CHANNEL

        self._assert_media_filter(
            query=PRODUCTS_FILTER_BY_HAS_VIDEOS_IN_SALES_CHANNEL,
            media_type=Media.VIDEO,
            missing=False,
        )

    def test_filter_by_missing_videos_in_sales_channel(self):
        from .queries import PRODUCTS_FILTER_BY_MISSING_VIDEOS_IN_SALES_CHANNEL

        self._assert_media_filter(
            query=PRODUCTS_FILTER_BY_MISSING_VIDEOS_IN_SALES_CHANNEL,
            media_type=Media.VIDEO,
            missing=True,
        )
