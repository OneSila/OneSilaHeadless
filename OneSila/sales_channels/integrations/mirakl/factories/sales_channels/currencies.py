from sales_channels.factories.mixins import LocalCurrencyMappingMixin, PullRemoteInstanceMixin
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import MiraklRemoteCurrency


class MiraklRemoteCurrencyPullFactory(GetMiraklAPIMixin, LocalCurrencyMappingMixin, PullRemoteInstanceMixin):
    """Pull Mirakl currencies."""

    remote_model_class = MiraklRemoteCurrency
    field_mapping = {
        "remote_code": "code",
        "label": "label",
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ["remote_code"]

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        response = self.mirakl_get(path="/api/currencies")
        account_info = self.get_account_info()
        default_currency = str(account_info.get("currency_iso_code") or "").strip()

        currencies = response.get("currencies") or []
        self.remote_instances = [currency for currency in currencies if isinstance(currency, dict)]
        for currency in self.remote_instances:
            currency["is_default"] = str(currency.get("code") or "").strip() == default_currency

        self.add_local_currency()

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        super().create_remote_instance_mirror(remote_data, remote_instance_mirror)
        remote_instance_mirror.label = remote_data.get("label", "")
        remote_instance_mirror.is_default = bool(remote_data.get("is_default"))
        remote_instance_mirror.raw_data = remote_data or {}
        remote_instance_mirror.save(update_fields=["label", "is_default", "raw_data"])

    def add_fields_to_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        update_fields = []
        for field_name, value in {
            "label": remote_data.get("label", ""),
            "is_default": bool(remote_data.get("is_default")),
            "raw_data": remote_data or {},
        }.items():
            if getattr(remote_instance_mirror, field_name) != value:
                setattr(remote_instance_mirror, field_name, value)
                update_fields.append(field_name)
        if update_fields:
            remote_instance_mirror.save(update_fields=update_fields)
