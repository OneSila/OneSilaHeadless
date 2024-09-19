from django.contrib import admin
from .models import MagentoSalesChannel, MagentoProperty, MagentoPropertySelectValue, MagentoSalesChannelView, MagentoOrder, MagentoCustomer, MagentoOrderItem, \
    MagentoProduct, MagentoSalesChannelViewAssign, MagentoProductProperty
from .models.properties import MagentoAttributeSet, MagentoAttributeSetAttribute
from .models.sales_channels import MagentoRemoteLanguage
from .models.taxes import MagentoCurrency


@admin.register(MagentoSalesChannel)
class MagentoSalesChannelAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'authentication_method', 'active')
    list_filter = ('active', 'authentication_method')
    search_fields = ('hostname', 'host_api_username')
    ordering = ('hostname',)

    fieldsets = (
        (None, {
            'fields': ('hostname', 'active', 'verify_ssl', 'authentication_method', 'host_api_username', 'host_api_key', 'multi_tenant_company')
        }),
        ('Magento Settings', {
            'fields': ('always_use_configurable_name', 'sync_contents')
        }),
    )


@admin.register(MagentoProperty)
class MagentoPropertyAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoPropertySelectValue)
class MagentoPropertySelectValueAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoProductProperty)
class MagentoProductPropertyAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoSalesChannelView)
class MagentoSalesChannelViewAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoSalesChannelViewAssign)
class MagentoSalesChannelViewAssignAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoRemoteLanguage)
class MagentoRemoteLanguageAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoCurrency)
class MagentoCurrencyAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoAttributeSet)
class MagentoAttributeSetAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoAttributeSetAttribute)
class MagentoAttributeSetAttributeAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoOrder)
class MagentoOrderAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoOrderItem)
class MagentoOrderAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoCustomer)
class MagentoCustomerAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoProduct)
class MagentoProductAdmin(admin.ModelAdmin):
    pass