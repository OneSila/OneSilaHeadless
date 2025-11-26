from core.tests import TestCase
from imports_exports.factories.properties import ImportPropertyInstance, ImportPropertySelectValueInstance, \
    ImportProductPropertiesRuleInstance, ImportProductPropertiesRuleItemInstance, ImportProductPropertyInstance
from imports_exports.models import Import
from products.models import Product
from properties.models import Property, PropertyTranslation, PropertySelectValueTranslation, PropertySelectValue, \
    ProductPropertiesRule, ProductPropertiesRuleItem, ProductPropertyTextTranslation


# Dummy concrete subclass to enable testing of ImportPropertyInstance without using AI queries
class DummyImportPropertyInstance(ImportPropertyInstance):
    def detect_type(self):
        self.type = "TEXT"


class ImportInstanceValidateDataTest(TestCase):
    def test_fully_specified_data(self):
        data = {
            "name": "Color",
            "internal_name": "color",
            "type": "TEXT",
            "is_public_information": True,
            "add_to_filters": True,
            "has_image": False
        }
        # Should not raise; instance is created successfully.
        instance = DummyImportPropertyInstance(data)
        self.assertEqual(getattr(instance, 'name', None), "Color")
        self.assertEqual(getattr(instance, 'internal_name', None), "color")
        self.assertEqual(getattr(instance, 'type', None), "TEXT")
        self.assertTrue(getattr(instance, 'is_public_information', None))
        self.assertTrue(getattr(instance, 'add_to_filters', None))
        self.assertFalse(getattr(instance, 'has_image', None))

    def test_minimal_data_with_name(self):
        data = {
            "name": "Size"
            # internal_name not provided; type also missing.
        }
        instance = DummyImportPropertyInstance(data)
        self.assertEqual(getattr(instance, 'name', None), "Size")
        self.assertEqual(getattr(instance, 'type', None), "TEXT")

    def test_minimal_data_with_internal_name(self):
        data = {
            "internal_name": "size"
            # name not provided; type also missing.
        }
        instance = DummyImportPropertyInstance(data)
        self.assertEqual(getattr(instance, 'internal_name', None), "size")
        self.assertEqual(getattr(instance, 'type', None), "TEXT")

    def test_reserved_internal_name_is_sanitized(self):
        data = {
            "internal_name": "product_type"
        }
        instance = DummyImportPropertyInstance(data)
        self.assertEqual(getattr(instance, 'internal_name', None), "product_type_external")

    def test_data_without_type(self):
        data = {
            "internal_name": "weight",
            "is_public_information": False,
            "add_to_filters": False,
            "has_image": False
            # 'type' is intentionally missing.
        }
        instance = DummyImportPropertyInstance(data)

        # detect_type() should provide "TEXT" + override bollean to False
        self.assertEqual(getattr(instance, 'internal_name', None), "weight")
        self.assertEqual(getattr(instance, 'type', None), "TEXT")
        self.assertFalse(getattr(instance, 'is_public_information', None))
        self.assertFalse(getattr(instance, 'add_to_filters', None))
        self.assertFalse(getattr(instance, 'has_image', None))

    def test_missing_name_and_internal_name(self):
        data = {
            "type": "TEXT"
        }

        with self.assertRaises(ValueError) as cm:
            DummyImportPropertyInstance(data)

        self.assertIn("Either 'internal_name' or 'name' must be provided", str(cm.exception))

    def test_invalid_boolean_field(self):
        data = {
            "internal_name": "color",
            "type": "TEXT",
            "is_public_information": "yes",  # invalid; should be boolean
            "add_to_filters": True,
            "has_image": False
        }

        with self.assertRaises(ValueError) as cm:
            DummyImportPropertyInstance(data)

        self.assertIn("Field 'is_public_information' must be a boolean value", str(cm.exception))


class ImportPropertyProcessTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_process_with_internal_name(self):

        properties_cnt = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        data = {
            "name": "aaa",
            "internal_name": "aaa",
            "type": "SELECT",
            "is_public_information": True,
            "add_to_filters": True,
            "has_image": False
        }
        instance = ImportPropertyInstance(data, self.import_process)
        instance.process()

        properties_post_import_cnt = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        self.assertEqual(properties_cnt + 1, properties_post_import_cnt)

    def test_process_with_name(self):

        properties_cnt = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        data = {
            "name": "bbb",
            "type": "SELECT",
            "is_public_information": True,
            "add_to_filters": True,
            "has_image": False
        }
        instance = ImportPropertyInstance(data, self.import_process)
        instance.process()

        properties_post_import_cnt = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        self.assertEqual(properties_cnt + 1, properties_post_import_cnt)

    def test_process_sanitizes_reserved_internal_name(self):

        data = {
            "name": "Woo Product Type",
            "internal_name": "product_type",
            "type": "SELECT",
            "is_public_information": True,
            "add_to_filters": True,
            "has_image": False
        }

        instance = ImportPropertyInstance(data, self.import_process)
        instance.process()

        created_internal_name = instance.instance.internal_name
        self.assertEqual(created_internal_name, "product_type_external")

    def test_edit_is_public_information_internal_name(self):
        data = {
            "name": "Warranty",
            "internal_name": "warranty_period",
            "type": "INT",
            "is_public_information": False,
            "add_to_filters": True,
            "has_image": False
        }

        existent_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name=data.get("internal_name"),
            type=data.get("type"),
        )

        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=existent_property,
            name=data.get("name"),
        )
        properties_cnt = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        instance = ImportPropertyInstance(data, self.import_process)
        instance.process()

        properties_post_import_cnt = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        self.assertEqual(properties_cnt, properties_post_import_cnt)

        existent_property.refresh_from_db()
        self.assertFalse(existent_property.is_public_information)

    def test_edit_is_public_information_with_translation(self):
        data = {
            "name": "Model",
            "type": "SELECT",
            "is_public_information": False,
            "add_to_filters": True,
            "has_image": False
        }

        existent_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=data.get("type"),
        )

        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=existent_property,
            name=data.get("name"),
        )
        properties_cnt = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        instance = ImportPropertyInstance(data, self.import_process)
        instance.process()

        properties_post_import_cnt = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        self.assertEqual(properties_cnt, properties_post_import_cnt)

        existent_property.refresh_from_db()
        self.assertFalse(existent_property.is_public_information)


class ImportPropertySelectValueInstanceValidateTest(TestCase):
    def setUp(self):
        super().setUp()
        # Create an Import instance for testing.
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_validate_with_external_property(self):
        # Test with a provided property.
        data = {
            "value": "Red",
            # property_data not needed because we supply property externally.
        }

        # Create a dummy property.
        dummy_prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="color",
            type="SELECT"
        )
        # Create a translation so that property.name is available.
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=dummy_prop,
            name="Color"
        )

        instance = ImportPropertySelectValueInstance(data, self.import_process, property=dummy_prop)
        self.assertEqual(getattr(instance, 'value', None), "Red")

    def test_validate_with_property_data(self):
        # Test with property_data provided (no external property).
        data = {
            "value": "Blue",
            "property_data": {
                "name": "Color",
                "internal_name": "color",
                "type": "SELECT",
            }
        }
        instance = ImportPropertySelectValueInstance(data, self.import_process)
        # Should validate without error.
        self.assertEqual(getattr(instance, 'value', None), "Blue")
        # And property_data exists.
        self.assertIsNotNone(getattr(instance, 'property_data', None))

    def test_validate_missing_property_and_property_data(self):
        # Test missing both external property and property_data.
        data = {
            "value": "Green"
        }
        with self.assertRaises(ValueError) as cm:
            ImportPropertySelectValueInstance(data, self.import_process)

        self.assertIn("Either a 'property' or 'property_data' must be provided", str(cm.exception))

    def test_validate_missing_value(self):
        # Test missing the required 'value' key.
        data = {
            "property_data": {
                "name": "Color",
                "internal_name": "color",
                "type": "SELECT"
            }
        }
        with self.assertRaises(ValueError) as cm:
            ImportPropertySelectValueInstance(data, self.import_process)

        self.assertIn("The 'value' field is required", str(cm.exception))

    def test_validate_incomplete_property_data(self):
        # Test with property_data that is incomplete (missing both 'name' and 'internal_name').
        data = {
            "value": "Yellow",
            "property_data": {
                "type": "SELECT"
            }
        }
        with self.assertRaises(ValueError) as cm:
            instance = ImportPropertySelectValueInstance(data, self.import_process)

        # Expect an error related to property data incompleteness.
        self.assertIn("Either 'internal_name' or 'name' must be provided", str(cm.exception))


class ImportPropertySelectValueInstanceProcessTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        # Create an existing Property with translation.
        self.existing_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="color",
            type="SELECT"
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.existing_property,
            name="Color"
        )
        # Create an existing PropertySelectValue with translation.
        self.existing_select_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.existing_property
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.existing_select_value,
            multi_tenant_company=self.multi_tenant_company,
            value="Red"
        )

    def test_process_no_change(self):
        """
        Provide data that matches the existing select value ("Red") exactly.
        Expect that the factory finds the existing select value and no update occurs.
        """
        data = {
            "value": "Red",
            "property_data": {
                "name": "Color",
                "internal_name": "color",
                "type": "SELECT",
            }
        }
        # Provide the existing property externally.
        instance = ImportPropertySelectValueInstance(data, self.import_process, property=self.existing_property)
        instance.process()
        self.assertEqual(instance.instance.pk, self.existing_select_value.pk)

    def test_process_update_existing(self):
        """
        Provide data with a different value ("Blue") using an existing property.
        Expect that the select value is updated accordingly.
        """
        data = {
            "value": "Blue",
            "property_data": {
                "name": "Color",
                "internal_name": "color",
                "type": "SELECT",
            }
        }
        instance = ImportPropertySelectValueInstance(data, self.import_process, property=self.existing_property)
        instance.process()
        self.existing_select_value.refresh_from_db()
        self.assertEqual(instance.instance.value, "Blue")
        self.assertEqual(instance.translation.value, "Blue")

    def test_process_update_existing_with_data(self):
        """
        Provide data with a different value ("Blue") using an existing property.
        Expect that the select value is updated accordingly.
        """
        data = {
            "value": "Green",
            "property_data": {
                "name": "Color",
                "type": "SELECT",
            }
        }
        instance = ImportPropertySelectValueInstance(data, self.import_process)
        instance.process()
        self.existing_select_value.refresh_from_db()
        self.assertEqual(instance.instance.value, "Green")
        self.assertEqual(instance.translation.value, "Green")

    def test_process_using_property_data(self):
        """
        Provide data without an external property; property_data is used to import the Property.
        Expect that a new Property is imported and a new PropertySelectValue is created.
        """
        data = {
            "value": "Metal",
            "property_data": {
                "name": "Material",
                "internal_name": "material",
                "type": "SELECT",
            }
        }
        instance = ImportPropertySelectValueInstance(data, self.import_process)
        instance.process()
        self.assertIsNotNone(instance.property)
        self.assertIsNotNone(instance.instance)
        self.assertEqual(instance.instance.value, "Metal")


class ImportProductPropertiesRuleInstanceValidateTest(TestCase):
    def setUp(self):
        super().setUp()
        # Create a dummy Import instance.
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_validate_with_value(self):
        """
        Test that valid data (providing a 'value' and a product type) passes validation.
        In this case, we supply the product_type externally.
        """
        data = {
            "value": "Chair"
        }

        instance = ImportProductPropertiesRuleInstance(data, self.import_process)
        self.assertEqual(getattr(instance, 'value', None), "Chair")

    def test_validate_missing_value(self):
        """
        Test that if the 'value' key is missing, a ValueError is raised.
        """
        data = {
            "wrong_key": "something"
        }
        with self.assertRaises(ValueError) as cm:
            ImportProductPropertiesRuleInstance(data, self.import_process)

        self.assertIn("The 'value' field is required", str(cm.exception))

    def test_validate_invalid_items(self):
        # Test with property_data that is incomplete (missing both 'name' and 'internal_name').
        data = {
            "value": "Table",
            "items": [
                {
                    "bad_data": "wrong"
                }
            ]
        }
        with self.assertRaises(ValueError) as cm:
            instance = ImportPropertySelectValueInstance(data, self.import_process)
            instance.process()

        self.assertTrue(type(cm.exception) == ValueError)


class ImportProductPropertiesRuleInstanceProcessTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True
        )

        self.product_type = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property
        )

        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.product_type,
            multi_tenant_company=self.multi_tenant_company,
            value="Chair"
        )

    def test_process_existing_product_type(self):
        """
        Provide data that matches the existing product type select value ("Chair").
        Expect that the factory finds the existing select value and the rule is created using it.
        """
        rules_cnt = ProductPropertiesRule.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        data = {
            "value": "Chair",
        }

        instance = ImportProductPropertiesRuleInstance(data, self.import_process)
        instance.process()

        post_process_rules_cnt = ProductPropertiesRule.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        rule = instance.instance
        self.assertIsNotNone(rule)
        self.assertEqual(rule.product_type.pk, self.product_type.pk)
        self.assertEqual(rules_cnt, post_process_rules_cnt)

    def test_process_no_existing_product_type(self):
        """
        Provide data for a product type ("Table") where no existing select value exists.
        Expect that a new PropertySelectValue is created and used for the rule.
        """
        data = {
            "value": "Table",
        }
        rules_cnt = ProductPropertiesRule.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        instance = ImportProductPropertiesRuleInstance(data, self.import_process)
        instance.process()

        post_process_rules_cnt = ProductPropertiesRule.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        rule = instance.instance
        self.assertIsNotNone(rule)
        self.assertEqual(rule.product_type.value, "Table")
        self.assertEqual(rules_cnt + 1, post_process_rules_cnt)

    def test_adding_items(self):
        """
        Provide data for a product type ("Table") where no existing select value exists.
        Expect that a new PropertySelectValue is created and used for the rule.
        """
        data = {
            "value": "Table",
            "items": [
                {
                    "sort_order": 1,
                    "property_data": {"name": "Color", "type": "SELECT"}
                },
                {
                    "type": "REQUIRED",
                    "property_data": {"name": "Material", "type": "SELECT"}
                }
            ]
        }

        rules_cnt = ProductPropertiesRule.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        instance = ImportProductPropertiesRuleInstance(data, self.import_process)
        instance.process()

        post_process_rules_cnt = ProductPropertiesRule.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        items_cnt = ProductPropertiesRuleItem.objects.filter(multi_tenant_company=self.multi_tenant_company, rule=instance.instance).count()

        rule = instance.instance
        self.assertIsNotNone(rule)
        self.assertEqual(rule.product_type.value, "Table")
        self.assertEqual(rules_cnt + 1, post_process_rules_cnt)
        self.assertEqual(items_cnt, 2)

    def test_process_with_require_ean_code(self):
        """
        Provide data with require_ean_code True.
        Expect that the rule is created with require_ean_code set to True.
        """
        data = {
            "value": "Chair",
            "require_ean_code": True,
        }
        instance = ImportProductPropertiesRuleInstance(data, self.import_process,
                                                       product_type=self.product_type)
        instance.process()

        rule = instance.instance
        self.assertIsNotNone(rule)
        self.assertTrue(rule.require_ean_code)


