from sales_channels.integrations.shopify.schema.types.input import ShopifySalesChannelInput, \
    ShopifySalesChannelPartialInput, ShopifyValidateAuthInput
from sales_channels.integrations.shopify.schema.types.types import ShopifySalesChannelType, ShopifyRedirectUrlType
from core.schema.core.mutations import create, type, List, update
import strawberry_django
from strawberry import Info
from core.schema.core.extensions import default_extensions
from core.schema.core.mutations import type
from core.schema.core.helpers import get_multi_tenant_company


@type(name="Mutation")
class ShopifySalesChannelMutation:
    create_shopify_sales_channel: ShopifySalesChannelType = create(ShopifySalesChannelInput)
    create_shopify_sales_channels: List[ShopifySalesChannelType] = create(ShopifySalesChannelInput)

    update_shopify_sales_channel: ShopifySalesChannelType = update(ShopifySalesChannelPartialInput)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def get_shopify_redirect_url(
        self, instance: ShopifySalesChannelPartialInput, info: Info
    ) -> ShopifyRedirectUrlType:
        from sales_channels.integrations.shopify.models import ShopifySalesChannel
        from sales_channels.integrations.shopify.factories.sales_channels.oauth import GetShopifyRedirectUrlFactory

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = ShopifySalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company
        )

        factory = GetShopifyRedirectUrlFactory(sales_channel=sales_channel)
        factory.run()

        return ShopifyRedirectUrlType(redirect_url=factory.redirect_url)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def validate_shopify_auth(
            self, instance: ShopifyValidateAuthInput, info: Info
    ) -> ShopifySalesChannelType:
        from sales_channels.integrations.shopify.models import ShopifySalesChannel
        from sales_channels.integrations.shopify.factories.sales_channels.oauth import ValidateShopifyAuthFactory

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = ShopifySalesChannel.objects.get(
            state=instance.state,
            multi_tenant_company=multi_tenant_company
        )

        factory = ValidateShopifyAuthFactory(
            sales_channel=sales_channel,
            shop=instance.shop,
            code=instance.code,
            hmac=instance.hmac,
            timestamp=instance.timestamp,
            host=instance.host,
        )
        factory.run()

        return sales_channel
