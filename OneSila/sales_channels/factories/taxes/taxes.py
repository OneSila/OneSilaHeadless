from sales_channels.factories.mixins import RemoteInstanceCreateFactory, RemoteInstanceUpdateFactory
from taxes.models import VatRate


class RemoteVatRateCreateFactory(RemoteInstanceCreateFactory):
    local_model_class = VatRate


class RemoteVatRateUpdateFactory(RemoteInstanceUpdateFactory):
    local_model_class = VatRate
    create_if_not_exists = True