class ImportProductPropertiesRuleItemInstanceValidateTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        # Create a dummy property for testing
        self.existing_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="sample_prop",
            type="SELECT"
        )

        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True
        )

        self.product_type = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property
        )

        self.existing_rule = ProductPropertiesRule.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type
        )

    def test_validate_with_external_rule_and_property(self):
        data = {
            "rule_data": {"dummy": "data"},   # dummy data; actual content not important for validation
            "property_data": {"name": "Material", "type": "SELECT"}
        }

        # Providing external property (and rule) should validate.
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process, rule=self.existing_rule, property=self.existing_property)
        self.assertEqual(instance.type, "OPTIONAL")

    def test_validate_with_rule_data_and_property_data(self):
        data = {
            "sort_order": 2,
            "rule_data": {"value": "Chair"},
            "property_data": {"name": "Color", "type": "SELECT"}
        }
        # Not providing external rule/property should still validate because rule_data and property_data exist.
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process)
        self.assertEqual(instance.type, "OPTIONAL")

    def test_validate_missing_property(self):
        data = {
            "type": "REQUIRED",
            "rule_data": {"value": "Chair"}
            # Missing both external property and property_data.
        }
        with self.assertRaises(ValueError) as cm:
            ImportProductPropertiesRuleItemInstance(data, self.import_process)

        self.assertIn("Either a 'property' or 'property_data' must be provided", str(cm.exception))

    def test_validate_missing_rule(self):
        data = {
            "type": "OPTIONAL",
            "sort_order": 2,
            "property_data": {"name": "Material", "type": "SELECT"}
            # Missing both external rule and rule_data.
        }
        with self.assertRaises(ValueError) as cm:
            ImportProductPropertiesRuleItemInstance(data, self.import_process)

        self.assertIn("Either a 'rule' or 'rule_data' must be provided", str(cm.exception))

    def test_validate_invalid_type(self):
        data = {
            "type": "INVALID_TYPE",
            "sort_order": 2,
            "rule_data": {"dummy": "data"},
            "property_data": {"name": "Material", "type": "SELECT"}
        }

        with self.assertRaises(ValueError) as cm:
            ImportProductPropertiesRuleItemInstance(data, self.import_process)

        self.assertTrue(type(cm.exception) == ValueError)


