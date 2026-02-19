from datetime import date, datetime
from types import SimpleNamespace

from django.test import SimpleTestCase

from properties.models import Property
from sales_channels.factories.value_mixins import RemoteValueMixin


class _MultiSelectManager:
    def __init__(self, values):
        self._values = values

    def all(self):
        return list(self._values)


class _ProductPropertyStub:
    def __init__(self, *, property_type, value=None, value_select=None, value_multi_select=None):
        self.property = SimpleNamespace(type=property_type)
        self._value = value
        self.value_select = value_select
        self.value_multi_select = _MultiSelectManager(value_multi_select or [])

    def get_value(self, language=None):
        _ = language
        return self._value


class _MixinStub(RemoteValueMixin):
    def __init__(self, *, product_property):
        self.local_instance = product_property
        self.local_property = product_property.property


class _RoutingMixinStub(_MixinStub):
    def __init__(self, *, product_property):
        super().__init__(product_property=product_property)
        self.calls = []

    def get_select_value(self, *, product_property=None, remote_property=None, language_code=None):
        _ = product_property
        _ = remote_property
        _ = language_code
        self.calls.append("select")
        return "single"

    def get_select_value_multiple(self, *, product_property=None, remote_property=None, language_code=None):
        _ = product_property
        _ = remote_property
        _ = language_code
        self.calls.append("multi")
        return ["multi"]


class RemoteValueMixinTest(SimpleTestCase):
    def test_select_and_multiselect_routing_uses_distinct_methods(self):
        select_prop = _ProductPropertyStub(
            property_type=Property.TYPES.SELECT,
            value_select=SimpleNamespace(value="red"),
        )
        mixin = _RoutingMixinStub(product_property=select_prop)
        self.assertEqual(mixin.get_remote_value(), "single")
        self.assertEqual(mixin.calls, ["select"])

        multi_prop = _ProductPropertyStub(
            property_type=Property.TYPES.MULTISELECT,
            value_multi_select=[SimpleNamespace(value="red"), SimpleNamespace(value="blue")],
        )
        mixin = _RoutingMixinStub(product_property=multi_prop)
        self.assertEqual(mixin.get_remote_value(), ["multi"])
        self.assertEqual(mixin.calls, ["multi"])

    def test_default_select_value_extractors(self):
        select_prop = _ProductPropertyStub(
            property_type=Property.TYPES.SELECT,
            value_select=SimpleNamespace(value="red"),
        )
        mixin = _MixinStub(product_property=select_prop)
        self.assertEqual(mixin.get_remote_value(), "red")

        multi_prop = _ProductPropertyStub(
            property_type=Property.TYPES.MULTISELECT,
            value_multi_select=[SimpleNamespace(value="red"), SimpleNamespace(value="blue")],
        )
        mixin = _MixinStub(product_property=multi_prop)
        self.assertEqual(mixin.get_remote_value(), ["red", "blue"])

    def test_default_boolean_and_date_time_conversions(self):
        true_prop = _ProductPropertyStub(
            property_type=Property.TYPES.BOOLEAN,
            value="1",
        )
        mixin = _MixinStub(product_property=true_prop)
        self.assertTrue(mixin.get_remote_value())

        false_prop = _ProductPropertyStub(
            property_type=Property.TYPES.BOOLEAN,
            value="false",
        )
        mixin = _MixinStub(product_property=false_prop)
        self.assertFalse(mixin.get_remote_value())

        date_prop = _ProductPropertyStub(
            property_type=Property.TYPES.DATE,
            value=date(2026, 2, 11),
        )
        mixin = _MixinStub(product_property=date_prop)
        self.assertEqual(mixin.get_remote_value(), "2026-02-11")

        datetime_prop = _ProductPropertyStub(
            property_type=Property.TYPES.DATETIME,
            value=datetime(2026, 2, 11, 13, 45, 30),
        )
        mixin = _MixinStub(product_property=datetime_prop)
        self.assertEqual(mixin.get_remote_value(), "2026-02-11T13:45:30")

    def test_get_remote_value_uses_explicit_product_property_argument(self):
        base_prop = _ProductPropertyStub(
            property_type=Property.TYPES.INT,
            value=1,
        )
        override_prop = _ProductPropertyStub(
            property_type=Property.TYPES.INT,
            value=99,
        )
        mixin = _MixinStub(product_property=base_prop)

        self.assertEqual(
            mixin.get_remote_value(product_property=override_prop),
            99,
        )
