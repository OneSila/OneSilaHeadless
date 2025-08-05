from django.core.exceptions import ValidationError
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin

from sales_channels.integrations.amazon.schema.types.input import (
    AmazonSalesChannelInput,
    AmazonSalesChannelPartialInput,
    AmazonPropertyInput,
    AmazonPropertyPartialInput,
    AmazonPropertySelectValueInput,
    AmazonPropertySelectValuePartialInput,
    AmazonProductPartialInput,
    AmazonProductTypeInput,
    AmazonProductTypePartialInput,
    AmazonProductTypeItemInput,
    AmazonProductTypeItemPartialInput,
    AmazonSalesChannelImportInput,
    AmazonSalesChannelImportPartialInput,
    AmazonDefaultUnitConfiguratorPartialInput,
    AmazonSalesChannelViewPartialInput,
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
    AmazonSalesChannelViewType,
    AmazonProductType as AmazonProductGraphqlType,
    SuggestedAmazonProductType, SuggestedAmazonProductTypeEntry,
)
from sales_channels.schema.types.input import SalesChannelViewPartialInput
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

    update_amazon_sales_channel_view: AmazonSalesChannelViewType = update(AmazonSalesChannelViewPartialInput)

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
        self,
        remote_product: AmazonProductPartialInput,
        view: AmazonSalesChannelViewPartialInput,
        info: Info,
    ) -> AmazonProductGraphqlType:
        """Refresh listing issues for a specific Amazon product."""
        from sales_channels.integrations.amazon.models import (
            AmazonProduct,
            AmazonSalesChannelView,
        )
        from sales_channels.integrations.amazon.factories.sales_channels.issues import (
            FetchRemoteIssuesFactory,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        remote_product = AmazonProduct.objects.select_related("sales_channel").get(
            id=remote_product.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )

        view = AmazonSalesChannelView.objects.select_related("sales_channel").get(
            id=view.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )

        factory = FetchRemoteIssuesFactory(
            remote_product=remote_product,
            view=view,
        )
        factory.run()

        return remote_product

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def resync_amazon_product(
        self,
        remote_product: AmazonProductPartialInput,
        view: AmazonSalesChannelViewPartialInput,
        force_validation_only: bool,
        info: Info,
    ) -> AmazonProductGraphqlType:
        """Trigger a manual sync for an Amazon product."""
        from sales_channels.integrations.amazon.models import (
            AmazonProduct,
            AmazonSalesChannelView,
        )
        from sales_channels.signals import manual_sync_remote_product

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        remote_product = AmazonProduct.objects.select_related("sales_channel").get(
            id=remote_product.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )

        view = AmazonSalesChannelView.objects.select_related("sales_channel").get(
            id=view.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )

        if remote_product.syncing_current_percentage != 100:
            raise ValidationError(
                _("You can't resync the product because is currently syncing."),
            )

        manual_sync_remote_product.send(
            sender=remote_product.__class__,
            instance=remote_product,
            view=view,
            force_validation_only=force_validation_only,
        )

        return remote_product

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def suggest_amazon_product_type(
        self,
        name: str | None,
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

        data = client.search_product_types(view.remote_id, name)

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

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def create_amazon_product_types_from_local_rules(
        self,
        instance: AmazonSalesChannelPartialInput,
        info: Info,
    ) -> List[AmazonProductTypeType]:
        """Create Amazon product types for all local rules on a given sales channel."""
        from sales_channels.integrations.amazon.models import (
            AmazonSalesChannel,
            AmazonProductType,
        )
        from properties.models import ProductPropertiesRule

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        sales_channel = AmazonSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        product_types: list[AmazonProductType] = []
        for rule in ProductPropertiesRule.objects.filter(
            multi_tenant_company=multi_tenant_company
        ).iterator():
            product_type, _ = AmazonProductType.objects.get_or_create_from_local_instance(
                local_instance=rule,
                sales_channel=sales_channel,
            )
            product_types.append(product_type)

        return product_types
