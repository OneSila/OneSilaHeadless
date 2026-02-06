from django.conf import settings
from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import ProductTranslation, ProductTranslationBulletPoint, SimpleProduct
from sales_channels.integrations.amazon.models import AmazonSalesChannel


class ProductFilterContentQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.language_code = settings.LANGUAGES[0][0]
        self.multi_tenant_company.language = self.language_code
        self.multi_tenant_company.languages = [self.language_code]
        self.multi_tenant_company.save(update_fields=["language", "languages"])
        self.user.language = self.language_code
        self.user.save(update_fields=["language"])
        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="content-filter.example.com",
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

    def _create_translation_for_field(
        self,
        *,
        product: SimpleProduct,
        field: str,
        value: str | None,
        is_default: bool,
    ) -> None:
        translation = ProductTranslation.objects.create(
            product=product,
            sales_channel=None if is_default else self.sales_channel,
            language=self.language_code,
            name="fallback-name",
            multi_tenant_company=self.multi_tenant_company,
        )

        if field == "NAME":
            translation.name = value
            translation.save(update_fields=["name"])
            return

        if field == "SUBTITLE":
            translation.subtitle = value
            translation.save(update_fields=["subtitle"])
            return

        if field == "DESCRIPTION":
            translation.description = value
            translation.save(update_fields=["description"])
            return

        if field == "SHORT_DESCRIPTION":
            translation.short_description = value
            translation.save(update_fields=["short_description"])
            return

        if field == "URL_KEY":
            translation.url_key = value
            translation.save(update_fields=["url_key"])
            return

        if field == "BULLET_POINTS" and value is not None:
            ProductTranslationBulletPoint.objects.create(
                product_translation=translation,
                text=value,
                sort_order=0,
                multi_tenant_company=self.multi_tenant_company,
            )

    def _assert_content_filter(
        self,
        *,
        field: str,
        missing: bool,
        is_default: bool = False,
        present_value: str,
        missing_value: str | None,
    ) -> None:
        from .queries import (
            PRODUCTS_FILTER_BY_CONTENT_FIELD_IN_VIEW,
            PRODUCTS_FILTER_BY_MISSING_CONTENT_FIELD_IN_VIEW,
        )

        with_content = SimpleProduct.objects.create(
            sku=f"content-has-{field}-{is_default}-{missing}",
            multi_tenant_company=self.multi_tenant_company,
        )
        missing_content = SimpleProduct.objects.create(
            sku=f"content-missing-{field}-{is_default}-{missing}",
            multi_tenant_company=self.multi_tenant_company,
        )

        self._create_translation_for_field(
            product=with_content,
            field=field,
            value=present_value,
            is_default=is_default,
        )
        self._create_translation_for_field(
            product=missing_content,
            field=field,
            value=missing_value,
            is_default=is_default,
        )

        query = (
            PRODUCTS_FILTER_BY_MISSING_CONTENT_FIELD_IN_VIEW
            if missing
            else PRODUCTS_FILTER_BY_CONTENT_FIELD_IN_VIEW
        )
        content_view_key = (
            f"0.{self.language_code}"
            if is_default
            else f"{self.sales_channel.id}.{self.language_code}"
        )

        ids = self._query_ids(
            query=query,
            variables={
                "contentViewKey": content_view_key,
                "field": field,
            },
        )
        self.assertSetEqual(ids, {missing_content.id} if missing else {with_content.id})

    def test_filter_has_title_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="NAME",
            missing=False,
            present_value="Title Value",
            missing_value="",
        )

    def test_filter_missing_title_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="NAME",
            missing=True,
            present_value="Title Value",
            missing_value="",
        )

    def test_filter_has_subtitle_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="SUBTITLE",
            missing=False,
            present_value="Subtitle Value",
            missing_value="",
        )

    def test_filter_missing_subtitle_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="SUBTITLE",
            missing=True,
            present_value="Subtitle Value",
            missing_value="",
        )

    def test_filter_has_description_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="DESCRIPTION",
            missing=False,
            present_value="Description Value",
            missing_value="<p><br></p>",
        )

    def test_filter_missing_description_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="DESCRIPTION",
            missing=True,
            present_value="Description Value",
            missing_value="<p><br></p>",
        )

    def test_filter_has_short_description_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="SHORT_DESCRIPTION",
            missing=False,
            present_value="Short Description Value",
            missing_value="",
        )

    def test_filter_missing_short_description_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="SHORT_DESCRIPTION",
            missing=True,
            present_value="Short Description Value",
            missing_value="",
        )

    def test_filter_has_url_key_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="URL_KEY",
            missing=False,
            present_value="url-key-value",
            missing_value="",
        )

    def test_filter_missing_url_key_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="URL_KEY",
            missing=True,
            present_value="url-key-value",
            missing_value="",
        )

    def test_filter_has_bullet_points_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="BULLET_POINTS",
            missing=False,
            present_value="Bullet Value",
            missing_value="<p><br></p>",
        )

    def test_filter_missing_bullet_points_in_sales_channel_in_language(self):
        self._assert_content_filter(
            field="BULLET_POINTS",
            missing=True,
            present_value="Bullet Value",
            missing_value="<p><br></p>",
        )

    def test_filter_has_title_in_default_language(self):
        self._assert_content_filter(
            field="NAME",
            missing=False,
            is_default=True,
            present_value="Default Title Value",
            missing_value="",
        )

    def test_filter_missing_title_in_default_language(self):
        self._assert_content_filter(
            field="NAME",
            missing=True,
            is_default=True,
            present_value="Default Title Value",
            missing_value="",
        )

    def test_filter_has_title_and_missing_description_with_empty_rich_text(self):
        product_expected = SimpleProduct.objects.create(
            sku="content-combined-expected",
            multi_tenant_company=self.multi_tenant_company,
        )
        product_with_description = SimpleProduct.objects.create(
            sku="content-combined-with-description",
            multi_tenant_company=self.multi_tenant_company,
        )
        product_missing_title = SimpleProduct.objects.create(
            sku="content-combined-missing-title",
            multi_tenant_company=self.multi_tenant_company,
        )

        ProductTranslation.objects.create(
            product=product_expected,
            sales_channel=self.sales_channel,
            language=self.language_code,
            name="Has title",
            description="<p><br></p>",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslation.objects.create(
            product=product_with_description,
            sales_channel=self.sales_channel,
            language=self.language_code,
            name="Has title",
            description="Real description",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslation.objects.create(
            product=product_missing_title,
            sales_channel=self.sales_channel,
            language=self.language_code,
            name="",
            description="<p><br></p>",
            multi_tenant_company=self.multi_tenant_company,
        )

        query = """
        query products($contentViewKey: String!) {
          products(
            filters: {
              contentFieldInView: {contentViewKey: $contentViewKey, field: NAME}
              NOT: {contentFieldInView: {contentViewKey: $contentViewKey, field: DESCRIPTION}}
            }
          ) {
            edges { node { id } }
          }
        }
        """
        ids = self._query_ids(
            query=query,
            variables={"contentViewKey": f"{self.sales_channel.id}.{self.language_code}"},
        )
        self.assertSetEqual(ids, {product_expected.id})
