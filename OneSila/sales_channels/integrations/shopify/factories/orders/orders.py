import json
from datetime import datetime, timedelta
from orders.models import Order, OrderItem
from sales_channels.models import RemoteProduct, RemoteLog
from sales_channels.factories.orders.orders import RemoteOrderPullFactory
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifyOrder, ShopifyOrderItem


class ShopifyOrderPullFactory(GetShopifyApiMixin, RemoteOrderPullFactory):
    remote_model_class = ShopifyOrder
    field_mapping = {
        'remote_id': 'id',
        'raw_data': 'to_dict',
    }
    get_or_create_fields = ['remote_id']
    allow_create = True
    allow_update = False
    allow_delete = False
    is_model_response = False  # this is JSON dicts from GraphQL

    def __init__(self, sales_channel, api=None, since_hours_ago=24):
        super().__init__(sales_channel, api)
        self.since_hours_ago = since_hours_ago
        self.multi_tenant_company = sales_channel.multi_tenant_company

    def fetch_remote_instances(self):
        cutoff_date = (datetime.utcnow() - timedelta(hours=self.since_hours_ago)).isoformat()
        query = '''
        query ($sinceQuery: String) {
          orders(first: 50, query: $sinceQuery) {
            edges {
              node {
                id
                name
                createdAt
                currencyCode
                lineItems(first: 100) {
                  edges {
                    node {
                      id
                      sku
                      quantity
                      originalUnitPriceSet {
                        shopMoney {
                          amount
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        '''
        gql = self.api.GraphQL()
        cutoff_date = (datetime.utcnow() - timedelta(hours=self.since_hours_ago)).date().isoformat()
        variables = {
            "sinceQuery": f"updated_at:>={cutoff_date} AND financial_status:paid AND fulfillment_status:shipped"
        }

        result = gql.execute(query, variables)
        data = json.loads(result)

        self.remote_instances = [
            edge["node"] for edge in data.get("data", {}).get("orders", {}).get("edges", [])
        ]

    def process_remote_instance(self, remote_data, remote_instance_mirror, created):
        if not created:
            return

        created_at = datetime.fromisoformat(remote_data['createdAt'].replace('Z', '+00:00'))
        reference = remote_data['name']
        currency_code = remote_data['currencyCode']

        # Create Order
        local_order = Order.objects.create(
            **self.get_order_default_fields(),
            reference=reference,
            currency=currency_code,
            price_incl_vat=True,
        )
        Order.objects.filter(pk=local_order.pk).update(created_at=created_at)

        remote_instance_mirror.local_instance = local_order
        remote_instance_mirror.save()

        # Add line items
        for edge in remote_data.get('lineItems', {}).get('edges', []):
            item = edge['node']
            sku = item['sku']
            price = item['originalUnitPriceSet']['shopMoney']['amount']
            quantity = item['quantity']

            rp = RemoteProduct.objects.filter(remote_sku=sku, sales_channel=self.sales_channel).first()
            if not rp or not rp.local_instance:
                continue

            local_item = OrderItem.objects.create(
                order=local_order,
                product=rp.local_instance,
                quantity=quantity,
                price=price,
                multi_tenant_company=self.multi_tenant_company
            )

            mirror_item = ShopifyOrderItem.objects.create(
                local_instance=local_item,
                remote_order=remote_instance_mirror,
                remote_sku=sku,
                remote_id=item['id'],
                price=price,
                quantity=quantity,
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel
            )

            self.log_action_for_instance(
                mirror_item,
                RemoteLog.ACTION_CREATE,
                item,
                {},
                self.get_identifiers()[0]
            )
