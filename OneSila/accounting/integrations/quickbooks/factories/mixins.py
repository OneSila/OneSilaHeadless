from quickbooks import QuickBooks
from intuitlib.client import AuthClient
from datetime import timedelta
from django.utils import timezone
import logging
from quickbooks.objects import Customer, PhoneNumber, EmailAddress, Ref, Address, Account, Item
from accounting.integrations.quickbooks.helpers import map_qb_address
from accounting.integrations.quickbooks.models import QuickbooksCustomer

logger = logging.getLogger(__name__)

class GetQuickbooksAPIMixin:
    """
    Mixin to handle QuickBooks OAuth2, token management, and API access.
    Automatically handles token acquisition, storage, and refresh.
    """

    def get_auth_client(self):
        """
        Instantiate the AuthClient for OAuth2.
        """
        return AuthClient(
            client_id=self.remote_account.client_id,
            client_secret=self.remote_account.client_secret,
            environment=self.remote_account.environment,
            redirect_uri=self.remote_account.redirect_uri
        )

    def get_api(self):
        """
        Retrieve the QuickBooks API client, handling access token refresh if needed.
        """
        # Check if the access token is still valid
        if not self.remote_account.access_token or self.is_token_expired():
            self.refresh_access_token()

        # Instantiate QuickBooks client with the stored tokens
        return QuickBooks(
            auth_client=self.get_auth_client(),
            access_token=self.remote_account.access_token,
            refresh_token=self.remote_account.refresh_token,
            company_id=self.remote_account.company_id
        )

    def is_token_expired(self):
        """
        Check if the stored access token is expired.
        """
        return self.remote_account.token_expiration is None or timezone.now() >= self.remote_account.token_expiration

    def refresh_access_token(self):
        """
        Refresh the access token using the stored refresh token.
        """
        auth_client = self.get_auth_client()

        try:
            token_response = auth_client.refresh(self.remote_account.refresh_token)
            access_token_expiration = timezone.now() + timedelta(minutes=60)

            self.remote_account.access_token = auth_client.access_token
            self.remote_account.refresh_token = auth_client.refresh_token
            self.remote_account.token_expiration = access_token_expiration
            self.remote_account.save()

            logger.info(f"Successfully refreshed QuickBooks access token.")
        except Exception as e:
            logger.error(f"Failed to refresh QuickBooks access token: {e}")
            raise

