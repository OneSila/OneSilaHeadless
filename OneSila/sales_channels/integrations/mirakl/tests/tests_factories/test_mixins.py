from unittest.mock import Mock, patch

from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannel


class DummyMiraklAPI(GetMiraklAPIMixin):
    def __init__(self, *, sales_channel):
        self.sales_channel = sales_channel


class GetMiraklAPIMixinTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=42,
            api_key="secret-token",
            verify_ssl=True,
        )

    def test_default_params_include_shop_id(self):
        api = DummyMiraklAPI(sales_channel=self.sales_channel)

        params = api.get_mirakl_default_params(params={"max": 10})

        self.assertEqual(params["shop_id"], 42)
        self.assertEqual(params["max"], 10)

    def test_paginated_get_collects_all_pages(self):
        api = DummyMiraklAPI(sales_channel=self.sales_channel)
        payloads = [
            {"items": [{"code": "A"}, {"code": "B"}], "total_count": 3},
            {"items": [{"code": "C"}], "total_count": 3},
        ]

        with patch.object(api, "mirakl_get", side_effect=payloads) as mirakl_get:
            records = api.mirakl_paginated_get(
                path="/api/example",
                results_key="items",
                page_size=2,
            )

        self.assertEqual(records, [{"code": "A"}, {"code": "B"}, {"code": "C"}])
        self.assertEqual(mirakl_get.call_count, 2)
        self.assertEqual(mirakl_get.call_args_list[0].kwargs["params"]["offset"], 0)
        self.assertEqual(mirakl_get.call_args_list[1].kwargs["params"]["offset"], 2)

    @patch("sales_channels.integrations.mirakl.factories.mixins.time.sleep")
    @patch("sales_channels.integrations.mirakl.factories.mixins.requests.request")
    def test_request_retries_after_rate_limit(self, request_mock, sleep_mock):
        api = DummyMiraklAPI(sales_channel=self.sales_channel)
        rate_limited = Mock(status_code=429, headers={"Retry-After": "0"}, text="rate limited")
        rate_limited.json.side_effect = ValueError("not json")
        success = Mock(status_code=200, headers={}, json=Mock(return_value={"ok": True}))
        request_mock.side_effect = [rate_limited, success]

        response = api._request(method="GET", path="/api/account", expected_statuses={200})

        self.assertIs(response, success)
        self.assertEqual(request_mock.call_count, 2)
        sleep_mock.assert_called_once_with(0)