class ImportProductPropertiesRuleItemInstanceProcessTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        # Create a dummy property for testing
        self.existing_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="sample_prop",
            type="SELECT"
        )

        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True
        )

        self.product_type = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property
        )

        translation = PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type,
            value="Table",
        )

        self.existing_rule = ProductPropertiesRule.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type
        )

    def test_process_create_using_data(self):
        """
        Provide data that matches the existing product type select value ("Chair").
        Expect that the factory finds the existing select value and the rule is created using it.
        """
        initial_rule_cnt = ProductPropertiesRule.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        data = {
            "rule_data": {"value": "Chair"},
            "property_data": {"name": "Material", "type": "SELECT"}
        }
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process)
        instance.process()

        rule = instance.rule
        final_rule_cnt = ProductPropertiesRule.objects.filter(multi_tenant_company=self.multi_tenant_company).count()
        self.assertIsNotNone(rule)

        self.assertEqual(initial_rule_cnt + 1, final_rule_cnt)
        self.assertEqual(ProductPropertiesRuleItem.objects.filter(rule=rule).count(), 1)

    def test_process_create_using_existing_rule(self):
        """
        Provide data that matches the existing product type select value ("Chair").
        Expect that the factory finds the existing select value and the rule is created using it.
        """
        data = {
            "property_data": {"name": "Material", "type": "SELECT"}
        }
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process, rule=self.existing_rule)
        instance.process()

        rule = instance.rule
        self.assertIsNotNone(rule.id, self.existing_rule.id)
        self.assertEqual(ProductPropertiesRuleItem.objects.filter(rule=rule).count(), 1)

    def test_reserved_internal_name_in_property_data_is_sanitized(self):
        data = {
            "property_data": {
                "internal_name": "product_type",
                "name": "Woo Product Type",
                "type": "SELECT"
            }
        }

        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process, rule=self.existing_rule)
        instance.process()

        self.assertEqual(instance.property.internal_name, "product_type_external")

    def test_reserved_internal_name_property_data_reuses_property(self):
        data = {
            "property_data": {
                "internal_name": "product_type",
                "name": "Woo Product Type",
                "type": "SELECT"
            }
        }

        base_count = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        first_instance = ImportProductPropertiesRuleItemInstance(data, self.import_process, rule=self.existing_rule)
        first_instance.process()

        mid_count = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        second_instance = ImportProductPropertiesRuleItemInstance({
            "property_data": {
                "internal_name": "product_type",
                "name": "Woo Product Type",
                "type": "SELECT"
            }
        }, self.import_process, rule=self.existing_rule)
        second_instance.process()

        final_count = Property.objects.filter(multi_tenant_company=self.multi_tenant_company).count()

        self.assertEqual(mid_count, final_count)
        self.assertEqual(first_instance.property, second_instance.property)

    def test_process_create_using_existing_property(self):
        """
        Provide data that matches the existing product type select value ("Chair").
        Expect that the factory finds the existing select value and the rule is created using it.
        """
        new_property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type="SELECT",
        )

        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=new_property,
            name="Brand"
        )

        data = {
            "rule_data": {"value": "Chair"},
        }
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process, property=new_property)
        instance.process()

        rule = instance.rule
        self.assertIsNotNone(rule.id, self.existing_rule.id)
        self.assertEqual(ProductPropertiesRuleItem.objects.filter(rule=rule).count(), 1)

    def test_edit_rule_item_using_existing_property_and_rule(self):
        """
        Create an initial rule item, then update its sort_order using rule_data.
        """
        # Create an initial rule item.
        initial_rule_item = ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.existing_rule,
            property=self.existing_property,
            type="OPTIONAL",
            sort_order=1
        )
        initial_item_cnt = ProductPropertiesRuleItem.objects.filter(rule=self.existing_rule).count()

        data = {
            "sort_order": 5,
        }
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process,
                                                           rule=self.existing_rule,
                                                           property=self.existing_property)
        instance.process()
        updated_item = instance.instance
        self.assertEqual(updated_item.sort_order, 5)
        self.assertEqual(initial_item_cnt, ProductPropertiesRuleItem.objects.filter(rule=self.existing_rule).count())

    def test_edit_rule_item_using_existing_property(self):
        """
        Create an initial rule item, then update its sort_order using rule_data.
        """
        # Create an initial rule item.
        initial_rule_item = ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.existing_rule,
            property=self.existing_property,
            type="OPTIONAL",
            sort_order=1
        )
        initial_item_cnt = ProductPropertiesRuleItem.objects.filter(rule=self.existing_rule).count()

        data = {
            "type": "REQUIRED",
            "rule_data": {"value": "Table"},
        }
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process, property=self.existing_property)
        instance.process()

        updated_item = instance.instance
        self.assertEqual(updated_item.type, "REQUIRED")
        self.assertEqual(updated_item.id, initial_rule_item.id)
        self.assertEqual(instance.rule.id, self.existing_rule.id)
        self.assertEqual(initial_item_cnt, ProductPropertiesRuleItem.objects.filter(rule=self.existing_rule).count())

    def test_edit_rule_item_using_existing_rule(self):
        """
        Create an initial rule item, then update its sort_order using rule_data.
        """
        # Create an initial rule item.
        initial_rule_item = ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.existing_rule,
            property=self.existing_property,
            type="OPTIONAL",
            sort_order=1
        )
        initial_item_cnt = ProductPropertiesRuleItem.objects.filter(rule=self.existing_rule).count()

        data = {
            "type": "REQUIRED",
            "property_data": {"internal_name": "sample_prop", "type": "SELECT"},
        }
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process, rule=self.existing_rule)
        instance.process()

        updated_item = instance.instance
        self.assertEqual(updated_item.type, "REQUIRED")
        self.assertEqual(updated_item.id, initial_rule_item.id)
        self.assertEqual(instance.rule.id, self.existing_rule.id)
        self.assertEqual(initial_item_cnt, ProductPropertiesRuleItem.objects.filter(rule=self.existing_rule).count())

    def test_create_new_rule_item_for_existing_rule(self):
        """
        Create an initial rule item, then update its sort_order using rule_data.
        """
        # Create an initial rule item.
        initial_rule_item = ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.existing_rule,
            property=self.existing_property,
            type="OPTIONAL",
            sort_order=1
        )
        initial_item_cnt = ProductPropertiesRuleItem.objects.filter(rule=self.existing_rule).count()

        data = {
            "rule_data": {"value": "Table"},
            "property_data": {"internal_name": "sample_prop_2", "type": "SELECT"},
        }
        instance = ImportProductPropertiesRuleItemInstance(data, self.import_process)
        instance.process()

        updated_item = instance.instance
        self.assertNotEquals(updated_item.id, initial_rule_item.id)
        self.assertEqual(instance.rule.id, self.existing_rule.id)
        self.assertEqual(initial_item_cnt + 1, ProductPropertiesRuleItem.objects.filter(rule=self.existing_rule).count())


class ImportProductPropertyInstanceProcessTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        self.product = Product.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sku="PROP001",
            type=Product.SIMPLE
        )

    def _create_property(self, name, prop_type):
        property = Property.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            type=prop_type
        )

        translation = PropertyTranslation.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            property=property,
        )

        return property

    def _process_instance(self, prop, value):
        data = {
            "value": value,
            "property_data": {"name": prop.name},
        }

        instance = ImportProductPropertyInstance(data, self.import_process, property=prop, product=self.product)
        instance.multi_tenant_company = self.import_process.multi_tenant_company
        instance.process()

        return instance

    def test_select_property(self):
        prop = self._create_property("Material", Property.TYPES.SELECT)
        select_value = PropertySelectValue.objects.create(property=prop, multi_tenant_company=prop.multi_tenant_company)
        translation = PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            propertyselectvalue=select_value,
            value="Red"
        )

        instance = self._process_instance(prop, "Red")
        self.assertEqual(instance.instance.value_select.value, "Red")

    def test_multiselect_property(self):
        prop = self._create_property("Size", Property.TYPES.MULTISELECT)

        select_s = PropertySelectValue.objects.create(property=prop, multi_tenant_company=prop.multi_tenant_company)
        select_m = PropertySelectValue.objects.create(property=prop, multi_tenant_company=prop.multi_tenant_company)
        select_l = PropertySelectValue.objects.create(property=prop, multi_tenant_company=prop.multi_tenant_company)

        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            propertyselectvalue=select_s,
            value="S"
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            propertyselectvalue=select_m,
            value="M"
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            propertyselectvalue=select_l,
            value="L"
        )

        instance = self._process_instance(prop, "S, M")
        values = list(instance.instance.value_multi_select.values_list("id", flat=True))

        self.assertIn(select_s.id, values)
        self.assertIn(select_m.id, values)
        self.assertNotIn(select_l.id, values)

    def test_int_property(self):
        prop = self._create_property("Stock", Property.TYPES.INT)
        instance = self._process_instance(prop, "42")
        self.assertEqual(instance.instance.value_int, 42)

    def test_float_property(self):
        prop = self._create_property("Weight", Property.TYPES.FLOAT)
        instance = self._process_instance(prop, "3.14")
        self.assertAlmostEqual(instance.instance.value_float, 3.14)

    def test_boolean_property(self):
        prop = self._create_property("Available", Property.TYPES.BOOLEAN)
        instance = self._process_instance(prop, "true")
        self.assertEqual(instance.instance.value_boolean, True)

    def test_date_property(self):
        prop = self._create_property("Launch Date", Property.TYPES.DATE)
        instance = self._process_instance(prop, "2024-12-01 00:00:00")
        self.assertEqual(str(instance.instance.value_date), "2024-12-01")

    def test_datetime_property(self):
        prop = self._create_property("Sale DateTime", Property.TYPES.DATETIME)
        instance = self._process_instance(prop, "2025-01-01 14:30:00")
        self.assertEqual(str(instance.instance.value_datetime), "2025-01-01 14:30:00")

    def test_text_property(self):
        prop = self._create_property("Note", Property.TYPES.TEXT)
        instance = self._process_instance(prop, "This is a simple note.")
        translation = ProductPropertyTextTranslation.objects.filter(product_property=instance.instance).first()
        self.assertEqual(translation.value_text, "This is a simple note.")

    def test_description_property(self):
        prop = self._create_property("Long Note", Property.TYPES.DESCRIPTION)
        instance = self._process_instance(prop, "Full paragraph of text.")
        translation = ProductPropertyTextTranslation.objects.filter(product_property=instance.instance).first()
        self.assertEqual(translation.value_description, "Full paragraph of text.")
