from core.tests import TestCase
from sales_channels.integrations.woocommerce.helpers import convert_fields_to_int, \
    convert_fields_to_string, raise_for_required_fields


class TestHelpers(TestCase):
    def test_convert_fields_to_int(self):
        fields_convert_to_int = ['attributes__id', 'id']
        data = {'id': '2992', 'attributes': {'id': '29', 'name': 'test'}}
        expected = {'id': 2992, 'attributes': {'id': 29, 'name': 'test'}}

        self.assertEqual(convert_fields_to_int(data, fields_convert_to_int), expected)

    def test_convert_fields_to_string(self):
        fields_convert_to_string = ['attributes__id', 'id']
        data = {'id': 2992, 'attributes': {'id': 29, 'name': 'test'}}
        expected = {'id': '2992', 'attributes': {'id': '29', 'name': 'test'}}

        self.assertEqual(convert_fields_to_string(data, fields_convert_to_string), expected)

    def test_raise_for_required_fields(self):
        required_fields = ['id', 'attributes__id', 'images__src', 'active']
        data = {'name': 'name', 'attributes': {'name': 'test'}, 'active': True}
        expected = ['images__src', 'id', 'attributes__id']

        with self.assertRaises(ValueError):
            fields = raise_for_required_fields(data, required_fields)
            self.assertEqual(set(fields), set(expected))
