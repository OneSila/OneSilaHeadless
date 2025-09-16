from django.core.exceptions import ValidationError

from sales_channels.integrations.ebay.schema.types.input import (
    EbaySalesChannelInput,
    EbaySalesChannelPartialInput,
    EbayValidateAuthInput,
    EbayPropertyPartialInput,
    EbaySalesChannelViewPartialInput,
)
from sales_channels.integrations.ebay.schema.types.types import (
    EbaySalesChannelType,
    EbayRedirectUrlType,
    EbayPropertyType,
    EbaySalesChannelViewType,
)
from core.schema.core.mutations import create, type, List, update
from strawberry import Info
import strawberry_django
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from django.utils.translation import gettext_lazy as _


@type(name="Mutation")
class EbaySalesChannelMutation:
    create_ebay_sales_channel: EbaySalesChannelType = create(EbaySalesChannelInput)
    create_ebay_sales_channels: List[EbaySalesChannelType] = create(EbaySalesChannelInput)

    update_ebay_sales_channel: EbaySalesChannelType = update(EbaySalesChannelPartialInput)

    update_ebay_property: EbayPropertyType = update(EbayPropertyPartialInput)
    # update_ebay_property_select_value: EbayPropertySelectValueType = update(EbayPropertySelectValuePartialInput)
    update_ebay_sales_channel_view: EbaySalesChannelViewType = update(EbaySalesChannelViewPartialInput)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def get_ebay_redirect_url(self, instance: EbaySalesChannelPartialInput, info: Info) -> EbayRedirectUrlType:
        from sales_channels.integrations.ebay.models import EbaySalesChannel
        from sales_channels.integrations.ebay.factories.sales_channels.oauth import GetEbayRedirectUrlFactory

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = EbaySalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company
        )

        factory = GetEbayRedirectUrlFactory(sales_channel=sales_channel)
        factory.run()

        return EbayRedirectUrlType(redirect_url=factory.redirect_url)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def validate_ebay_auth(self, instance: EbayValidateAuthInput, info: Info) -> EbaySalesChannelType:
        from sales_channels.integrations.ebay.models import EbaySalesChannel
        from sales_channels.integrations.ebay.factories.sales_channels.oauth import ValidateEbayAuthFactory

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        try:
            sales_channel = EbaySalesChannel.objects.get(
                state=instance.state,
                multi_tenant_company=multi_tenant_company
            )
        except EbaySalesChannel.DoesNotExist:
            raise ValidationError(_("Could not find eBay integration. Please restart the authorization process."))

        factory = ValidateEbayAuthFactory(
            sales_channel=sales_channel,
            code=instance.code,
        )
        factory.run()

        return sales_channel
