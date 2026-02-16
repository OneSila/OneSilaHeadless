from django.core.exceptions import ValidationError
from model_bakery import baker

from core.tests import TestCase
from properties.models import Property
from sales_channels.integrations.ebay.models import EbayInternalProperty, EbaySalesChannel


class EbayInternalPropertyModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_allowed_types_default_is_loaded_from_constants(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.INT,
        )

        internal_property = EbayInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="packageWeightAndSize__dimensions__length",
            name="Package Length",
            type=Property.TYPES.FLOAT,
            local_instance=local_property,
            is_root=True,
        )

        self.assertEqual(
            internal_property.allowed_types,
            [Property.TYPES.FLOAT, Property.TYPES.INT],
        )

    def test_type_must_be_in_allowed_types(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )

        with self.assertRaises(ValidationError):
            EbayInternalProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                code="packageWeightAndSize__dimensions__length",
                name="Package Length",
                type=Property.TYPES.TEXT,
                local_instance=local_property,
                is_root=True,
            )

    def test_local_instance_type_must_be_allowed(self):
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.FLOAT,
        )

        with self.assertRaises(ValidationError):
            EbayInternalProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                code="isbn",
                name="ISBN",
                type=Property.TYPES.TEXT,
                local_instance=local_property,
                is_root=False,
            )
