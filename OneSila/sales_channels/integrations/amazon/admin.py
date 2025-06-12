from django.contrib import admin
from sales_channels.admin import SalesChannelRemoteAdmin, SalesChannelRemoteProductAdmin
from polymorphic.admin import PolymorphicChildModelAdmin
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductProperty,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
    AmazonCurrency,
    AmazonOrder,
    AmazonOrderItem,
    AmazonProduct,
    AmazonProductContent,
    AmazonPrice,
    AmazonEanCode,
    AmazonImageProductAssociation,
    AmazonVat,
)
from sales_channels.models import SalesChannelViewAssign

@admin.register(AmazonSalesChannel)
class AmazonSalesChannelAdmin(PolymorphicChildModelAdmin):
    base_model = AmazonSalesChannel
    list_display = ('hostname', 'region', 'active')
    list_filter = ('active', 'region')
    search_fields = ('hostname',)
    ordering = ('hostname',)

    fieldsets = (
        (None, {
            'fields': ('hostname', 'active', 'verify_ssl', 'region', 'refresh_token', 'first_import_complete', 'is_importing', 'multi_tenant_company')
        }),
        ('Amazon Settings', {
            'fields': ('use_configurable_name', 'sync_contents', 'sync_ean_codes', 'sync_prices', 'import_orders', 'requests_per_minute', 'max_retries')
        }),
    )

@admin.register(AmazonProperty)
class AmazonPropertyAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonPropertySelectValue)
class AmazonPropertySelectValueAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonProductProperty)
class AmazonProductPropertyAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonSalesChannelView)
class AmazonSalesChannelViewAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonRemoteLanguage)
class AmazonRemoteLanguageAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonCurrency)
class AmazonCurrencyAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonProductType)
class AmazonProductTypeAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonProductTypeItem)
class AmazonProductTypeItemAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonOrder)
class AmazonOrderAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonOrderItem)
class AmazonOrderItemAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonProduct)
class AmazonProductAdmin(SalesChannelRemoteProductAdmin):
    pass

@admin.register(AmazonProductContent)
class AmazonProductContentAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonPrice)
class AmazonPriceAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonEanCode)
class AmazonEanCodeAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonImageProductAssociation)
class AmazonImageProductAssociationAdmin(SalesChannelRemoteAdmin):
    pass

@admin.register(AmazonVat)
class AmazonVatAdmin(SalesChannelRemoteAdmin):
    pass