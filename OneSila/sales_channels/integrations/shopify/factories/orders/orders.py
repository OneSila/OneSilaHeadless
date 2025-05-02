import datetime
from django.utils.dateparse import parse_datetime
from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models.orders import ShopifyOrder, ShopifyOrderItem
from orders.models import Order, OrderItem
from sales_channels.models import RemoteProduct, RemoteLog

class ShopifyOrderPullFactory(GetShopifyApiMixin, PullRemoteInstanceMixin):
    remote_model_class = ShopifyOrder
    field_mapping = {
        'remote_id': 'id',
        'raw_data': 'to_dict',
    }
    get_or_create_fields = ['remote_id']
    api_package_name = 'Order'
    api_method_name = 'find'
    api_method_is_property = False
    allow_create = True
    allow_update = False
    allow_delete = False
    is_model_response = True

    def __init__(self, sales_channel, api=None, since_hours_ago=24):
        super().__init__(sales_channel, api)
        self.since_hours_ago = since_hours_ago
        self.multi_tenant_company = self.sales_channel.multi_tenant_company

    def fetch_remote_instances(self):
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=self.since_hours_ago)).isoformat()
        orders = self.api.Order.find(updated_at_min=cutoff, status='any')
        self.remote_instances = orders

    def process_remote_instance(self, remote_data, remote_instance_mirror, created):
        if not created:
            return

        created_at = parse_datetime(remote_data.created_at)
        reference = getattr(remote_data, 'name', None) or str(remote_data.id)

        local_order = Order.objects.create(
            **self.get_order_default_fields(),
            reference=reference,
            currency=remote_data.currency,
            price_incl_vat=True,
        )
        Order.objects.filter(pk=local_order.pk).update(created_at=created_at)

        remote_instance_mirror.local_instance = local_order
        remote_instance_mirror.save()

        for item in remote_data.line_items:
            remote_sku = item.sku
            rp = RemoteProduct.objects.filter(remote_sku=remote_sku, sales_channel=self.sales_channel).first()
            if not rp or not rp.local_instance:
                continue

            local_item = OrderItem.objects.create(
                order=local_order,
                product=rp.local_instance,
                quantity=item.quantity,
                price=item.price,
                multi_tenant_company=self.multi_tenant_company
            )

            mirror_item = ShopifyOrderItem.objects.create(
                local_instance=local_item,
                remote_order=remote_instance_mirror,
                remote_sku=item.sku,
                remote_id=item.id,
                price=item.price,
                quantity=item.quantity,
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel
            )

            self.log_action_for_instance(
                mirror_item,
                RemoteLog.ACTION_CREATE,
                item.to_dict(),
                {},
                self.get_identifiers()[0]
            )

    def serialize_response(self, response):
        return response
