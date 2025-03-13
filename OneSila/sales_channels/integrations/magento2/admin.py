from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin

from .models import MagentoSalesChannel, MagentoProperty, MagentoPropertySelectValue, MagentoSalesChannelView, MagentoOrder, MagentoOrderItem, \
    MagentoProduct, MagentoProductProperty, MagentoImageProductAssociation, MagentoProductContent
from .models.products import MagentoEanCode
from .models.properties import MagentoAttributeSet, MagentoAttributeSetAttribute
from .models.sales_channels import MagentoRemoteLanguage
from .models.taxes import MagentoCurrency
from ...models import SalesChannelViewAssign

@admin.register(MagentoSalesChannel)
class MagentoSalesChannelAdmin(PolymorphicChildModelAdmin):
    base_model = MagentoSalesChannel
    list_display = ('hostname', 'authentication_method', 'active')
    list_filter = ('active', 'authentication_method')
    search_fields = ('hostname', 'host_api_username')
    ordering = ('hostname',)

    fieldsets = (
        (None, {
            'fields': ('hostname', 'active', 'verify_ssl', 'authentication_method', 'host_api_username', 'host_api_key', 'multi_tenant_company')
        }),
        ('Magento Settings', {
            'fields': ('attribute_set_skeleton_id', 'use_configurable_name', 'sync_contents', 'sync_ean_codes', 'sync_prices', 'requests_per_minute', 'max_retries')
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

@admin.register(SalesChannelViewAssign)
class SalesChannelViewAssignAdmin(admin.ModelAdmin):
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

@admin.register(MagentoProduct)
class MagentoProductAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoProductContent)
class MagentoProductContentAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoEanCode)
class MagentoEanCodeAdmin(admin.ModelAdmin):
    pass

@admin.register(MagentoImageProductAssociation)
class MagentoImageProductAssociationAdmin(admin.ModelAdmin):
    pass