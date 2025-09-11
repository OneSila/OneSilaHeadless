from django.test import SimpleTestCase
from django.utils.translation import gettext as _, override

from sales_channels.integrations.woocommerce.factories.mixins import (
    WoocommerceRemoteValueConversionMixin,
)


class BooleanConversionTest(SimpleTestCase):
    def test_boolean_values_are_translated_strings(self):
        mixin = WoocommerceRemoteValueConversionMixin()
        with override('en'):
            self.assertEqual(mixin.get_boolean_value(True), _("Yes"))
            self.assertEqual(mixin.get_boolean_value(False), _("No"))
