from django.contrib import admin
from sales_channels.integrations.shopify.models import ShopifySalesChannelView, ShopifyProduct, ShopifySalesChannel, \
    ShopifyProductProperty, ShopifyImageProductAssociation


@admin.register(ShopifySalesChannelView)
class ShopifySalesChannelViewAdmin(admin.ModelAdmin):
    pass


@admin.register(ShopifyProduct)
class ShopifyProductAdmin(admin.ModelAdmin):
    pass


@admin.register(ShopifyProductProperty)
class ShopifyProductPropertyAdmin(admin.ModelAdmin):
    pass


@admin.register(ShopifySalesChannel)
class ShopifySalesChannelAdmin(admin.ModelAdmin):
    pass


@admin.register(ShopifyImageProductAssociation)
class ShopifyImageProductAssociationAdmin(admin.ModelAdmin):
    pass
