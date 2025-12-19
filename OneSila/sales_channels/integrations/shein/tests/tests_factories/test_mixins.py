"""Tests covering the Shein mixin helpers."""

from unittest.mock import Mock, patch

import requests
from django.test import override_settings
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import SheinSalesChannel


class _DummyFactory(SheinSignatureMixin):
    def __init__(self, *, sales_channel: SheinSalesChannel):
        self.sales_channel = sales_channel


class SheinSignatureMixinTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
            open_key_id="open-key",
            secret_key="secret-key",
        )
        self.factory = _DummyFactory(sales_channel=self.sales_channel)

    def test_build_shein_headers_includes_signature_and_language(self) -> None:
        self.sales_channel.multi_tenant_company.language = "es"
        self.sales_channel.multi_tenant_company.save(update_fields=["language"])

        with patch.object(
            self.factory,
            "generate_shein_signature",
            return_value=("signed-value", 1700000000000, "abcde"),
        ) as signature_mock:
            headers, timestamp, random_key = self.factory.build_shein_headers(
                path="/open-api/orders/sync",
                add_language=True,
                extra_headers={"Custom": "Value"},
            )

        signature_mock.assert_called_once_with(
            path="/open-api/orders/sync",
            timestamp=None,
            random_key=None,
        )

        expected_headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "x-lt-openKeyId": "open-key",
            "x-lt-timestamp": "1700000000000",
            "x-lt-signature": "signed-value",
            "language": "es",
            "Custom": "Value",
        }

        self.assertEqual(headers, expected_headers)
        self.assertEqual(timestamp, 1700000000000)
        self.assertEqual(random_key, "abcde")

    # @TODO: FIX THIS AFTER DEPLOY
    # def test_build_shein_headers_maps_portuguese_to_brazilian(self) -> None:
    #     self.sales_channel.multi_tenant_company.language = "pt"
    #     self.sales_channel.multi_tenant_company.save(update_fields=["language"])
    #
    #     with patch.object(
    #         self.factory,
    #         "generate_shein_signature",
    #         return_value=("signed-value", 1700000000000, "abcde"),
    #     ):
    #         headers, _, _ = self.factory.build_shein_headers(
    #             path="/open-api/orders/sync",
    #         )
    #
    #     self.assertEqual(headers["language"], "pt-br")

    def test_build_shein_headers_skips_language_when_disabled(self) -> None:
        with patch.object(
            self.factory,
            "generate_shein_signature",
            return_value=("signed-value", 1700000000000, "abcde"),
        ):
            headers, _, _ = self.factory.build_shein_headers(
                path="/open-api/orders/sync",
                add_language=False,
            )

        self.assertNotIn("language", headers)

    @override_settings(DEBUG=False)
    @patch("sales_channels.integrations.shein.factories.mixins.requests.post")
    def test_shein_post_executes_request_with_expected_arguments(self, post_mock: Mock) -> None:
        response = Mock()
        response.raise_for_status = Mock()
        post_mock.return_value = response

        with patch.object(
            self.factory,
            "build_shein_headers",
            return_value=(
                {
                    "Content-Type": "application/json;charset=UTF-8",
                    "x-lt-openKeyId": "open-key",
                    "x-lt-timestamp": "1700000000000",
                    "x-lt-signature": "signed-value",
                    "language": "fr",
                },
                1700000000000,
                "abcde",
            ),
        ) as headers_mock:
            result = self.factory.shein_post(
                path="/open-api/orders/sync",
                payload={"foo": "bar"},
                add_language=True,
                timeout=20,
            )

        headers_mock.assert_called_once_with(
            path="/open-api/orders/sync",
            add_language=True,
            timestamp=None,
            random_key=None,
            extra_headers=None,
        )

        post_mock.assert_called_once_with(
            "https://openapi.sheincorp.com/open-api/orders/sync",
            json={"foo": "bar"},
            headers=headers_mock.return_value[0],
            timeout=20,
            verify=self.sales_channel.verify_ssl,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertIs(result, response)

    @override_settings(DEBUG=False)
    @patch("sales_channels.integrations.shein.factories.mixins.requests.get")
    def test_shein_get_executes_request_with_expected_arguments(self, get_mock: Mock) -> None:
        response = Mock()
        response.raise_for_status = Mock()
        get_mock.return_value = response

        with patch.object(
            self.factory,
            "build_shein_headers",
            return_value=(
                {
                    "Content-Type": "application/json;charset=UTF-8",
                    "x-lt-openKeyId": "open-key",
                    "x-lt-timestamp": "1700000000000",
                    "x-lt-signature": "signed-value",
                    "language": "fr",
                },
                1700000000000,
                "abcde",
            ),
        ) as headers_mock:
            result = self.factory.shein_get(
                path="/open-api/msc/warehouse/list",
                payload={"page": 1},
                add_language=True,
                timeout=20,
            )

        headers_mock.assert_called_once_with(
            path="/open-api/msc/warehouse/list",
            add_language=True,
            timestamp=None,
            random_key=None,
            extra_headers=None,
        )

        get_mock.assert_called_once_with(
            "https://openapi.sheincorp.com/open-api/msc/warehouse/list",
            params={"page": 1},
            headers=headers_mock.return_value[0],
            timeout=20,
            verify=self.sales_channel.verify_ssl,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertIs(result, response)

    # @TODO: FIX THIS AFTER DEPLOY
    # @patch("sales_channels.integrations.shein.factories.mixins.requests.post")
    # def test_shein_post_network_error_raises_value_error(self, post_mock: Mock) -> None:
    #     post_mock.side_effect = requests.RequestException("boom")
    #
    #     with self.assertRaisesMessage(ValueError, "Shein request failed: unable to reach remote service."):
    #         self.factory.shein_post(path="/open-api/failure")

    # @TODO: FIX THIS AFTER DEPLOY
    # @patch("sales_channels.integrations.shein.factories.mixins.requests.post")
    # def test_shein_post_http_error_is_wrapped(self, post_mock: Mock) -> None:
    #     response = Mock()
    #     response.raise_for_status.side_effect = requests.HTTPError("bad request")
    #     post_mock.return_value = response
    #
    #     with self.assertRaisesMessage(ValueError, "Shein request returned an HTTP error."):
    #         self.factory.shein_post(path="/open-api/orders/sync")

    @patch("sales_channels.integrations.shein.factories.mixins.requests.post")
    def test_shein_post_skip_raise_for_status(self, post_mock: Mock) -> None:
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("bad request")
        post_mock.return_value = response

        result = self.factory.shein_post(
            path="/open-api/orders/sync",
            raise_for_status=False,
        )

        self.assertIs(result, response)
        response.raise_for_status.assert_not_called()

    @patch("sales_channels.integrations.shein.factories.mixins.requests.get")
    def test_shein_get_skip_raise_for_status(self, get_mock: Mock) -> None:
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("bad request")
        get_mock.return_value = response

        result = self.factory.shein_get(
            path="/open-api/msc/warehouse/list",
            raise_for_status=False,
        )

        self.assertIs(result, response)
        response.raise_for_status.assert_not_called()
