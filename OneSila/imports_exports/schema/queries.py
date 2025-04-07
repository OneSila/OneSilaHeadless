from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin
from imports_exports.models import Import
from imports_exports.schema.types.filters import ImportFilter
from imports_exports.schema.types.ordering import ImportOrder


@type(Import, filters=ImportFilter, order=ImportOrder, pagination=True, fields="__all__")
class ImportType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
