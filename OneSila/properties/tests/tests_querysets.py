from core.tests import TestCase
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
)


class PropertyQuerySetTest(TestCase):
    def test_with_translated_name_single_query(self):
        props = []
        for i in range(2):
            prop = Property.objects.create(
                type=Property.TYPES.TEXT,
                multi_tenant_company=self.multi_tenant_company,
            )
            PropertyTranslation.objects.create(
                property=prop,
                language=self.multi_tenant_company.language,
                name=f"Prop {i}",
                multi_tenant_company=self.multi_tenant_company,
            )
            props.append(prop)

        qs = Property.objects.filter(
            multi_tenant_company=self.multi_tenant_company
        ).with_translated_name(language_code=self.multi_tenant_company.language)

        with self.assertNumQueries(1):
            names = [p.name for p in qs]

        # "Brand", "Product Type" are created by default with the mtc
        self.assertEqual(set(names), {"Brand", "Product Type", "Prop 0", "Prop 1"})

    def test_all_translated_name_multiple_queries(self):
        props = []
        for i in range(2):
            prop = Property.objects.create(
                type=Property.TYPES.TEXT,
                multi_tenant_company=self.multi_tenant_company,
            )
            PropertyTranslation.objects.create(
                property=prop,
                language=self.multi_tenant_company.language,
                name=f"Prop {i}",
                multi_tenant_company=self.multi_tenant_company,
            )
            props.append(prop)

        qs = Property.objects.filter(
            multi_tenant_company=self.multi_tenant_company
        ).all()

        # +2 because of brand and product type
        props_len = len(props) + 2
        with self.assertNumQueries(1 + (props_len * 3)):
            names = [p.name for p in qs]

        self.assertEqual(set(names), {"Brand", "Product Type", "Prop 0", "Prop 1"})


class PropertySelectValueQuerySetTest(TestCase):
    def test_with_translated_value_single_query(self):
        prop = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            property=prop,
            language=self.multi_tenant_company.language,
            name="PT",
            multi_tenant_company=self.multi_tenant_company,
        )

        values = []
        for i in range(2):
            val = PropertySelectValue.objects.create(
                property=prop,
                multi_tenant_company=self.multi_tenant_company,
            )
            PropertySelectValueTranslation.objects.create(
                propertyselectvalue=val,
                language=self.multi_tenant_company.language,
                value=f"Val {i}",
                multi_tenant_company=self.multi_tenant_company,
            )
            values.append(val)

        qs = PropertySelectValue.objects.filter(
            property=prop
        ).with_translated_value(language_code=self.multi_tenant_company.language)

        with self.assertNumQueries(1):
            vals = [v.value for v in qs]

        self.assertEqual(set(vals), {"Val 0", "Val 1"})

    def test_all_translated_value_multiple_queries(self):
        prop = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            property=prop,
            language=self.multi_tenant_company.language,
            name="PT",
            multi_tenant_company=self.multi_tenant_company,
        )

        values = []
        for i in range(2):
            val = PropertySelectValue.objects.create(
                property=prop,
                multi_tenant_company=self.multi_tenant_company,
            )
            PropertySelectValueTranslation.objects.create(
                propertyselectvalue=val,
                language=self.multi_tenant_company.language,
                value=f"Val {i}",
                multi_tenant_company=self.multi_tenant_company,
            )
            values.append(val)

        qs = PropertySelectValue.objects.filter(property=prop).all()

        with self.assertNumQueries(1 + (len(values) * 3)):
            vals = [v.value for v in qs]

        self.assertEqual(set(vals), {"Val 0", "Val 1"})
