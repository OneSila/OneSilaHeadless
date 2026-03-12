from django.core.exceptions import ValidationError
from strawberry import Info
import strawberry_django

from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.mutations import List, create, type, update
from sales_channels.integrations.mirakl.factories.sales_channels import ValidateMiraklCredentialsFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelImport
from sales_channels.schema.types.input import SalesChannelFeedPartialInput, SalesChannelImportPartialInput
from sales_channels.schema.types.types import SalesChannelFeedType
from sales_channels.integrations.mirakl.schema.types.input import (
    MiraklCategoryPartialInput,
    MiraklDocumentTypePartialInput,
    MiraklInternalPropertyOptionPartialInput,
    MiraklInternalPropertyPartialInput,
    MiraklProductCategoryInput,
    MiraklProductCategoryPartialInput,
    MiraklProductTypeItemPartialInput,
    MiraklPropertyApplicabilityPartialInput,
    MiraklPropertyPartialInput,
    MiraklPropertySelectValuePartialInput,
    MiraklRemoteCurrencyPartialInput,
    MiraklRemoteLanguagePartialInput,
    MiraklSalesChannelInput,
    MiraklSalesChannelPartialInput,
    MiraklSalesChannelViewPartialInput,
)
from sales_channels.integrations.mirakl.schema.types.types import (
    MiraklCategoryType,
    MiraklDocumentTypeType,
    MiraklInternalPropertyOptionType,
    MiraklInternalPropertyType,
    MiraklProductCategoryType,
    MiraklProductTypeItemType,
    MiraklPropertyApplicabilityType,
    MiraklPropertySelectValueType,
    MiraklPropertyType,
    MiraklRemoteCurrencyType,
    MiraklRemoteLanguageType,
    MiraklSalesChannelType,
    MiraklSalesChannelImportType,
    MiraklSalesChannelViewType,
)
from sales_channels.signals import refresh_website_pull_models


@type(name="Mutation")
class MiraklSalesChannelMutation:
    create_mirakl_sales_channel: MiraklSalesChannelType = create(MiraklSalesChannelInput)
    create_mirakl_sales_channels: List[MiraklSalesChannelType] = create(MiraklSalesChannelInput)
    create_mirakl_product_category: MiraklProductCategoryType = create(MiraklProductCategoryInput)

    update_mirakl_sales_channel: MiraklSalesChannelType = update(MiraklSalesChannelPartialInput)
    update_mirakl_sales_channel_view: MiraklSalesChannelViewType = update(MiraklSalesChannelViewPartialInput)
    update_mirakl_remote_currency: MiraklRemoteCurrencyType = update(MiraklRemoteCurrencyPartialInput)
    update_mirakl_remote_language: MiraklRemoteLanguageType = update(MiraklRemoteLanguagePartialInput)
    update_mirakl_internal_property: MiraklInternalPropertyType = update(MiraklInternalPropertyPartialInput)
    update_mirakl_internal_property_option: MiraklInternalPropertyOptionType = update(
        MiraklInternalPropertyOptionPartialInput,
    )
    update_mirakl_category: MiraklCategoryType = update(MiraklCategoryPartialInput)
    update_mirakl_property: MiraklPropertyType = update(MiraklPropertyPartialInput)
    update_mirakl_property_select_value: MiraklPropertySelectValueType = update(
        MiraklPropertySelectValuePartialInput,
    )
    update_mirakl_property_applicability: MiraklPropertyApplicabilityType = update(
        MiraklPropertyApplicabilityPartialInput,
    )
    update_mirakl_product_type_item: MiraklProductTypeItemType = update(MiraklProductTypeItemPartialInput)
    update_mirakl_product_category: MiraklProductCategoryType = update(MiraklProductCategoryPartialInput)
    update_mirakl_document_type: MiraklDocumentTypeType = update(MiraklDocumentTypePartialInput)

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

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def start_mirakl_schema_import(
        self,
        instance: MiraklSalesChannelPartialInput,
        info: Info,
    ) -> MiraklSalesChannelImportType:
        from imports_exports.models import Import
        from sales_channels.integrations.mirakl.tasks import mirakl_import_db_task

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = MiraklSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        if not sales_channel.connected:
            raise ValidationError("Mirakl sales channel is missing credentials.")

        if sales_channel.is_importing:
            raise ValidationError("Mirakl sales channel is already importing.")

        import_process = MiraklSalesChannelImport.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=multi_tenant_company,
            type=MiraklSalesChannelImport.TYPE_SCHEMA,
            status=Import.STATUS_NEW,
            name=f"Mirakl schema import - {sales_channel.hostname}",
        )

        mirakl_import_db_task(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        return import_process

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def start_mirakl_product_feed(
        self,
        instance: MiraklSalesChannelPartialInput,
        info: Info,
    ) -> SalesChannelFeedType:
        from sales_channels.integrations.mirakl.flows import process_mirakl_gathering_product_feeds

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = MiraklSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        if not sales_channel.connected:
            raise ValidationError("Mirakl sales channel is missing credentials.")

        feeds = process_mirakl_gathering_product_feeds(sales_channel_id=sales_channel.id, force=True)
        if not feeds:
            raise ValidationError("No Mirakl gathering product feed was ready to process.")
        return feeds[-1]

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def retry_mirakl_feed(
        self,
        instance: SalesChannelFeedPartialInput,
        info: Info,
    ) -> SalesChannelFeedType:
        from sales_channels.integrations.mirakl.flows import retry_mirakl_feed
        from sales_channels.models import SalesChannelFeed

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        feed = SalesChannelFeed.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )
        if not isinstance(feed.sales_channel.get_real_instance(), MiraklSalesChannel):
            raise ValidationError("Feed does not belong to a Mirakl sales channel.")
        return retry_mirakl_feed(feed_id=feed.id)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def refresh_mirakl_import(
        self,
        instance: MiraklSalesChannelPartialInput,
        import_process: SalesChannelImportPartialInput,
        info: Info,
    ) -> MiraklSalesChannelImportType:
        from sales_channels.integrations.mirakl.flows import refresh_mirakl_imports

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = MiraklSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )
        mirakl_import = MiraklSalesChannelImport.objects.get(
            id=import_process.id.node_id,
            sales_channel=sales_channel,
            multi_tenant_company=multi_tenant_company,
        )
        refresh_mirakl_imports(import_process_id=mirakl_import.id)
        mirakl_import.refresh_from_db()
        return mirakl_import

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def refresh_mirakl_import_status(
        self,
        instance: MiraklSalesChannelPartialInput,
        import_process: SalesChannelImportPartialInput,
        info: Info,
    ) -> MiraklSalesChannelImportType:
        return self.refresh_mirakl_import(
            instance=instance,
            import_process=import_process,
            info=info,
        )
