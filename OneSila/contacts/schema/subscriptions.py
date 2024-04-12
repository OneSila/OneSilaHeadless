from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from contacts.models import Company, Supplier, Customer, Influencer, InternalCompany, \
    Person, Address, ShippingAddress, InvoiceAddress, InternalShippingAddress
from .types.types import CompanyType, SupplierType, CustomerType, InfluencerType, \
    InternalCompanyType, PersonType, AddressType, ShippingAddressType, InvoiceAddressType, \
    InternalShippingAddressType

import logging
logger = logging.getLogger(__name__)


@type(name="Subscription")
class ContactsSubscription:
    # company: AsyncGenerator[CompanyType, None] = model_subscription_field(Company)

    @subscription
    async def company(self, info: Info, pk: str) -> AsyncGenerator[CompanyType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Company):
            yield i

    @subscription
    async def supplier(self, info: Info, pk: str) -> AsyncGenerator[SupplierType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Supplier):
            yield i

    @subscription
    async def customer(self, info: Info, pk: str) -> AsyncGenerator[CustomerType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Customer):
            yield i

    @subscription
    async def influencer(self, info: Info, pk: str) -> AsyncGenerator[InfluencerType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Influencer):
            yield i

    @subscription
    async def internal_company(self, info: Info, pk: str) -> AsyncGenerator[InternalCompanyType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=InternalCompany):
            yield i

    @subscription
    async def person(self, info: Info, pk: str) -> AsyncGenerator[PersonType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Person):
            yield i

    @subscription
    async def address(self, info: Info, pk: str) -> AsyncGenerator[AddressType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Address):
            yield i

    @subscription
    async def shipping_address(self, info: Info, pk: str) -> AsyncGenerator[ShippingAddressType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ShippingAddress):
            yield i

    @subscription
    async def invoice_address(self, info: Info, pk: str) -> AsyncGenerator[InvoiceAddressType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=InvoiceAddress):
            yield i

    @subscription
    async def internal_shipping_address(self, info: Info, pk: str) -> AsyncGenerator[InternalShippingAddressType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=InternalShippingAddress):
            yield i
