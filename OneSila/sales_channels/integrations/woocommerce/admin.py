from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin
from .models import WoocommerceSalesChannel, \
    WoocommerceGlobalAttribute, WoocommerceGlobalAttributeValue, \
    WoocommerceProduct


@admin.register(WoocommerceSalesChannel)
class WoocommerceSalesChannelAdmin(PolymorphicChildModelAdmin):
    base_model = WoocommerceSalesChannel
    list_display = ('hostname', 'api_url', 'active')
    search_fields = ('hostname', 'api_url')
    list_filter = ('active',)

    fieldsets = (
        (None, {
            'fields': ('hostname', 'active', 'verify_ssl', 'multi_tenant_company')
        }),
        ('WooCommerce API Settings', {
            'fields': ('api_url', 'api_key', 'api_secret', 'api_version')
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
    list_display = ('get_name', 'get_sku')
    search_fields = ('get_name', 'get_sku')
    list_filter = ('sales_channel',)

    def get_name(self, obj):
        return obj.local_instance.name

    def get_sku(self, obj):
        return obj.local_instance.sku
