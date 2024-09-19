from datetime import datetime, timedelta
from magento.models import Order as MagentoApiOrder
from contacts.languages import LANGUAGE_TO_CUSTOMER_CONVERTOR
from contacts.models import Customer, ShippingAddress, InvoiceAddress, Address
from core.helpers import clean_json_data
from orders.models import Order, OrderItem
from sales_channels.factories.orders.orders import RemoteOrderPullFactory, ChangeRemoteOrderStatus, SyncCancelledOrdersFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoOrder, MagentoSalesChannelView, MagentoCurrency, MagentoCustomer, MagentoOrderItem
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

    MAGENTO_TO_LOCAL_STATUS_MAPPING = {
        MagentoApiOrder.STATUS_CANCELED: Order.CANCELLED,  # Magento canceled -> Local CANCELLED
        MagentoApiOrder.STATUS_CLOSED: Order.CANCELLED,  # Magento closed -> Local CANCELLED
        MagentoApiOrder.STATUS_COMPLETE: Order.SHIPPED,  # Magento complete -> Local SHIPPED
        MagentoApiOrder.STATUS_HOLDED: Order.HOLD,  # Magento holded -> Local HOLD
        MagentoApiOrder.STATUS_PENDING: Order.DRAFT,  # Magento pending -> Local DRAFT
        MagentoApiOrder.STATUS_PROCESSING: Order.DRAFT,  # Magento processing -> Local DRAFT
        MagentoApiOrder.STATUS_UNHOLDED: Order.DRAFT,  # Magento unhold -> Local DRAFT
    }

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
        # Calculate since_date from since_hours_ago
        calculated_since_date = datetime.now() - timedelta(hours=self.since_hours_ago)

        # Use sync_orders_after as a fallback if it is more recent than calculated_since_date
        if self.sales_channel.sync_orders_after and self.sales_channel.sync_orders_after > calculated_since_date:
            since_date = self.sales_channel.sync_orders_after
        else:
            since_date = calculated_since_date

        # Convert since_date to the required string format
        since_date_str = since_date.strftime('%Y-%m-%d %H:%M:%S')

        # Fetch remote instances using the since_date
        self.remote_instances = self.api.orders.\
            since(since_date_str).\
            add_criteria('status', MagentoApiOrder.STATUS_PROCESSING).\
            all_in_memory()


    def process_remote_instance(self, remote_data: MagentoApiOrder, remote_instance_mirror: MagentoOrder, created: bool):
        """
        Processes each order by sequentially handling customer creation, order creation,
        address assignments, order items, and final status changes.
        """

        # if this get imported after was already imported no need to do anything
        if not created:
            return

        # Set the sales view
        self.set_sales_view(remote_data)

        # Set the remote language and currency
        self.set_remote_language(remote_data)
        self.set_remote_currency(remote_data)

        # Step 1: Get or create the local customer
        local_customer = self.get_or_create_local_customer(remote_data)

        # Step 2: Get or create the local shipping address linked to the local customer
        shipping_address = self.get_or_create_local_shipping_address(remote_data, local_customer)

        # Step 3: Get or create the local invoice address linked to the local customer
        invoice_address = self.get_or_create_local_invoice_address(remote_data, local_customer)

        # Step 4: Get or create the remote customer mirror instance
        remote_customer = self.get_or_create_remote_customer(local_customer, remote_data, shipping_address, invoice_address)

        # Step 5: Create the local order linked to the local customer
        local_order = self.create_local_order(remote_data, local_customer, shipping_address, invoice_address)

        # Step 6: Assign the local order to the remote order mirror
        self.assign_local_order(remote_instance_mirror, local_order)

        # Step 7: Populate order items for the local order
        self.populate_items(local_order, remote_data, remote_instance_mirror)

        # Step 8: Update the status of the local order after processing
        self.change_status_after_process(remote_data, local_order)

    def extract_address_fields(self, address_data, remote_data):
        """
        Extracts address fields from the given address data.

        :param address_data: Dictionary containing address details from remote data.
        :param remote_data: The full remote order data from which to extract additional fields like VAT.
        :return: A dictionary with extracted address fields.
        """
        # Extract address fields
        street_lines = address_data.get('street', [])
        address1 = street_lines[0] if len(street_lines) > 0 else ''
        address2 = street_lines[1] if len(street_lines) > 1 else ''
        address3 = street_lines[2] if len(street_lines) > 2 else ''

        # If there are more than three elements, adjust address2 and address3
        if len(street_lines) > 3:
            address2 = f"{street_lines[1]} {street_lines[2]}".strip()
            address3 = street_lines[3]

        # Map the rest of the fields
        postcode = address_data.get('postcode', '')
        city = address_data.get('city', '')
        country = address_data.get('country_id', '')
        region = address_data.get('region', '')

        # Optionally, append the region to address3 if useful
        if region and address3:
            address3 = f"{address3}, {region}".strip()
        elif region and not address3:
            address3 = region

        # VAT number is directly from remote_data
        vat_number = remote_data.customer_taxvat if hasattr(remote_data, 'customer_taxvat') else None

        return {
            'address1': address1,
            'address2': address2,
            'address3': address3,
            'postcode': postcode,
            'city': city,
            'country': country,
            'vat_number': vat_number,
        }

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

    def set_remote_language(self, remote_data):
        """
        Sets the remote language for the order using the sales view and sales channel.
        """
        self.remote_language = MagentoRemoteLanguage.objects.filter(
            sales_channel_view=self.sales_view,
            sales_channel=self.sales_channel
        ).first()

        if not self.remote_language:
            raise ValueError(f"Remote language not found for sales view {self.sales_view} in sales channel {self.sales_channel}.")

    def set_remote_currency(self, remote_data):
        """
        Sets the remote currency for the order using the sales view and sales channel.
        """
        self.remote_currency = MagentoCurrency.objects.filter(
            sales_channel_view=self.sales_view,
            sales_channel=self.sales_channel
        ).first()

        if not self.remote_currency:
            raise ValueError(f"Remote currency not found for sales view {self.sales_view} in sales channel {self.sales_channel}.")

    def get_or_create_local_customer(self, remote_data):
        """
        Retrieves or creates a local customer instance from the remote data.
        """
        # Extract the billing address to check for company name
        billing_address = remote_data.billing_address
        company_name = billing_address.get('company', None)

        # If company name exists, use it; otherwise, fallback to first and last name
        if company_name:
            name = company_name
        else:
            first_name = remote_data.customer_firstname
            last_name = remote_data.customer_lastname
            name = f"{first_name} {last_name}".strip()

        email = remote_data.customer_email

        local_customer = Customer.objects.filter(
            name=name,
            email=email,
            multi_tenant_company=self.multi_tenant_company
        ).first()

        if local_customer:
            return local_customer

        # Extract additional fields for creating a new customer
        phone = billing_address.get('telephone', '')

        # Create a new customer instance if not found
        local_customer = Customer.objects.create(
            name=name,
            phone=phone,
            email=email,
            language=LANGUAGE_TO_CUSTOMER_CONVERTOR.get(self.remote_language.local_instance, None),
            currency=self.remote_currency.local_instance,
            multi_tenant_company=self.multi_tenant_company
        )

        return local_customer

    def get_or_create_remote_customer(self, local_customer, remote_data, shipping_address, invoice_address):
        """
        Retrieves or creates a remote customer mirror instance from the remote data, associated with the local customer.
        """
        remote_customer = getattr(remote_data, 'customer', None)
        remote_id = None if not remote_customer else remote_customer.id

        existing_remote_customer = MagentoCustomer.objects.filter(
            local_instance=local_customer,
            remote_id=remote_id,
            sales_channel=self.sales_channel
        ).first()

        if existing_remote_customer:
            return existing_remote_customer

        raw_data = clean_json_data(remote_customer.to_dict() if remote_customer else {})
        new_remote_customer = MagentoCustomer.objects.create(
            local_instance=local_customer,
            remote_id=remote_id,
            shipping_address=shipping_address,
            invoice_address=invoice_address,
            raw_data=raw_data,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company
        )

        self.log_action_for_instance(
            new_remote_customer,
            RemoteLog.ACTION_CREATE,
            raw_data,
            {},
            self.get_identifier()
        )

        return new_remote_customer

    def create_local_order(self, remote_data, local_customer, shipping_address, invoice_address):
        """
        Creates or retrieves a local order instance from the remote data, using the provided local customer,
        shipping address, and invoice address.
        """

        base_subtotal = remote_data.base_subtotal
        base_subtotal_incl_tax = remote_data.base_subtotal_incl_tax
        price_incl_vat = base_subtotal == base_subtotal_incl_tax

        # Extract order reference from remote data
        reference = remote_data.increment_id

        # Lookup fields for finding an existing order
        lookup_fields = {
            'reference': reference,
            'customer': local_customer,
        }

        # Attempt to find an existing order first
        local_order = Order.objects.filter(**lookup_fields).first()

        if local_order:
            return local_order

        # Create the order if not found
        local_order = Order.objects.create(
            reference=reference,
            customer=local_customer,
            invoice_address=invoice_address,
            shipping_address=shipping_address,
            currency=self.remote_currency.local_instance,
            price_incl_vat=price_incl_vat,
            reason_for_sale=Order.SALE,
            status=self.MAGENTO_TO_LOCAL_STATUS_MAPPING.get(remote_data.status, Order.DRAFT),
            multi_tenant_company=self.multi_tenant_company,
        )

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
            self.get_identifier()
        )

        return remote_order_item

    def get_or_create_local_shipping_address(self, remote_data, local_customer):
        """
        Retrieves or creates a local shipping address instance from the remote data, associated with the local customer.
        """
        # Extract shipping address data
        shipping_address_data = remote_data.extension_attributes.get('shipping_assignments', [])[0] \
            .get('shipping', {}).get('address', {})

        # Use helper method to extract address fields
        address_fields = self.extract_address_fields(shipping_address_data, remote_data)

        lookup_fields = {
            'company': local_customer,
            'postcode': address_fields['postcode'],
        }

        # Attempt to find an existing address first based on postcode
        existing_address = Address.objects.filter(**lookup_fields).first()
        if existing_address:
            # If it exists but isn't marked as a shipping address, update it
            if not existing_address.is_shipping_address:
                existing_address.is_shipping_address = True
                existing_address.save()
            return existing_address

        shipping_address = ShippingAddress.objects.create(
            company=local_customer,
            address1=address_fields['address1'],
            address2=address_fields['address2'],
            address3=address_fields['address3'],
            postcode=address_fields['postcode'],
            city=address_fields['city'],
            country=address_fields['country'],
            vat_number=address_fields['vat_number'],
            multi_tenant_company=self.multi_tenant_company
        )

        return shipping_address

    def get_or_create_local_invoice_address(self, remote_data, local_customer):
        """
        Retrieves or creates a local billing address instance from the remote data, associated with the local customer.
        """
        billing_address_data = remote_data.billing_address

        address_fields = self.extract_address_fields(billing_address_data, remote_data)

        lookup_fields = {
            'company': local_customer,
            'postcode': address_fields['postcode'],
        }

        # Attempt to find an existing address first based on postcode
        existing_address = Address.objects.filter(**lookup_fields).first()
        if existing_address:
            if not existing_address.is_invoice_address:
                existing_address.is_invoice_address = True
                existing_address.save()
            return existing_address

        # Create a new address if none found
        billing_address = InvoiceAddress.objects.create(
            company=local_customer,
            address1=address_fields['address1'],
            address2=address_fields['address2'],
            address3=address_fields['address3'],
            postcode=address_fields['postcode'],
            city=address_fields['city'],
            country=address_fields['country'],
            vat_number=address_fields['vat_number'],
            is_invoice_address=True,
            multi_tenant_company=self.multi_tenant_company
        )

        return billing_address

    def change_status_after_process(self, remote_data, local_order):
        """
        Changes the status of the local order after processing.
        """
        pass
        # if remote_data.status == MagentoApiOrder.STATUS_PENDING:
        #     remote_data.update_status(MagentoApiOrder.STATUS_PROCESSING)

