from core.tests import TestCase
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from properties.schema.types.filters import PropertyFilter, PropertySelectValueFilter


# class PropertyFilterTranslationTestCase(TestCase):
#     def setUp(self):
#         super().setUp()
#         self.multi_tenant_company.language = "en"
#         self.multi_tenant_company.languages = ["en", "fr"]
#         self.multi_tenant_company.save()
#
#         self.p1 = Property.objects.create(
#             multi_tenant_company=self.multi_tenant_company,
#             type=Property.TYPES.SELECT,
#         )
#         PropertyTranslation.objects.create(
#             property=self.p1,
#             language="en",
#             name="Color",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#
#         self.p2 = Property.objects.create(
#             multi_tenant_company=self.multi_tenant_company,
#             type=Property.TYPES.SELECT,
#         )
#         PropertyTranslation.objects.create(
#             property=self.p2,
#             language="en",
#             name="Size",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#         PropertyTranslation.objects.create(
#             property=self.p2,
#             language="fr",
#             name="Taille",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#
#         self.p3 = Property.objects.create(
#             multi_tenant_company=self.multi_tenant_company,
#             type=Property.TYPES.SELECT,
#         )
#         PropertyTranslation.objects.create(
#             property=self.p3,
#             language="fr",
#             name="Poids",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#
#     def test_missing_main_translation_true(self):
#         qs, _ = PropertyFilter().missing_main_translation(
#             Property.objects.filter(multi_tenant_company=self.multi_tenant_company),
#             True,
#             "",
#         )
#         self.assertSetEqual(set(qs), {self.p3})
#
#     def test_missing_main_translation_false(self):
#         qs, _ = PropertyFilter().missing_main_translation(
#             Property.objects.filter(multi_tenant_company=self.multi_tenant_company),
#             False,
#             "",
#         )
#         self.assertSetEqual(set(qs), {self.p1, self.p2})
#
#     def test_missing_translations_true(self):
#         qs, _ = PropertyFilter().missing_translations(
#             Property.objects.filter(multi_tenant_company=self.multi_tenant_company),
#             True,
#             "",
#         )
#         self.assertSetEqual(set(qs), {self.p1, self.p3})
#
#     def test_missing_translations_false(self):
#         qs, _ = PropertyFilter().missing_translations(
#             Property.objects.filter(multi_tenant_company=self.multi_tenant_company),
#             False,
#             "",
#         )
#         self.assertSetEqual(set(qs), {self.p2})
#
#
# class PropertySelectValueFilterTranslationTestCase(TestCase):
#     def setUp(self):
#         super().setUp()
#         self.multi_tenant_company.language = "en"
#         self.multi_tenant_company.languages = ["en", "fr"]
#         self.multi_tenant_company.save()
#
#         self.property = Property.objects.create(
#             multi_tenant_company=self.multi_tenant_company,
#             type=Property.TYPES.SELECT,
#         )
#         PropertyTranslation.objects.create(
#             property=self.property,
#             language="en",
#             name="Color",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#         PropertyTranslation.objects.create(
#             property=self.property,
#             language="fr",
#             name="Couleur",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#
#         self.v1 = PropertySelectValue.objects.create(
#             property=self.property,
#             multi_tenant_company=self.multi_tenant_company,
#         )
#         PropertySelectValueTranslation.objects.create(
#             propertyselectvalue=self.v1,
#             language="en",
#             value="Red",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#
#         self.v2 = PropertySelectValue.objects.create(
#             property=self.property,
#             multi_tenant_company=self.multi_tenant_company,
#         )
#         PropertySelectValueTranslation.objects.create(
#             propertyselectvalue=self.v2,
#             language="en",
#             value="Green",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#         PropertySelectValueTranslation.objects.create(
#             propertyselectvalue=self.v2,
#             language="fr",
#             value="Vert",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#
#         self.v3 = PropertySelectValue.objects.create(
#             property=self.property,
#             multi_tenant_company=self.multi_tenant_company,
#         )
#         PropertySelectValueTranslation.objects.create(
#             propertyselectvalue=self.v3,
#             language="fr",
#             value="Bleu",
#             multi_tenant_company=self.multi_tenant_company,
#         )
#
#     def test_missing_main_translation_true(self):
#         qs, _ = PropertySelectValueFilter().missing_main_translation(
#             PropertySelectValue.objects.filter(multi_tenant_company=self.multi_tenant_company),
#             True,
#             "",
#         )
#         self.assertSetEqual(set(qs), {self.v3})
#
#     def test_missing_main_translation_false(self):
#         qs, _ = PropertySelectValueFilter().missing_main_translation(
#             PropertySelectValue.objects.filter(multi_tenant_company=self.multi_tenant_company),
#             False,
#             "",
#         )
#         self.assertSetEqual(set(qs), {self.v1, self.v2})
#
#     def test_missing_translations_true(self):
#         qs, _ = PropertySelectValueFilter().missing_translations(
#             PropertySelectValue.objects.filter(multi_tenant_company=self.multi_tenant_company),
#             True,
#             "",
#         )
#         self.assertSetEqual(set(qs), {self.v1, self.v3})
#
#     def test_missing_translations_false(self):
#         qs, _ = PropertySelectValueFilter().missing_translations(
#             PropertySelectValue.objects.filter(multi_tenant_company=self.multi_tenant_company),
#             False,
#             "",
#         )
#         self.assertSetEqual(set(qs), {self.v2})
