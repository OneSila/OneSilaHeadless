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


class PropertySelectValueSearchQuerySetTest(TestCase):
    def test_literal_exact_match_search(self):
        property_instance, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name='size',
            defaults={
                'type': Property.TYPES.SELECT,
                'is_public_information': True,
            },
        )
        PropertyTranslation.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            property=property_instance,
            language=self.multi_tenant_company.language,
            defaults={
                'name': 'Size',
                'multi_tenant_company': self.multi_tenant_company,
            },
        )

        for index in range(5000):
            value_instance = PropertySelectValue.objects.create(
                property=property_instance,
                multi_tenant_company=self.multi_tenant_company,
            )
            PropertySelectValueTranslation.objects.create(
                propertyselectvalue=value_instance,
                language=self.multi_tenant_company.language,
                value=f"{index}S value",
                multi_tenant_company=self.multi_tenant_company,
            )

        exact_match = PropertySelectValue.objects.create(
            property=property_instance,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=exact_match,
            language=self.multi_tenant_company.language,
            value="S",
            multi_tenant_company=self.multi_tenant_company,
        )

        queryset, _ = PropertySelectValue.objects.filter(
            property=property_instance,
            multi_tenant_company=self.multi_tenant_company,
        ).get_search_results(
            search_term='"S"',
            search_fields=PropertySelectValue._meta.search_terms,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertEqual(queryset.count(), 1)

        result = queryset.first()
        self.assertIsNotNone(result)
        self.assertEqual(
            result.value,
            "S",
        )