class MagentoChangeRemoteOrderStatus(GetMagentoAPIMixin, ChangeRemoteOrderStatus):

    REMOTE_TO_SHIP_STATUS = MagentoApiOrder.STATUS_PROCESSING
    REMOTE_SHIPPED_STATUS = MagentoApiOrder.STATUS_COMPLETE
    REMOTE_CANCELLED_STATUS = MagentoApiOrder.STATUS_CANCELED
    REMOTE_HOLD_STATUS = MagentoApiOrder.STATUS_HOLDED

    remote_class = MagentoOrder

    def update_remote(self):
        self.magento_instance = self.api.orders.by_id(self.remote_instance.remote_id)
        self.magento_instance.update_status(self.remote_status)

    def serialize_response(self, response):
        """
        Serializes the response from the Magento API.
        """
        return response


class MagentoSyncCancelledOrdersFactory(GetMagentoAPIMixin, SyncCancelledOrdersFactory):
    """
    Magento-specific factory to sync canceled orders from the remote system to the local system.
    Extends the base SyncCancelledOrdersFactory with Magento-specific logic.
    """
    remote_model_class = MagentoOrder

    def __init__(self, sales_channel, api=None, since_hours_ago=720):
        """
        Initialize the factory with a default of 1 month ago (720 hours).

        :param sales_channel: The sales channel for which orders are being synced.
        :param api: The API client instance, if not provided, it will use the default one.
        :param since_hours_ago: How many hours ago to start fetching canceled orders.
        """
        super().__init__(sales_channel, api)
        self.since_hours_ago = since_hours_ago

    def fetch_remote_instances(self):
        """
        Fetch remote instances using the Magento API's `all_in_memory` method,
        which retrieves all relevant orders since the specified number of hours ago.
        """
        since_date = (datetime.now() - timedelta(hours=self.since_hours_ago)).strftime('%Y-%m-%d %H:%M:%S')
        self.remote_instances = self.api.orders.since(since_date).add_criteria('status', MagentoApiOrder.STATUS_CLOSED).all_in_memory()

    def get_remote_identifier(self, remote_data):
        return remote_data.id