"""Tests covering the Shein mixin helpers."""

from unittest.mock import Mock, call, patch

import requests
from django.test import override_settings
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.shein.exceptions import SheinResponseException
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import (
    SheinRemoteLanguage,
    SheinSalesChannel,
    SheinSalesChannelView,
)


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
    @patch("sales_channels.integrations.shein.decorators.time.sleep")
    @patch("sales_channels.integrations.shein.factories.mixins.requests.post")
    def test_shein_post_retries_on_timeout(self, post_mock: Mock, sleep_mock: Mock) -> None:
        response = Mock()
        response.raise_for_status = Mock()
        post_mock.side_effect = [
            requests.exceptions.ReadTimeout("slow"),
            response,
        ]

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
        ):
            result = self.factory.shein_post(
                path="/open-api/orders/sync",
                payload={"foo": "bar"},
                add_language=True,
                timeout=20,
            )

        self.assertEqual(post_mock.call_count, 2)
        sleep_mock.assert_called_once()
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

    def test_get_all_products_paginates_and_includes_filters(self) -> None:
        response_one = Mock()
        response_one.json.return_value = {
            "code": "0",
            "msg": "OK",
            "info": {
                "data": [
                    {"spuName": "M1"},
                    {"spuName": "M2"},
                ]
            },
        }
        response_two = Mock()
        response_two.json.return_value = {
            "code": "0",
            "msg": "OK",
            "info": {
                "data": [
                    {"spuName": "M3"},
                ]
            },
        }

        with patch.object(
            self.factory,
            "shein_post",
            side_effect=[response_one, response_two],
        ) as post_mock:
            results = list(
                self.factory.get_all_products(
                    page_size=2,
                    insert_time_start="2024-11-15 20:00:00",
                    insert_time_end="2024-11-15 19:00:00",
                    update_time_start="2024-11-15 19:00:00",
                    update_time_end="2024-11-15 19:00:00",
                )
            )

        expected_payload_base = {
            "pageSize": 2,
            "insertTimeStart": "2024-11-15 20:00:00",
            "insertTimeEnd": "2024-11-15 19:00:00",
            "updateTimeStart": "2024-11-15 19:00:00",
            "updateTimeEnd": "2024-11-15 19:00:00",
        }

        post_mock.assert_has_calls(
            [
                call(
                    path="/open-api/openapi-business-backend/product/query",
                    payload={**expected_payload_base, "pageNum": 1},
                ),
                call(
                    path="/open-api/openapi-business-backend/product/query",
                    payload={**expected_payload_base, "pageNum": 2},
                ),
            ]
        )

        self.assertEqual(
            results,
            [
                {"spuName": "M1"},
                {"spuName": "M2"},
                {"spuName": "M3"},
            ],
        )

    def test_get_all_products_skips_failed_page_on_timeout(self) -> None:
        response = Mock()
        response.json.return_value = {
            "code": "0",
            "msg": "OK",
            "info": {
                "data": [
                    {"spuName": "M1"},
                ]
            },
        }

        timeout_error = ValueError("Shein request failed")
        timeout_error.__cause__ = requests.exceptions.ReadTimeout("slow")

        with patch.object(
            self.factory,
            "shein_post",
            side_effect=[timeout_error, response],
        ) as post_mock:
            results = list(
                self.factory.get_all_products(
                    page_size=2,
                    skip_failed_page=True,
                    max_failed_pages=2,
                )
            )

        post_mock.assert_has_calls(
            [
                call(
                    path="/open-api/openapi-business-backend/product/query",
                    payload={"pageSize": 2, "pageNum": 1},
                ),
                call(
                    path="/open-api/openapi-business-backend/product/query",
                    payload={"pageSize": 2, "pageNum": 2},
                ),
            ]
        )
        self.assertEqual(results, [{"spuName": "M1"}])

    def test_get_all_products_raises_on_error_response(self) -> None:
        response = Mock()
        response.json.return_value = {"code": "1", "msg": "nope"}

        with patch.object(self.factory, "shein_post", return_value=response):
            with self.assertRaisesMessage(
                ValueError,
                "Failed to fetch Shein products: nope",
            ):
                list(self.factory.get_all_products())

    def test_get_product_uses_view_languages_and_returns_info(self) -> None:
        view = SheinSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            name="Default View",
            is_default=True,
        )
        SheinRemoteLanguage.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel_view=view,
            local_instance="pt",
            remote_code="pt",
        )
        SheinRemoteLanguage.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel_view=view,
            local_instance=None,
            remote_code="zh-cn",
        )

        response = Mock()
        response.json.return_value = {
            "code": "0",
            "msg": "OK",
            "info": {"spuName": "MM2404163183"},
        }

        with patch.object(self.factory, "shein_post", return_value=response) as post_mock:
            info = self.factory.get_product(spu_name="MM2404163183")

        post_mock.assert_called_once_with(
            path="/open-api/goods/spu-info",
            payload={
                "languageList": ["pt-br", "zh-cn"],
                "spuName": "MM2404163183",
            },
            add_language=False,
        )
        self.assertEqual(info, {"spuName": "MM2404163183"})

    def test_get_product_defaults_to_english_when_no_languages(self) -> None:
        response = Mock()
        response.json.return_value = {
            "code": "0",
            "msg": "OK",
            "info": {"spuName": "MM2404163183"},
        }

        with patch.object(self.factory, "shein_post", return_value=response) as post_mock:
            self.factory.get_product(spu_name="MM2404163183")

        post_mock.assert_called_once_with(
            path="/open-api/goods/spu-info",
            payload={
                "languageList": ["en"],
                "spuName": "MM2404163183",
            },
            add_language=False,
        )

    def test_get_product_raises_on_error_response(self) -> None:
        response = Mock()
        response.json.return_value = {
            "code": "0003",
            "msg": "unable to obtain skc information according to spu",
        }

        with patch.object(self.factory, "shein_post", return_value=response):
            with self.assertRaises(SheinResponseException):
                self.factory.get_product(spu_name="MM2404163183")

    def test_get_store_info_returns_payload(self) -> None:
        response = Mock()
        response.json.return_value = {
            "code": "0",
            "msg": "OK",
            "info": {
                "storeProductQuota": {"usedQuota": 12},
                "storeInfo": {"supplierId": 123},
            },
        }

        with patch.object(self.factory, "shein_post", return_value=response) as post_mock:
            info = self.factory.get_store_info()

        post_mock.assert_called_once_with(
            path="/open-api/openapi-business-backend/query-store-info",
            payload={},
            add_language=False,
        )
        self.assertEqual(
            info,
            {
                "storeProductQuota": {"usedQuota": 12},
                "storeInfo": {"supplierId": 123},
            },
        )

    def test_get_total_product_count_returns_used_quota(self) -> None:
        response = Mock()
        response.json.return_value = {
            "code": "0",
            "msg": "OK",
            "info": {"storeProductQuota": {"usedQuota": "37"}},
        }

        with patch.object(self.factory, "shein_post", return_value=response):
            total = self.factory.get_total_product_count()

        self.assertEqual(total, 37)
