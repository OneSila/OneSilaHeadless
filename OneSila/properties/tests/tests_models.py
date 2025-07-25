from core.tests import TestCase
from properties.models import Property


class PropertyManagerGetOrCreateTestCase(TestCase):
    def test_get_or_create_auto_increment_internal_name(self):
        """Ensure a unique internal_name is generated for each call."""
        # Existing property with internal_name "color"
        Property.objects.create(
            internal_name="color",
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )

        prop1, created1 = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
            internal_name="color",
        )
        self.assertTrue(created1)
        self.assertEqual(prop1.internal_name, "color_1")

        prop2, created2 = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
            internal_name="color",
        )
        self.assertFalse(created2)
        self.assertEqual(prop2.internal_name, "color_1")
