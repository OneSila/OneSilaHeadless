from datetime import datetime
from magento.models import Order as MagentoApiOrder
from core.helpers import clean_json_data
from orders.models import Order, OrderItem
from sales_channels.factories.orders.orders import RemoteOrderPullFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoOrder, MagentoSalesChannelView, MagentoCurrency, MagentoOrderItem
from sales_channels.integrations.magento2.models.sales_channels import MagentoRemoteLanguage
from sales_channels.models import RemoteProduct, RemoteLog


class MagentoOrderPullFactory(GetMagentoAPIMixin, RemoteOrderPullFactory):
    remote_model_class = MagentoOrder
    field_mapping = {
        'remote_id': 'entity_id',
        'raw_data': 'data',
    }
    get_or_create_fields = ['remote_id']
    is_model_response = True

    def __init__(self, sales_channel, api=None, since_hours_ago=24):
        super().__init__(sales_channel, api)
        self.since_hours_ago = since_hours_ago
        self.multi_tenant_company = sales_channel.multi_tenant_company

    def fetch_remote_instances(self):
        """
        Fetch remote instances using the Magento API's `all_in_memory` method, 
        which retrieves all relevant orders since the specified number of hours ago,
        with a fallback to the `sync_orders_after` date if it is more recent.
        """

        # Fetch remote instances using the since_date
        self.remote_instances = self.api.orders.\
            add_criteria('status', MagentoApiOrder.STATUS_COMPLETE).\
            all_in_memory()


    def process_remote_instance(self, remote_data: MagentoApiOrder, remote_instance_mirror: MagentoOrder, created: bool):
        """
        Processes each order by sequentially handling creation, order creation,
        address assignments, order items, and final status changes.
        """

        # if this get imported after was already imported no need to do anything
        if not created:
            return

        # Set the sales view
        self.set_sales_view(remote_data)

        # Set the remote language and currency
        self.set_remote_currency(remote_data)

        local_order = self.create_local_order(remote_data)
        self.assign_local_order(remote_instance_mirror, local_order)
        self.populate_items(local_order, remote_data, remote_instance_mirror)


    def set_sales_view(self, remote_data):
        """
        Sets the sales view for the order based on the `store_id` in the remote data.
        """
        store_id = remote_data.store_id
        if not store_id:
            raise ValueError("Store ID not found in the remote data.")

        self.sales_view = MagentoSalesChannelView.objects.filter(
            remote_id=store_id,
            sales_channel=self.sales_channel
        ).first()

        if not self.sales_view:
            raise ValueError(f"Sales Channel View not found for store ID {store_id} in sales channel {self.sales_channel}.")

    def set_remote_currency(self, remote_data):
        """
        Sets the remote currency for the order using the sales view and sales channel.
        """
        self.remote_currency = MagentoCurrency.objects.filter(
            website_code=self.sales_view.code,
            sales_channel=self.sales_channel
        ).first()

        if not self.remote_currency:
            raise ValueError(f"Remote currency not found for sales view {self.sales_view} in sales channel {self.sales_channel}.")

    def create_local_order(self, remote_data):
        """
        Creates or retrieves a local order instance from the remote data
        """

        base_subtotal = remote_data.base_subtotal
        base_subtotal_incl_tax = remote_data.base_subtotal_incl_tax
        price_incl_vat = base_subtotal == base_subtotal_incl_tax
        created_at_dt = datetime.strptime(remote_data.created_at, '%Y-%m-%d %H:%M:%S')

        # Extract order reference from remote data
        reference = remote_data.increment_id

        # Lookup fields for finding an existing order
        lookup_fields = {
            'reference': reference,
            'multi_tenant_company': self.sales_channel.multi_tenant_company,
            'source': self.sales_channel
        }

        # Attempt to find an existing order first
        local_order = Order.objects.filter(**lookup_fields).first()

        if local_order:
            return local_order

        # Create the order if not found
        local_order = Order.objects.create(
            **self.get_order_default_fields(),
            reference=reference,
            currency=self.remote_currency.local_instance,
            price_incl_vat=price_incl_vat,
        )

        # we need to set the created_at like this to bypass theauto_now_add
        Order.objects.filter(pk=local_order.pk).update(created_at=created_at_dt)

        return local_order

    def assign_local_order(self, remote_order, local_order):
        """
        Assigns the local order instance to the remote order mirror instance.
        """
        remote_order.local_instance = local_order
        remote_order.save()

    def populate_items(self, local_order, remote_data, remote_instance_mirror):
        """
        Populates order items for the local order using data from the remote system.
        """
        for item in remote_data.items:
            # Fetch the remote SKU
            remote_sku = item.sku

            # Try to get the corresponding remote product by SKU and sales channel
            remote_product = RemoteProduct.objects.filter(
                remote_sku=remote_sku,
                sales_channel=self.sales_channel
            ).first()

            # Pass the fetched remote_product to the create methods
            local_order_item = self.create_local_order_item(local_order, item, remote_product)
            self.create_remote_order_item(local_order_item, remote_instance_mirror, item, remote_product)

    def create_local_order_item(self, local_order, item_data, remote_product):

        if not remote_product:
            return None

        # Try to retrieve the local order item by order and product
        local_order_item = OrderItem.objects.filter(
            order=local_order,
            product=remote_product.local_instance
        ).first()

        if local_order_item:
            return local_order_item

        # Creating the local order item
        local_order_item = OrderItem.objects.create(
            order=local_order,
            product=remote_product.local_instance,
            quantity=item_data.qty_ordered,
            price=item_data.price,
            multi_tenant_company=self.multi_tenant_company
        )

        return local_order_item

    def create_remote_order_item(self, local_item, remote_order, item_data, remote_product):

        remote_order_item = MagentoOrderItem.objects.filter(
            remote_order=remote_order,
            remote_sku=item_data.sku
        ).first()

        if remote_order_item:
            return remote_order_item

        # Creating the remote order item
        raw_data = clean_json_data(item_data.to_dict())
        remote_order_item = MagentoOrderItem.objects.create(
            local_instance=local_item,
            remote_order=remote_order,
            remote_product=remote_product,
            price=item_data.price,
            quantity=item_data.qty_ordered,
            remote_sku=item_data.sku,
            remote_id=item_data.item_id,
            raw_data=raw_data,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel
        )

        self.log_action_for_instance(
            remote_order_item,
            RemoteLog.ACTION_CREATE,
            raw_data,
            {},
            self.get_identifiers()[0]
        )

        return remote_order_item