from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import EbaySalesChannelView


class EbaySalesChannelViewPullFactory(GetEbayAPIMixin, PullRemoteInstanceMixin):
    """Pull eBay marketplaces as sales channel views."""

    remote_model_class = EbaySalesChannelView
    field_mapping = {
        'remote_id': 'marketplace_id',
        'name': 'name',
        'url': 'url',
        'is_default': 'is_default',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['remote_id']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        self.remote_instances = []
        try:
            subscription_marketplace_ids = self.get_subscription_marketplace_ids()
        except Exception:
            subscription_marketplace_ids = None
        if isinstance(subscription_marketplace_ids, list):
            marketplaces = list(dict.fromkeys(subscription_marketplace_ids))
        else:
            marketplaces = self.get_marketplace_ids()
        try:
            default_marketplace = self.get_default_marketplace_id()
        except:
            # for this api sometimes we get
            # There was a problem with an eBay internal system or process. Contact eBay developer support for assistance
            # and this can manually be set so we can ignore it for now
            default_marketplace = None

        reference = self.marketplace_reference()
        merchant_location_choices = self._get_merchant_location_choices()

        for marketplace_id in marketplaces:
            info = reference.get(marketplace_id)

            if not info:
                continue

            name = info[0]
            languages = info[1]
            url = next(iter(languages.values()))[0] if languages else ""
            fulfillment_policy_choices = self._get_fulfillment_policy_choices(marketplace_id)
            payment_policy_choices = self._get_payment_policy_choices(marketplace_id)
            return_policy_choices = self._get_return_policy_choices(marketplace_id)
            default_category_tree_id = self._get_default_category_tree_id(marketplace_id)
            self.remote_instances.append({
                "marketplace_id": marketplace_id,
                "name": name,
                "url": url,
                "is_default": marketplace_id == default_marketplace,
                "fulfillment_policy_choices": fulfillment_policy_choices,
                "payment_policy_choices": payment_policy_choices,
                "return_policy_choices": return_policy_choices,
                "merchant_location_choices": merchant_location_choices,
                "default_category_tree_id": default_category_tree_id,
            })

    def serialize_response(self, response):
        return response

    def _get_policy_choices(self, endpoint, result_key, marketplace_id, value_key):
        try:
            response = self._request_account_policy(endpoint, marketplace_id)
        except Exception:
            return []

        if not isinstance(response, dict):
            return []

        policies = response.get(result_key, [])
        if not isinstance(policies, list):
            return []

        choices = []
        for policy in policies:
            if not isinstance(policy, dict):
                continue
            if policy.get("marketplaceId") != marketplace_id:
                continue

            value = policy.get(value_key)
            if not value:
                continue

            label = policy.get("name") or value
            choices.append({"label": label, "value": value})

        return choices

    def _get_fulfillment_policy_choices(self, marketplace_id):
        return self._get_policy_choices(
            "fulfillment_policy", "fulfillmentPolicies", marketplace_id, "fulfillmentPolicyId"
        )

    def _get_payment_policy_choices(self, marketplace_id):
        return self._get_policy_choices(
            "payment_policy", "paymentPolicies", marketplace_id, "paymentPolicyId"
        )

    def _get_return_policy_choices(self, marketplace_id):
        return self._get_policy_choices(
            "return_policy", "returnPolicies", marketplace_id, "returnPolicyId"
        )

    def _get_merchant_location_choices(self):
        try:
            response = self.api.sell_inventory_get_inventory_locations()
        except Exception:
            return []

        if response is None:
            return []

        if isinstance(response, dict):
            response_items = [response]
        else:
            try:
                response_items = list(response)
            except TypeError:
                response_items = []

        choices = []
        for entry in response_items:
            if not isinstance(entry, dict):
                continue
            record = entry.get("record")
            if not isinstance(record, dict):
                continue

            merchant_location_key = record.get("merchant_location_key")
            if not merchant_location_key:
                continue

            location = record.get("location", {})
            address = location.get("address", {}) if isinstance(location, dict) else {}
            if not isinstance(address, dict):
                address = {}

            address_parts = []
            for key in (
                "address_line1",
                "address_line2",
                "city",
                "country",
                "county",
                "postal_code",
                "state_or_province",
            ):
                value = address.get(key)
                if value:
                    address_parts.append(value)

            label = ", ".join(address_parts) if address_parts else merchant_location_key
            choices.append({"label": label, "value": merchant_location_key})

        return choices

    def _get_default_category_tree_id(self, marketplace_id):
        try:
            response = self.api.commerce_taxonomy_get_default_category_tree_id(marketplace_id)
        except Exception:
            return None

        if isinstance(response, dict):
            return response.get("category_tree_id")

        return None

    def process_remote_instance(self, remote_data, remote_instance_mirror, created):
        updated_fields = []
        for field in [
            "fulfillment_policy_choices",
            "payment_policy_choices",
            "return_policy_choices",
            "merchant_location_choices",
            "default_category_tree_id",
        ]:
            if field not in remote_data:
                continue

            value = remote_data.get(field)

            if getattr(remote_instance_mirror, field) != value:
                setattr(remote_instance_mirror, field, value)
                updated_fields.append(field)

        if updated_fields:
            remote_instance_mirror.save(update_fields=updated_fields)
