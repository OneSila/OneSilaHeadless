from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from core.models import MultiTenantCompany
from products.models import SimpleProduct, ProductTranslation, Product, ProductTranslationBulletPoint


DUPLICATE_PRODUCT_MUTATION = """
    mutation(
      $product: ProductPartialInput!,
      $sku: String,
      $createAsAlias: Boolean,
      $createRelationships: Boolean
    ) {
      duplicateProduct(
        product: $product,
        sku: $sku,
        createAsAlias: $createAsAlias,
        createRelationships: $createRelationships
      ) {
        id
        sku
      }
    }
"""

TRANSLATION_CLEAN_FIELD_MUTATION = """
    mutation(
      $translation: ProductTranslationPartialInput!,
      $field: ContentField!
    ) {
      cleanTranslationField(
        translation: $translation,
        field: $field
      ) {
        id
        name
        shortDescription
        description
        subtitle
      }
    }
"""


class DuplicateProductMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        ProductTranslation.objects.create(
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Original",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_duplicate_product_mutation(self):
        resp = self.strawberry_test_client(
            query=DUPLICATE_PRODUCT_MUTATION,
            variables={
                "product": {"id": self.to_global_id(self.product)},
                "sku": None,
                "createAsAlias": False,
                "createRelationships": True,
            },
        )

        self.assertIsNone(resp.errors)
        data = resp.data["duplicateProduct"]
        self.assertIsNotNone(data["id"])

    def test_duplicate_product_mutation_existing_sku(self):
        resp = self.strawberry_test_client(
            query=DUPLICATE_PRODUCT_MUTATION,
            variables={
                "product": {"id": self.to_global_id(self.product)},
                "sku": self.product.sku,
                "createAsAlias": False,
                "createRelationships": True,
            },
            asserts_errors=False,
        )

        self.assertTrue(resp.errors is not None)

    def test_duplicate_product_mutation_create_as_alias(self):
        resp = self.strawberry_test_client(
            query=DUPLICATE_PRODUCT_MUTATION,
            variables={
                "product": {"id": self.to_global_id(self.product)},
                "sku": None,
                "createAsAlias": True,
                "createRelationships": True,
            },
        )
        self.assertIsNone(resp.errors)
        data = resp.data["duplicateProduct"]
        _, id = self.from_global_id(data["id"])

        new_product = Product.objects.get(id=id)
        self.assertEqual(new_product.type, Product.ALIAS)
        self.assertEqual(new_product.alias_parent_product, self.product)


class CleanTranslationFieldMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.translation = ProductTranslation.objects.create(
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Original",
            short_description="Short text",
            description="Long text",
            subtitle="Subtitle text",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=self.translation,
            text="Bullet 1",
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=self.translation,
            text="Bullet 2",
            sort_order=1,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_clean_translation_field_short_description(self):
        resp = self.strawberry_test_client(
            query=TRANSLATION_CLEAN_FIELD_MUTATION,
            variables={
                "translation": {"id": self.to_global_id(self.translation)},
                "field": "SHORT_DESCRIPTION",
            },
        )

        self.assertIsNone(resp.errors)
        self.translation.refresh_from_db()
        self.assertIsNone(self.translation.short_description)
        self.assertEqual(resp.data["cleanTranslationField"]["shortDescription"], None)

    def test_clean_translation_field_bullet_points(self):
        resp = self.strawberry_test_client(
            query=TRANSLATION_CLEAN_FIELD_MUTATION,
            variables={
                "translation": {"id": self.to_global_id(self.translation)},
                "field": "BULLET_POINTS",
            },
        )

        self.assertIsNone(resp.errors)
        self.assertEqual(self.translation.bullet_points.count(), 0)

    def test_clean_translation_field_invalid_company(self):
        other_company = baker.make(MultiTenantCompany)
        other_product = SimpleProduct.objects.create(multi_tenant_company=other_company)
        other_translation = ProductTranslation.objects.create(
            product=other_product,
            language=other_company.language,
            name="Other",
            multi_tenant_company=other_company,
        )

        resp = self.strawberry_test_client(
            query=TRANSLATION_CLEAN_FIELD_MUTATION,
            variables={
                "translation": {"id": self.to_global_id(other_translation)},
                "field": "SHORT_DESCRIPTION",
            },
            asserts_errors=True,
        )

        self.assertTrue(resp.errors is not None)
