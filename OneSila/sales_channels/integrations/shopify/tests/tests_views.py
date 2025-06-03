import json
from django.test import Client
from sales_channels.integrations.shopify.models import ShopifySalesChannelView, ShopifySalesChannel
from core.tests import TestCase

# class ShopifyWebhookTests(TestCase):
#     def setUp(self):
#         super().setUp()
#         self.client = Client()
#         self.customer_data_request_url = "/direct/integrations/shopify/customerdata/request/"
#         self.customer_data_erase_url = "/direct/integrations/shopify/customerdata/erase/"
#         self.shop_data_erase_url = "/direct/integrations/shopify/shopdata/erase/"
#
#     def test_customer_data_request_does_not_crash(self):
#         response = self.client.post(
#             self.customer_data_request_url,
#             data=json.dumps({"customer": "123"}),
#             content_type="application/json"
#         )
#         self.assertEqual(response.status_code, 200)
#
#     def test_customer_data_erase_does_not_crash(self):
#         response = self.client.post(
#             self.customer_data_erase_url,
#             data=json.dumps({"customer": "456"}),
#             content_type="application/json"
#         )
#         self.assertEqual(response.status_code, 200)
#
#     def test_shop_data_erase_marks_sales_channel_for_delete(self):
#
#         # Setup: create a sales channel + view
#         sales_channel = ShopifySalesChannel.objects.create(hostname="https//:shopify.test.com", multi_tenant_company=self.multi_tenant_company)
#         view = ShopifySalesChannelView.objects.create(
#             sales_channel=sales_channel,
#             remote_id="999999999",
#             multi_tenant_company=self.multi_tenant_company
#         )
#
#         payload = {
#             "shop_id": "999999999"
#         }
#
#         response = self.client.post(
#             self.shop_data_erase_url,
#             data=json.dumps(payload),
#             content_type="application/json"
#         )
#         self.assertEqual(response.status_code, 200)
#
#         # Refresh from DB
#         view.refresh_from_db()
#         view.sales_channel.refresh_from_db()
#         self.assertTrue(view.sales_channel.mark_for_delete)
#
#     def test_shop_data_erase_missing_view_logs_warning(self):
#         payload = {
#             "shop_id": "nonexistent"
#         }
#         response = self.client.post(
#             self.shop_data_erase_url,
#             data=json.dumps(payload),
#             content_type="application/json"
#         )
#         self.assertEqual(response.status_code, 200)
#
#     def test_shop_data_erase_invalid_payload_returns_400(self):
#         response = self.client.post(
#             self.shop_data_erase_url,
#             data="not-a-json",
#             content_type="application/json"
#         )
#         self.assertEqual(response.status_code, 400)