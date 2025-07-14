from django.core.exceptions import ValidationError
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin

from sales_channels.integrations.amazon.schema.types.input import (
    AmazonSalesChannelInput,
    AmazonSalesChannelPartialInput,
    AmazonPropertyInput,
    AmazonPropertyPartialInput,
    AmazonPropertySelectValueInput,
    AmazonPropertySelectValuePartialInput,
    AmazonProductTypeInput,
    AmazonProductTypePartialInput,
    AmazonProductTypeItemInput,
    AmazonProductTypeItemPartialInput,
    AmazonSalesChannelImportInput,
    AmazonSalesChannelImportPartialInput,
    AmazonDefaultUnitConfiguratorPartialInput,
    AmazonValidateAuthInput,
    BulkAmazonPropertySelectValueLocalInstanceInput,
)
from sales_channels.integrations.amazon.schema.types.types import (
    AmazonSalesChannelType,
    AmazonPropertyType,
    AmazonPropertySelectValueType,
    AmazonProductTypeType,
    AmazonProductTypeItemType,
    AmazonRedirectUrlType,
    AmazonSalesChannelImportType,
    AmazonDefaultUnitConfiguratorType,
    SuggestedAmazonProductType, SuggestedAmazonProductTypeEntry,
)
from sales_channels.schema.types.input import (
    SalesChannelViewAssignPartialInput,
    SalesChannelViewPartialInput,
)
from sales_channels.schema.types.types import SalesChannelViewAssignType
from core.schema.core.mutations import create, type, List, update, delete
from strawberry import Info
import strawberry_django
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from django.utils.translation import gettext_lazy as _


@type(name="Mutation")
class AmazonSalesChannelMutation:
    create_amazon_sales_channel: AmazonSalesChannelType = create(AmazonSalesChannelInput)
    create_amazon_sales_channels: List[AmazonSalesChannelType] = create(AmazonSalesChannelInput)

    update_amazon_sales_channel: AmazonSalesChannelType = update(AmazonSalesChannelPartialInput)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def get_amazon_redirect_url(self, instance: AmazonSalesChannelPartialInput, info: Info) -> AmazonRedirectUrlType:
        from sales_channels.integrations.amazon.models import AmazonSalesChannel
        from sales_channels.integrations.amazon.factories.sales_channels.oauth import GetAmazonRedirectUrlFactory

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = AmazonSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company
        )

        factory = GetAmazonRedirectUrlFactory(sales_channel=sales_channel)
        factory.run()

        return AmazonRedirectUrlType(redirect_url=factory.redirect_url)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def validate_amazon_auth(self, instance: AmazonValidateAuthInput, info: Info) -> AmazonSalesChannelType:
        from sales_channels.integrations.amazon.models import AmazonSalesChannel
        from sales_channels.integrations.amazon.factories.sales_channels.oauth import ValidateAmazonAuthFactory

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        try:
            sales_channel = AmazonSalesChannel.objects.get(
                state=instance.state,
                multi_tenant_company=multi_tenant_company
            )
        except AmazonSalesChannel.DoesNotExist:
            raise ValidationError(_("Could not find Amazon integration. Please restart the authorization process."))

        factory = ValidateAmazonAuthFactory(
            sales_channel=sales_channel,
            code=instance.spapi_oauth_code,
            selling_partner_id=instance.selling_partner_id,
        )
        factory.run()

        return sales_channel

    update_amazon_property: AmazonPropertyType = update(AmazonPropertyPartialInput)
    update_amazon_property_select_value: AmazonPropertySelectValueType = update(AmazonPropertySelectValuePartialInput)
    update_amazon_product_type: AmazonProductTypeType = update(AmazonProductTypePartialInput)
    update_amazon_product_type_item: AmazonProductTypeItemType = update(AmazonProductTypeItemPartialInput)

    update_amazon_default_unit_configurator: AmazonDefaultUnitConfiguratorType = update(AmazonDefaultUnitConfiguratorPartialInput)

    create_amazon_import_process: AmazonSalesChannelImportType = create(AmazonSalesChannelImportInput)
    update_amazon_import_process: AmazonSalesChannelImportType = update(AmazonSalesChannelImportPartialInput)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def bulk_update_amazon_property_select_value_local_instance(
        self,
        instance: BulkAmazonPropertySelectValueLocalInstanceInput,
        info: Info,
    ) -> List[AmazonPropertySelectValueType]:
        from sales_channels.integrations.amazon.models import AmazonPropertySelectValue
        from properties.models import PropertySelectValue

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        local_instance = None
        if instance.local_instance_id:
            local_instance = PropertySelectValue.objects.get(
                id=instance.local_instance_id.node_id,
                multi_tenant_company=multi_tenant_company,
            )

        value_ids = [gid.node_id for gid in instance.ids]

        values = list(
            AmazonPropertySelectValue.objects.filter(
                id__in=value_ids,
                multi_tenant_company=multi_tenant_company,
            )
        )

        for value in values:
            value.local_instance = local_instance
            value.save()

        return values

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def refresh_amazon_latest_issues(
        self, instance: SalesChannelViewAssignPartialInput, info: Info
    ) -> SalesChannelViewAssignType:
        """Refresh listing issues for a specific Amazon listing."""
        from sales_channels.models import SalesChannelViewAssign
        from sales_channels.integrations.amazon.factories.sales_channels.issues import (
            RefreshLatestIssuesFactory,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        assign = SalesChannelViewAssign.objects.select_related(
            "remote_product", "sales_channel_view", "sales_channel"
        ).get(
            id=instance.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )

        factory = RefreshLatestIssuesFactory(assign=assign)
        factory.run()

        return assign

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def suggest_amazon_product_type(
        self,
        name: str,
        marketplace: SalesChannelViewPartialInput,
        info: Info,
    ) -> SuggestedAmazonProductType:
        """Return suggested product types for a given name and marketplace."""
        from sales_channels.models import SalesChannelView

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        view = SalesChannelView.objects.select_related("sales_channel").get(
            id=marketplace.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )

        class _Client(GetAmazonAPIMixin):
            pass

        client = _Client()
        client.sales_channel = view.sales_channel.get_real_instance()

        data = client.search_product_types(view.remote_id, name) or {}

        product_types = [
            SuggestedAmazonProductTypeEntry(
                display_name=pt.get("display_name"),
                marketplace_ids=pt.get("marketplace_ids", []),
                name=pt.get("name"),
            )
            for pt in data.get("product_types", [])
        ]

        return SuggestedAmazonProductType(
            product_type_version=data.get("product_type_version", ""),
            product_types=product_types,
        )
