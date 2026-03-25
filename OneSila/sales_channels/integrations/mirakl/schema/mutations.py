from django.core.exceptions import ValidationError
from strawberry import Info
import strawberry_django

from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.mutations import List, create, delete, type, update
from sales_channels.integrations.mirakl.factories.sales_channels import ValidateMiraklCredentialsFactory
from sales_channels.integrations.mirakl.models import (
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelImport,
)
from sales_channels.schema.types.input import SalesChannelFeedPartialInput
from sales_channels.integrations.mirakl.schema.types.input import (
    MiraklCategoryPartialInput,
    MiraklDocumentTypePartialInput,
    MiraklProductCategoryInput,
    MiraklProductCategoryPartialInput,
    MiraklProductTypePartialInput,
    MiraklProductTypeItemPartialInput,
    MiraklPropertyPartialInput,
    MiraklPropertySelectValuePartialInput,
    MiraklRemoteCurrencyPartialInput,
    MiraklRemoteLanguagePartialInput,
    MiraklSalesChannelImportInput,
    MiraklSalesChannelImportPartialInput,
    MiraklSalesChannelInput,
    MiraklSalesChannelPartialInput,
    MiraklSalesChannelViewPartialInput,
)
from sales_channels.integrations.mirakl.schema.types.types import (
    MiraklCategoryType,
    MiraklDocumentTypeType,
    MiraklProductCategoryType,
    MiraklProductTypeType,
    MiraklProductTypeItemType,
    MiraklPropertySelectValueType,
    MiraklPropertyType,
    MiraklRemoteCurrencyType,
    MiraklRemoteLanguageType,
    MiraklSalesChannelType,
    MiraklSalesChannelFeedType,
    MiraklSalesChannelImportType,
    MiraklSalesChannelViewType,
)
from sales_channels.signals import refresh_website_pull_models


@type(name="Mutation")
class MiraklSalesChannelMutation:
    create_mirakl_sales_channel: MiraklSalesChannelType = create(MiraklSalesChannelInput)
    create_mirakl_sales_channels: List[MiraklSalesChannelType] = create(MiraklSalesChannelInput)
    create_mirakl_product_category: MiraklProductCategoryType = create(MiraklProductCategoryInput)
    update_mirakl_product_category: MiraklProductCategoryType = update(MiraklProductCategoryPartialInput)
    delete_mirakl_product_category: MiraklProductCategoryType = delete()

    update_mirakl_sales_channel: MiraklSalesChannelType = update(MiraklSalesChannelPartialInput)
    update_mirakl_sales_channel_view: MiraklSalesChannelViewType = update(MiraklSalesChannelViewPartialInput)
    update_mirakl_remote_currency: MiraklRemoteCurrencyType = update(MiraklRemoteCurrencyPartialInput)
    update_mirakl_remote_language: MiraklRemoteLanguageType = update(MiraklRemoteLanguagePartialInput)
    update_mirakl_product_type: MiraklProductTypeType = update(MiraklProductTypePartialInput)
    update_mirakl_document_type: MiraklDocumentTypeType = update(MiraklDocumentTypePartialInput)
    update_mirakl_property: MiraklPropertyType = update(MiraklPropertyPartialInput)
    update_mirakl_property_select_value: MiraklPropertySelectValueType = update(
        MiraklPropertySelectValuePartialInput,
    )
    update_mirakl_product_type_item: MiraklProductTypeItemType = update(MiraklProductTypeItemPartialInput)
    create_mirakl_import_process: MiraklSalesChannelImportType = create(MiraklSalesChannelImportInput)
    update_mirakl_import_process: MiraklSalesChannelImportType = update(MiraklSalesChannelImportPartialInput)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def validate_mirakl_credentials(
        self,
        instance: MiraklSalesChannelPartialInput,
        info: Info,
    ) -> MiraklSalesChannelType:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = MiraklSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        factory = ValidateMiraklCredentialsFactory(sales_channel=sales_channel)
        factory.run()
        refresh_website_pull_models.send(sender=sales_channel.__class__, instance=sales_channel)
        sales_channel.refresh_from_db()
        return sales_channel

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def refresh_mirakl_metadata(
        self,
        instance: MiraklSalesChannelPartialInput,
        info: Info,
    ) -> MiraklSalesChannelType:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = MiraklSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        if not sales_channel.active:
            raise ValidationError("Sales channel is not active.")

        refresh_website_pull_models.send(sender=sales_channel.__class__, instance=sales_channel)
        sales_channel.refresh_from_db()
        return sales_channel

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def resync_mirakl_feed(
        self,
        instance: SalesChannelFeedPartialInput,
        info: Info,
    ) -> MiraklSalesChannelFeedType:
        from sales_channels.integrations.mirakl.flows import resync_mirakl_feed

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        feed = MiraklSalesChannelFeed.objects.select_related("sales_channel").get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )
        return resync_mirakl_feed(feed_id=feed.id)
