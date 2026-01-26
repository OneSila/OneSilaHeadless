from django.conf import settings
from time import perf_counter

from core.tests import TestCase
from model_bakery import baker
from core.models import MultiTenantCompany
from products.models import Product
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
)


class PropertyQuerySetTest(TestCase):
    def test_used_in_products(self):
        prop_used = Property.objects.create(
            type=Property.TYPES.BOOLEAN,
            multi_tenant_company=self.multi_tenant_company,
        )
        prop_unused = Property.objects.create(
            type=Property.TYPES.BOOLEAN,
            multi_tenant_company=self.multi_tenant_company,
        )

        product = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=product,
            property=prop_used,
            value_boolean=True,
            multi_tenant_company=self.multi_tenant_company,
        )

        other_mtc = baker.make(MultiTenantCompany)
        other_prop_used = Property.objects.create(
            type=Property.TYPES.BOOLEAN,
            multi_tenant_company=other_mtc,
        )
        other_product = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=other_mtc,
        )
        ProductProperty.objects.create(
            product=other_product,
            property=other_prop_used,
            value_boolean=True,
            multi_tenant_company=other_mtc,
        )

        qs_used = Property.objects.used_in_products(
            multi_tenant_company_id=self.multi_tenant_company.id,
            used=True,
        )
        self.assertIn(prop_used, qs_used)
        self.assertNotIn(prop_unused, qs_used)
        self.assertNotIn(other_prop_used, qs_used)

        qs_unused = Property.objects.used_in_products(
            multi_tenant_company_id=self.multi_tenant_company.id,
            used=False,
        )
        self.assertIn(prop_unused, qs_unused)
        self.assertNotIn(prop_used, qs_unused)

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
    def test_used_in_products(self):
        prop_select = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        select_used = PropertySelectValue.objects.create(
            property=prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )
        select_unused = PropertySelectValue.objects.create(
            property=prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )

        prop_multi = Property.objects.create(
            type=Property.TYPES.MULTISELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        multi_used = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        multi_unused = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )

        product = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=product,
            property=prop_select,
            value_select=select_used,
            multi_tenant_company=self.multi_tenant_company,
        )
        pp_multi = ProductProperty.objects.create(
            product=product,
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        pp_multi.value_multi_select.add(multi_used)

        other_mtc = baker.make(MultiTenantCompany)
        other_prop = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=other_mtc,
        )
        other_value_used = PropertySelectValue.objects.create(
            property=other_prop,
            multi_tenant_company=other_mtc,
        )
        other_product = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=other_mtc,
        )
        ProductProperty.objects.create(
            product=other_product,
            property=other_prop,
            value_select=other_value_used,
            multi_tenant_company=other_mtc,
        )

        qs_used = PropertySelectValue.objects.used_in_products(
            multi_tenant_company_id=self.multi_tenant_company.id,
            used=True,
        )
        self.assertIn(select_used, qs_used)
        self.assertIn(multi_used, qs_used)
        self.assertNotIn(select_unused, qs_used)
        self.assertNotIn(multi_unused, qs_used)
        self.assertNotIn(other_value_used, qs_used)

        qs_unused = PropertySelectValue.objects.used_in_products(
            multi_tenant_company_id=self.multi_tenant_company.id,
            used=False,
        )
        self.assertIn(select_unused, qs_unused)
        self.assertIn(multi_unused, qs_unused)
        self.assertNotIn(select_used, qs_unused)
        self.assertNotIn(multi_used, qs_unused)

    def test_with_usage_count_counts_select_and_multi(self):
        prop_select = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        prop_multi = Property.objects.create(
            type=Property.TYPES.MULTISELECT,
            multi_tenant_company=self.multi_tenant_company,
        )

        select_used = PropertySelectValue.objects.create(
            property=prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )
        select_unused = PropertySelectValue.objects.create(
            property=prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )
        multi_used = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        multi_unused = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )

        product_one = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_two = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )

        ProductProperty.objects.create(
            product=product_one,
            property=prop_select,
            value_select=select_used,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=product_two,
            property=prop_select,
            value_select=select_used,
            multi_tenant_company=self.multi_tenant_company,
        )

        pp_multi_one = ProductProperty.objects.create(
            product=product_one,
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        pp_multi_two = ProductProperty.objects.create(
            product=product_two,
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        pp_multi_one.value_multi_select.add(multi_used)
        pp_multi_two.value_multi_select.add(multi_used)

        qs = PropertySelectValue.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).with_usage_count(
            multi_tenant_company_id=self.multi_tenant_company.id,
        )
        usage_by_id = {value.id: value.usage_count for value in qs}

        self.assertEqual(usage_by_id[select_used.id], 2)
        self.assertEqual(usage_by_id[select_unused.id], 0)
        self.assertEqual(usage_by_id[multi_used.id], 2)
        self.assertEqual(usage_by_id[multi_unused.id], 0)

    def test_merge_updates_product_property_value_select(self):
        prop_select = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        source1 = PropertySelectValue.objects.create(
            property=prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )
        source2 = PropertySelectValue.objects.create(
            property=prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )
        target = PropertySelectValue.objects.create(
            property=prop_select,
            multi_tenant_company=self.multi_tenant_company,
        )

        product = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=product,
            property=prop_select,
            value_select=source1,
            multi_tenant_company=self.multi_tenant_company,
        )

        PropertySelectValue.objects.filter(id__in=[source1.id, source2.id]).merge(target)

        product_property.refresh_from_db()
        self.assertEqual(product_property.value_select_id, target.id)
        self.assertFalse(PropertySelectValue.objects.filter(id__in=[source1.id, source2.id]).exists())

    def test_merge_updates_product_property_value_multi_select(self):
        prop_multi = Property.objects.create(
            type=Property.TYPES.MULTISELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        source1 = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        source2 = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        target = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )

        product = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=product,
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property.value_multi_select.add(source1, source2)

        PropertySelectValue.objects.filter(id__in=[source1.id, source2.id]).merge(target)

        product_property.refresh_from_db()
        self.assertSetEqual(
            set(product_property.value_multi_select.values_list("id", flat=True)),
            {target.id},
        )
        self.assertFalse(PropertySelectValue.objects.filter(id__in=[source1.id, source2.id]).exists())

    def test_merge_multi_select_when_target_already_assigned(self):
        prop_multi = Property.objects.create(
            type=Property.TYPES.MULTISELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        source = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        target = PropertySelectValue.objects.create(
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )

        product = Product.objects.create(
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=product,
            property=prop_multi,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property.value_multi_select.add(source, target)

        PropertySelectValue.objects.filter(id=source.id).merge(target)

        product_property.refresh_from_db()
        self.assertSetEqual(
            set(product_property.value_multi_select.values_list("id", flat=True)),
            {target.id},
        )
        self.assertFalse(PropertySelectValue.objects.filter(id=source.id).exists())

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
    MASSIVE_PROPERTY_COUNT = 5
    MASSIVE_VALUES_PER_PROPERTY = 2000
    MASSIVE_LANGUAGE_COUNT = 10
    TRANSLATION_INSERT_THRESHOLD = 5000
    TRANSLATION_BULK_BATCH_SIZE = 1000
    VALUE_BULK_BATCH_SIZE = 2000

    def _get_language_codes(self, *, languages_count):
        available_codes = [code for code, _ in settings.LANGUAGES]
        default_language = self.multi_tenant_company.language

        if default_language not in available_codes:
            available_codes.insert(0, default_language)

        language_codes = []
        for code in available_codes:
            if code not in language_codes:
                language_codes.append(code)
            if len(language_codes) == languages_count:
                break

        return language_codes

    def _create_massive_select_value_dataset(self, *, property_count=None, values_per_property=None, languages_count=None):
        property_count = property_count or self.MASSIVE_PROPERTY_COUNT
        values_per_property = values_per_property or self.MASSIVE_VALUES_PER_PROPERTY
        languages_count = languages_count or self.MASSIVE_LANGUAGE_COUNT

        language_codes = self._get_language_codes(languages_count=languages_count)
        if not language_codes:
            raise AssertionError("No language codes available to create translations.")

        dataset = {
            'single_word_value_id': None,
            'multi_word_value_id': None,
            'language_codes': language_codes,
            'property_count': property_count,
            'values_per_property': values_per_property,
        }

        for property_index in range(property_count):
            property_instance = Property.objects.create(
                type=Property.TYPES.SELECT,
                multi_tenant_company=self.multi_tenant_company,
            )
            PropertyTranslation.objects.bulk_create([
                PropertyTranslation(
                    property=property_instance,
                    language=language_code,
                    name=f"Property {property_index} {language_code}",
                    multi_tenant_company=self.multi_tenant_company,
                )
                for language_code in language_codes
            ])

            select_values = [
                PropertySelectValue(
                    property=property_instance,
                    multi_tenant_company=self.multi_tenant_company,
                )
                for _ in range(values_per_property)
            ]
            PropertySelectValue.objects.bulk_create(select_values, batch_size=self.VALUE_BULK_BATCH_SIZE)

            value_ids = list(
                PropertySelectValue.objects.filter(property=property_instance)
                .order_by('id')
                .values_list('id', flat=True)
            )

            if property_index == 0 and value_ids:
                dataset['single_word_value_id'] = value_ids[0]
            if property_index == 1 and value_ids:
                dataset['multi_word_value_id'] = value_ids[0]

            translations_buffer = []
            for value_index, value_id in enumerate(value_ids):
                base_translation = f"prop-{property_index}-value-{value_index}"
                for language_code in language_codes:
                    translation_value = f"{base_translation}-{language_code}"
                    if (
                        dataset['single_word_value_id'] == value_id
                        and language_code == self.multi_tenant_company.language
                    ):
                        translation_value = "red"
                    elif (
                        dataset['multi_word_value_id'] == value_id
                        and language_code == self.multi_tenant_company.language
                    ):
                        translation_value = "red pants with a blue pocket"

                    translations_buffer.append(
                        PropertySelectValueTranslation(
                            propertyselectvalue_id=value_id,
                            language=language_code,
                            value=translation_value,
                            multi_tenant_company=self.multi_tenant_company,
                        )
                    )

                if len(translations_buffer) >= self.TRANSLATION_INSERT_THRESHOLD:
                    PropertySelectValueTranslation.objects.bulk_create(
                        translations_buffer,
                        batch_size=self.TRANSLATION_BULK_BATCH_SIZE,
                    )
                    translations_buffer.clear()

            if translations_buffer:
                PropertySelectValueTranslation.objects.bulk_create(
                    translations_buffer,
                    batch_size=self.TRANSLATION_BULK_BATCH_SIZE,
                )

        dataset['total_values'] = property_count * values_per_property
        dataset['total_translations'] = dataset['total_values'] * len(language_codes)

        return dataset

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

    def test_new_search_matches_old_implementation(self):
        dataset = self._create_massive_select_value_dataset(
            property_count=1,
            values_per_property=10,
            languages_count=2,
        )
        qs = PropertySelectValue.objects.filter(property__multi_tenant_company=self.multi_tenant_company)
        search_term = "red pants"

        new_queryset, _ = qs.get_search_results(
            search_term=search_term,
            search_fields=PropertySelectValue._meta.search_terms,
            multi_tenant_company=self.multi_tenant_company,
        )
        old_queryset, _ = qs.get_search_results_old(
            search_term=search_term,
            search_fields=PropertySelectValue._meta.search_terms,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertCountEqual(
            list(new_queryset.values_list('pk', flat=True)),
            list(old_queryset.values_list('pk', flat=True)),
        )

    def _assert_search_execution(self, *, queryset, search_term, expected_id, label):
        start = perf_counter()
        exists = queryset.search(
            search_term=search_term,
            multi_tenant_company=self.multi_tenant_company,
        ).filter(id=expected_id).exists()
        elapsed = perf_counter() - start
        self.assertTrue(exists, f"Expected value id {expected_id} to be found for {label} search.")

    def test_massive_dataset_single_word_search(self):
        dataset = self._create_massive_select_value_dataset()
        qs = PropertySelectValue.objects.filter(property__multi_tenant_company=self.multi_tenant_company)
        with self.assertNumQueries(1):
            self._assert_search_execution(
                queryset=qs,
                search_term="red",
                expected_id=dataset['single_word_value_id'],
                label="single-word",
            )

        self.assertIsNotNone(dataset['single_word_value_id'])

        total_values = qs.count()
        translations_qs = PropertySelectValueTranslation.objects.filter(
            propertyselectvalue__property__multi_tenant_company=self.multi_tenant_company
        )
        total_translations = translations_qs.count()

        self.assertGreaterEqual(total_values, dataset['total_values'])
        self.assertGreaterEqual(total_translations, dataset['total_translations'])

    def test_massive_dataset_multi_word_search(self):
        dataset = self._create_massive_select_value_dataset()
        qs = PropertySelectValue.objects.filter(property__multi_tenant_company=self.multi_tenant_company)
        search_term = "red pants with a blue pocket"
        with self.assertNumQueries(1):
            self._assert_search_execution(
                queryset=qs,
                search_term=search_term,
                expected_id=dataset['multi_word_value_id'],
                label="multi-word",
            )

        self.assertIsNotNone(dataset['multi_word_value_id'])

        # Ensures we are testing against a high volume of data similar to production.
        values_per_company = qs.count()
        translations_qs = PropertySelectValueTranslation.objects.filter(
            propertyselectvalue__property__multi_tenant_company=self.multi_tenant_company
        )
        translations_per_company = translations_qs.count()

        self.assertGreaterEqual(values_per_company, dataset['total_values'])
        self.assertGreaterEqual(translations_per_company, dataset['total_translations'])
