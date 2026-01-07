from core.tests import TestCase
from model_bakery import baker

from products.factories.translation_import import ProductTranslationImportFactory
from products.models import ProductTranslation, ProductTranslationBulletPoint, SimpleProduct
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.models import SalesChannel


class ProductTranslationImportFactoryTestCase(TestCase):
    def test_import_single_language_respects_existing_values(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        source_channel = baker.make(AmazonSalesChannel, multi_tenant_company=self.multi_tenant_company)
        target_channel = baker.make(AmazonSalesChannel, multi_tenant_company=self.multi_tenant_company)

        ProductTranslation.objects.create(
            product=product,
            language="en",
            sales_channel=source_channel,
            name="Source Name",
            description="<p>Source description</p>",
            multi_tenant_company=self.multi_tenant_company,
        )

        destination_translation = ProductTranslation.objects.create(
            product=product,
            language="en",
            sales_channel=target_channel,
            name="Existing Name",
            description="<p><br></p>",
            multi_tenant_company=self.multi_tenant_company,
        )

        factory = ProductTranslationImportFactory(
            multi_tenant_company=self.multi_tenant_company,
            products=[product],
            source_channel=source_channel,
            target_channel=target_channel,
            language="en",
            override=False,
            all_languages=False,
            fields=["name", "description"],
        )
        factory.work()

        destination_translation.refresh_from_db()
        self.assertEqual(destination_translation.name, "Existing Name")
        self.assertEqual(destination_translation.description, "<p>Source description</p>")

    def test_import_all_languages_overwrites_bullet_points(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        source_channel = baker.make(SalesChannel, multi_tenant_company=self.multi_tenant_company)
        target_channel = baker.make(SalesChannel, multi_tenant_company=self.multi_tenant_company)

        source_en = ProductTranslation.objects.create(
            product=product,
            language="en",
            sales_channel=source_channel,
            name="Source EN",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=source_en,
            text="Source EN 1",
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=source_en,
            text="Source EN 2",
            sort_order=1,
            multi_tenant_company=self.multi_tenant_company,
        )

        source_fr = ProductTranslation.objects.create(
            product=product,
            language="fr",
            sales_channel=source_channel,
            name="Source FR",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=source_fr,
            text="Source FR 1",
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )

        destination_en = ProductTranslation.objects.create(
            product=product,
            language="en",
            sales_channel=target_channel,
            name="Destination EN",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=destination_en,
            text="Destination EN",
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )

        factory = ProductTranslationImportFactory(
            multi_tenant_company=self.multi_tenant_company,
            products=[product],
            source_channel=source_channel,
            target_channel=target_channel,
            language=None,
            override=True,
            all_languages=True,
            fields=["name", "bullet_points"],
        )
        factory.work()

        destination_en.refresh_from_db()
        self.assertEqual(destination_en.name, "Source EN")
        self.assertEqual(
            list(destination_en.bullet_points.values_list("text", flat=True)),
            ["Source EN 1", "Source EN 2"],
        )

        destination_fr = ProductTranslation.objects.get(
            product=product,
            language="fr",
            sales_channel=target_channel,
        )
        self.assertEqual(destination_fr.name, "Source FR")
        self.assertEqual(
            list(destination_fr.bullet_points.values_list("text", flat=True)),
            ["Source FR 1"],
        )

    def test_import_bullet_points_fills_to_five_when_not_overriding(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        source_channel = baker.make(SalesChannel, multi_tenant_company=self.multi_tenant_company)
        target_channel = baker.make(SalesChannel, multi_tenant_company=self.multi_tenant_company)

        source_translation = ProductTranslation.objects.create(
            product=product,
            language="en",
            sales_channel=source_channel,
            name="Source EN",
            multi_tenant_company=self.multi_tenant_company,
        )
        for index in range(5):
            ProductTranslationBulletPoint.objects.create(
                product_translation=source_translation,
                text=f"Source {index + 1}",
                sort_order=index,
                multi_tenant_company=self.multi_tenant_company,
            )

        destination_translation = ProductTranslation.objects.create(
            product=product,
            language="en",
            sales_channel=target_channel,
            name="Destination EN",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=destination_translation,
            text="Destination 1",
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=destination_translation,
            text="Destination 2",
            sort_order=1,
            multi_tenant_company=self.multi_tenant_company,
        )

        factory = ProductTranslationImportFactory(
            multi_tenant_company=self.multi_tenant_company,
            products=[product],
            source_channel=source_channel,
            target_channel=target_channel,
            language="en",
            override=False,
            all_languages=False,
            fields=["bullet_points"],
        )
        factory.work()

        destination_translation.refresh_from_db()
        self.assertEqual(
            list(destination_translation.bullet_points.values_list("text", flat=True)),
            ["Destination 1", "Destination 2", "Source 1", "Source 2", "Source 3"],
        )
