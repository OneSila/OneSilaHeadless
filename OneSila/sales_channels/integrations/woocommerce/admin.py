from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin
from .models import WoocommerceSalesChannel


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
