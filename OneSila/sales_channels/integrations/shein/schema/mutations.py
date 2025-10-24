"""GraphQL mutation mixins for the Shein integration."""

from strawberry import Info
import strawberry_django

from django.utils.translation import gettext_lazy as _
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.mutations import List, create, type, update
from sales_channels.integrations.shein.schema.types.input import (
    SheinSalesChannelInput,
    SheinSalesChannelPartialInput,
    SheinValidateAuthInput,
)
from sales_channels.integrations.shein.schema.types.types import (
    SheinRedirectUrlType,
    SheinSalesChannelType,
)


@type(name="Mutation")
class SheinSalesChannelMutation:
    """Expose create/update helpers and OAuth entry-points for Shein."""

    create_shein_sales_channel: SheinSalesChannelType = create(SheinSalesChannelInput)
    create_shein_sales_channels: List[SheinSalesChannelType] = create(SheinSalesChannelInput)

    update_shein_sales_channel: SheinSalesChannelType = update(SheinSalesChannelPartialInput)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def get_shein_redirect_url(
        self,
        instance: SheinSalesChannelPartialInput,
        info: Info,
    ) -> SheinRedirectUrlType:
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.shein.factories.sales_channels.oauth import (
            GetSheinRedirectUrlFactory,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = SheinSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        factory = GetSheinRedirectUrlFactory(sales_channel=sales_channel)
        factory.run()

        return SheinRedirectUrlType(redirect_url=factory.redirect_url)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def validate_shein_auth(
        self,
        instance: SheinValidateAuthInput,
        info: Info,
    ) -> SheinSalesChannelType:
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.shein.factories.sales_channels.oauth import (
            ValidateSheinAuthFactory,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        try:
            sales_channel = SheinSalesChannel.objects.get(
                state=instance.state,
                multi_tenant_company=multi_tenant_company,
            )
        except SheinSalesChannel.DoesNotExist as exc:  # pragma: no cover - guard path
            raise ValueError(
                _("Could not find Shein integration for the provided state.")
            ) from exc

        factory = ValidateSheinAuthFactory(
            sales_channel=sales_channel,
            app_id=instance.app_id,
            temp_token=instance.temp_token,
            state=instance.state,
        )
        factory.run()

        return sales_channel