class GetOrCreateQuickbooksCustomerMixin:
    """
    Mixin to handle creation or updating of a QuickBooks Customer.
    """

    def get_quickbooks_customer(self):
        """
        Retrieves the QuickBooks customer record or creates it if not available.
        """
        # Check if a QuickBooksCustomer exists for the local instance
        try:
            qb_customer = QuickbooksCustomer.objects.get(local_instance=self.customer, remote_account=self.remote_account)
            self.qb_customer_instance = qb_customer
        except QuickbooksCustomer.DoesNotExist:
            self.qb_customer_instance = None

        # If customer does not exist remotely, create it
        if not self.qb_customer_instance:
            return self.create_quickbooks_customer()
        else:
            return self.update_quickbooks_customer()

    def map_address(self, address_instance) -> Address | None:
        """
        Maps a local Address model instance to a QuickBooks Address object.
        """
        if not address_instance:
            return None

        return map_qb_address(address_instance)

    def create_quickbooks_customer(self):
        """
        Creates a new customer in QuickBooks and returns the QuickbooksCustomer instance.
        """
        # Create a QuickBooks Customer object
        qb_customer = Customer()

        # Populate QuickBooks Customer fields from the local customer instance
        qb_customer.DisplayName = self.customer.name

        if self.customer.phone:
            phone_number = PhoneNumber()
            phone_number.FreeFormNumber = self.customer.phone
            qb_customer.PrimaryPhone = phone_number

        if self.customer.email:
            email = EmailAddress()
            email.Address = self.customer.email
            qb_customer.PrimaryEmailAddr = email

        qb_customer.CompanyName = self.customer.name

        qb_customer.BillAddr = self.map_address(self.sales_order.invoice_address)
        qb_customer.ShipAddr = self.map_address(self.sales_order.shipping_address)

        # Save the customer to QuickBooks
        qb_customer.save(qb=self.api)

        # Create a QuickbooksCustomer instance and save it locally
        self.qb_customer_instance = QuickbooksCustomer.objects.create(
            multi_tenant_company=self.remote_account.multi_tenant_company,
            local_instance=self.customer,
            remote_account=self.remote_account,
            remote_id=qb_customer.Id,
        )

        return qb_customer

    def update_nested_attribute_if_needed(self, parent_obj, nested_attr_name, sub_attr_name, new_value, nested_attr_class):
        """
        Checks if the nested attribute's sub-attribute needs to be updated, and updates it if necessary.
        Returns True if an update was made, False otherwise.
        """
        needs_update = False
        nested_attr = getattr(parent_obj, nested_attr_name, None)
        current_value = None
        if nested_attr is not None:
            current_value = getattr(nested_attr, sub_attr_name, None)
        if current_value != new_value:
            needs_update = True
            if nested_attr is None:
                nested_attr = nested_attr_class()
                setattr(parent_obj, nested_attr_name, nested_attr)
            setattr(nested_attr, sub_attr_name, new_value)

        return needs_update

    def update_quickbooks_customer(self):
        """
        Updates an existing customer in QuickBooks and returns the updated QuickbooksCustomer instance.
        """
        qb_customer = Customer.get(self.qb_customer_instance.remote_id, qb=self.api)
        fields_to_update = False

        if qb_customer.DisplayName != self.customer.name:
            qb_customer.DisplayName = self.customer.name
            fields_to_update = True

        if self.update_nested_attribute_if_needed(
                qb_customer,
                'PrimaryPhone',
                'FreeFormNumber',
                self.customer.phone,
                PhoneNumber
        ):
            fields_to_update = True

        if self.update_nested_attribute_if_needed(
                qb_customer,
                'PrimaryEmailAddr',
                'Address',
                self.customer.email,
                EmailAddress
        ):
            fields_to_update = True

        if fields_to_update:
            qb_customer.save(qb=self.api)

            self.qb_customer_instance.save()

        return qb_customer


class GetCreateOrUpdateItemMixin:

    def get_or_create_item(self, item, product):
        """
        This method will attempt to retrieve an item by SKU in QuickBooks. If it doesn't exist,
        it will create the item. If it exists and has a different name, it will update it.
        """

        items = Item.filter(Name=item.name, qb=self.api)

        income_accounts = Account.filter(AccountSubType='SalesOfProductIncome', qb=self.api)
        expense_accounts = Account.filter(AccountType='Cost of Goods Sold', qb=self.api)
        asset_accounts = Account.filter(AccountSubType='OtherCurrentAssets', qb=self.api)

        if not income_accounts:
            raise ValueError("No account with AccountSubType='SalesOfProductIncome' found. This field is mandatory.")
        if not expense_accounts:
            raise ValueError("No account with AccountType='CostOfGoodsSold' found. This field is mandatory.")
        if not asset_accounts:
            raise ValueError("No account with AccountSubType='OtherCurrentAsset' found. This field is mandatory.")

        if not items:
            qb_item = Item()
            qb_item.Name = item.name
            qb_item.Sku = product.sku # this need to be set in settings so we cannot use it for filter
            qb_item.InvStartDate = timezone.now().strftime('%Y-%m-%d')
            qb_item.Type = "Inventory"
            qb_item.QtyOnHand = product.inventory.salable()

            qb_item.AssetAccountRef = asset_accounts[0].to_ref()
            qb_item.ExpenseAccountRef = expense_accounts[0].to_ref()
            qb_item.IncomeAccountRef = income_accounts[0].to_ref()

            qb_item.save(qb=self.api)
            return qb_item

        qb_item = items[0]
        return qb_item
