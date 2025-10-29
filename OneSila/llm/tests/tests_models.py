from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.tests import TestCase
from llm.models import ChatGptProductFeedConfig
from properties.models import Property, PropertySelectValue


class ChatGptProductFeedConfigModelTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.condition_property = self._create_property(internal_name="condition")
        self.brand_property = Property.objects.get(multi_tenant_company=self.multi_tenant_company, internal_name="brand")
        self.material_property = self._create_property(internal_name="material")
        self.color_property = self._create_property(internal_name="color")
        self.size_property = self._create_property(internal_name="size")

        self.condition_value = self._create_value(prop=self.condition_property)
        self.color_value = self._create_value(prop=self.color_property)

    def _create_property(self, *, internal_name):
        return Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            internal_name=internal_name,
        )

    def _create_value(self, *, prop):
        return PropertySelectValue.objects.create(
            property=prop,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _create_valid_config(self):
        return ChatGptProductFeedConfig(
            multi_tenant_company=self.multi_tenant_company,
            condition_property=self.condition_property,
            brand_property=self.brand_property,
            material_property=self.material_property,
            color_property=self.color_property,
            size_property=self.size_property,
            condtion_new_value=self.condition_value,
        )

    def test_allows_partial_configuration_on_create(self):
        config = ChatGptProductFeedConfig(
            multi_tenant_company=self.multi_tenant_company,
        )

        config.full_clean()

    def test_requires_required_fields_after_creation(self):
        config = self._create_valid_config()
        config.save(force_save=True)

        config.brand_property = None

        with self.assertRaises(ValidationError) as context:
            config.full_clean()

        self.assertIn("brand_property", context.exception.error_dict)

    def test_condition_values_must_match_property(self):
        config = self._create_valid_config()
        config.condtion_new_value = self.color_value

        with self.assertRaises(ValidationError) as context:
            config.full_clean()

        self.assertIn("condtion_new_value", context.exception.error_dict)

    def test_unique_per_multi_tenant_company(self):
        config = self._create_valid_config()
        config.save(force_save=True)

        duplicate = self._create_valid_config()

        with self.assertRaises(IntegrityError):
            duplicate.save(force_save=True)
