from core.schema.core.queries import field
from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin
from eancodes.models import EanCode
from products.schema.types.types import ProductType
from .filters import EanCodeFilter
from .ordering import EanCodeOrder


@type(EanCode, filters=EanCodeFilter, order=EanCodeOrder, pagination=True, fields="__all__")
class EanCodeType(relay.Node, GetQuerysetMultiTenantMixin):
    product: ProductType | None

    @field()
    def product_name(self, info) -> str | None:
        return self.product_name
