from .mixins import TestCaseWoocommerceMixin
from django.utils.translation import gettext as _

from sales_channels.integrations.woocommerce.factories.sales_channels import TryConnection
from sales_channels.integrations.woocommerce.exceptions import FailedToGetError


class TryConnectionTestCase(TestCaseWoocommerceMixin):
    """
    Test case for the TryConnection factory class.
    """

    def test_try_connection_success(self):
        """
        Test that TryConnection successfully connects to WooCommerce API.
        """
        # Try the connection
        connection = TryConnection(sales_channel=self.sales_channel)

        # Basic assertions to verify the connection works
        self.assertIsNotNone(connection)
        self.assertIsNotNone(connection.api)
        self.assertIsNotNone(connection.sales_channel)
        self.assertEqual(connection.sales_channel, self.sales_channel)

    def test_try_connection_initialize_correctly(self):
        """
        Test that TryConnection initializes with the correct sales channel.
        """
        connection = TryConnection(sales_channel=self.sales_channel)

        # Verify connection uses the correct sales channel
        self.assertEqual(connection.sales_channel.hostname, self.sales_channel.hostname)
        self.assertEqual(connection.sales_channel.api_key, self.sales_channel.api_key)
        self.assertEqual(connection.sales_channel.api_secret, self.sales_channel.api_secret)

    def test_get_api_client_method(self):
        """
        Test that the get_api_client method returns a properly configured API wrapper.
        """
        # Create the connection
        connection = TryConnection(sales_channel=self.sales_channel)

        # Basic assertions about the API client
        self.assertIsNotNone(connection.api)
        self.assertEqual(connection.api.hostname, self.sales_channel.hostname)
        self.assertEqual(connection.api.api_key, self.sales_channel.api_key)
        self.assertEqual(connection.api.api_secret, self.sales_channel.api_secret)
        self.assertEqual(connection.api.api_version, self.sales_channel.api_version)
