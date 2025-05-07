from django.contrib import admin
from .models import WoocommerceSalesChannel, WoocommerceProduct


@admin.register(WoocommerceSalesChannel)
class WoocommerceSalesChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_url', 'is_active')
    search_fields = ('name', 'api_url')
    list_filter = ('is_active',)


@admin.register(WoocommerceProduct)
class WoocommerceProductAdmin(admin.ModelAdmin):
    list_display = ('remote_id', 'product', 'sales_channel')
    search_fields = ('remote_id', 'product__name')
    list_filter = ('sales_channel',)
    raw_id_fields = ('product', 'sales_channel')
