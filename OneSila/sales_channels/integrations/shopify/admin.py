from django.contrib import admin
from sales_channels.integrations.shopify.models import ShopifySalesChannelView, ShopifyProduct, ShopifySalesChannel, \
    ShopifyProductProperty, ShopifyImageProductAssociation
from core.admin import ModelAdmin
from sales_channels.admin import SalesChannelRemoteAdmin, SalesChannelRemoteProductAdmin


@admin.register(ShopifySalesChannel)
class ShopifySalesChannelAdmin(ModelAdmin):
    pass


@admin.register(ShopifySalesChannelView)
class ShopifySalesChannelViewAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(ShopifyProduct)
class ShopifyProductAdmin(SalesChannelRemoteProductAdmin):
    raw_id_fields = (
        'local_instance',
        'remote_parent_product',
        'sales_channel',
        'created_by_multi_tenant_user',
        'last_update_by_multi_tenant_user',
    )


@admin.register(ShopifyProductProperty)
class ShopifyProductPropertyAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(ShopifyImageProductAssociation)
class ShopifyImageProductAssociationAdmin(SalesChannelRemoteAdmin):
    pass
