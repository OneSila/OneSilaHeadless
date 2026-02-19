from django.core.exceptions import ValidationError
from model_bakery import baker

from core.tests import TestCase
from properties.models import Property
from sales_channels.integrations.shein.models import SheinInternalProperty, SheinSalesChannel


class SheinInternalPropertyModelTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.model.test",
            remote_id="SC-INT-1",
        )

    def test_allowed_types_comes_from_definition(self) -> None:
        internal_property = SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="supplier_code",
            name="Supplier code",
            type=Property.TYPES.TEXT,
            payload_field="supplier_code",
        )

        self.assertEqual(
            internal_property.allowed_types,
            [Property.TYPES.TEXT, Property.TYPES.DESCRIPTION, Property.TYPES.INT],
        )

    def test_save_rejects_disallowed_local_property_type(self) -> None:
        invalid_local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.BOOLEAN,
        )

        with self.assertRaises(ValidationError) as raised:
            SheinInternalProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                code="quantity_info__quantity",
                name="Quantity",
                type=Property.TYPES.INT,
                payload_field="quantity",
                local_instance=invalid_local_property,
            )

        self.assertIn(
            "Allowed types: INT, FLOAT",
            str(raised.exception),
        )
