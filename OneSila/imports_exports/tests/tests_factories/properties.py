from core.tests import TestCase
from imports_exports.factories.properties import ImportPropertyInstance
from properties.models import Property


# Dummy concrete subclass to enable testing of ImportPropertyInstance
class DummyImportPropertyInstance(ImportPropertyInstance):
    def detect_type(self):
        # Simply return "TEXT" for testing purposes.
        return "TEXT"


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
        self.assertEqual(instance.data["name"], "Color")
        self.assertEqual(instance.data["internal_name"], "color")
        self.assertEqual(instance.data["type"], "TEXT")
        self.assertTrue(instance.data["is_public_information"])
        self.assertTrue(instance.data["add_to_filters"])
        self.assertFalse(instance.data["has_image"])

    def test_minimal_data_with_name(self):
        data = {
            "name": "Size"
            # internal_name not provided; type also missing.
        }
        instance = DummyImportPropertyInstance(data)
        self.assertEqual(instance.data["name"], "Size")
        self.assertEqual(instance.data["type"], "TEXT")
        self.assertTrue(instance.data["is_public_information"])
        self.assertTrue(instance.data["add_to_filters"])
        self.assertFalse(instance.data["has_image"])

    def test_minimal_data_with_internal_name(self):
        data = {
            "internal_name": "size"
            # name not provided; type also missing.
        }
        instance = DummyImportPropertyInstance(data)
        self.assertEqual(instance.data["internal_name"], "size")
        self.assertEqual(instance.data["type"], "TEXT")

    def test_data_without_type(self):
        data = {
            "internal_name": "weight",
            "is_public_information": False,
            "add_to_filters": False,
            "has_image": False
            # 'type' is intentionally missing.
        }
        instance = DummyImportPropertyInstance(data)
        # detect_type() should provide "TEXT"
        self.assertEqual(instance.data["type"], "TEXT")
        self.assertEqual(instance.data["internal_name"], "weight")
        self.assertFalse(instance.data["is_public_information"])
        self.assertFalse(instance.data["add_to_filters"])

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
