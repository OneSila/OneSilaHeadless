from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin
from core.admin import ModelAdmin
from .models import MagentoSalesChannel, MagentoProperty, MagentoPropertySelectValue, MagentoSalesChannelView, MagentoOrder, MagentoOrderItem, \
    MagentoProduct, MagentoProductProperty, MagentoImageProductAssociation, MagentoProductContent
from .models.products import MagentoEanCode, MagentoPrice
from .models.properties import MagentoAttributeSet, MagentoAttributeSetAttribute
from .models.sales_channels import MagentoRemoteLanguage
from .models.taxes import MagentoCurrency, MagentoTaxClass
from ...models import SalesChannelViewAssign
from sales_channels.admin import SalesChannelRemoteAdmin, SalesChannelRemoteProductAdmin


@admin.register(MagentoSalesChannel)
class MagentoSalesChannelAdmin(PolymorphicChildModelAdmin):
    base_model = MagentoSalesChannel
    list_display = ('hostname', 'authentication_method', 'active')
    list_filter = ('active', 'authentication_method')
    search_fields = ('hostname', 'host_api_username')
    ordering = ('hostname',)

    fieldsets = (
        (None, {
            'fields': ('hostname', 'active', 'verify_ssl', 'authentication_method', 'host_api_username', 'host_api_key', 'first_import_complete', 'is_importing', 'multi_tenant_company')
        }),
        ('Magento Settings', {
            'fields': ('attribute_set_skeleton_id', 'use_configurable_name', 'sync_contents', 'sync_ean_codes', 'sync_prices', 'import_orders', 'requests_per_minute', 'max_retries')
        }),
    )


@admin.register(MagentoProperty)
class MagentoPropertyAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoPropertySelectValue)
class MagentoPropertySelectValueAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoProductProperty)
class MagentoProductPropertyAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoSalesChannelView)
class MagentoSalesChannelViewAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(SalesChannelViewAssign)
class SalesChannelViewAssignAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoRemoteLanguage)
class MagentoRemoteLanguageAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoCurrency)
class MagentoCurrencyAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoAttributeSet)
class MagentoAttributeSetAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoAttributeSetAttribute)
class MagentoAttributeSetAttributeAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoOrder)
class MagentoOrderAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoOrderItem)
class MagentoOrderAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoProduct)
class MagentoProductAdmin(SalesChannelRemoteProductAdmin):
    pass


@admin.register(MagentoProductContent)
class MagentoProductContentAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoPrice)
class MagentoPriceAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoEanCode)
class MagentoEanCodeAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoImageProductAssociation)
class MagentoImageProductAssociationAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(MagentoTaxClass)
class MagentoTaxClassAdmin(SalesChannelRemoteAdmin):
    pass
