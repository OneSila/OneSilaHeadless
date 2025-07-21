from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin
from .models import WoocommerceSalesChannel, \
    WoocommerceGlobalAttribute, WoocommerceGlobalAttributeValue, \
    WoocommerceProduct, WoocommerceMediaThroughProduct


@admin.register(WoocommerceSalesChannel)
class WoocommerceSalesChannelAdmin(PolymorphicChildModelAdmin):
    base_model = WoocommerceSalesChannel
    list_display = ('hostname', 'active')
    search_fields = ('hostname',)
    list_filter = ('active',)

    fieldsets = (
        (None, {
            'fields': ('hostname', 'active', 'verify_ssl', 'multi_tenant_company')
        }),
        ('WooCommerce API Settings', {
            'fields': ('api_key', 'api_secret', 'api_version')
        }),
        ('Synchronization Settings', {
            'fields': ('use_configurable_name', 'sync_contents', 'sync_ean_codes',
                      'sync_prices', 'import_orders', 'first_import_complete',
                      'is_importing', 'requests_per_minute', 'max_retries')
        }),
    )


@admin.register(WoocommerceGlobalAttribute)
class WoocommerceGlobalAttributeAdmin(admin.ModelAdmin):
    # base_model = WoocommerceGlobalAttribute
    list_display = ('get_name', 'remote_id')
    search_fields = ('get_name', 'remote_id')
    list_filter = ('sales_channel',)

    def get_name(self, obj):
        return obj.local_instance.name


@admin.register(WoocommerceGlobalAttributeValue)
class WoocommerceGlobalAttributeValueAdmin(admin.ModelAdmin):
    # base_model = WoocommerceGlobalAttributeValue
    list_display = ('get_value', 'remote_id')
    search_fields = ('get_value', 'remote_id')
    list_filter = ('sales_channel',)

    def get_value(self, obj):
        return obj.local_instance.value


@admin.register(WoocommerceProduct)
class WoocommerceProductAdmin(admin.ModelAdmin):
    list_filter = ('sales_channel',)
    list_display = ('local_instance', 'local_instance__sku', 'remote_id', 'is_variation')


@admin.register(WoocommerceMediaThroughProduct)
class WoocommerceMediaThroughProductAdmin(admin.ModelAdmin):
    pass
