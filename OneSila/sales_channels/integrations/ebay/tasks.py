"""Huey tasks for the eBay integration."""

from huey.contrib.djhuey import db_task

from llm.flows.remote_translations import (
    TranslateRemotePropertyFlow,
    TranslateRemoteSelectValueFlow,
)


@db_task()
def ebay_import_db_task(import_process, sales_channel):
    from sales_channels.integrations.ebay.factories.imports.schema_imports import (
        EbaySchemaImportProcessor,
    )
    from sales_channels.integrations.ebay.factories.imports.products_imports import (
        EbayProductsAsyncImportProcessor,
    )
    from sales_channels.integrations.ebay.models import EbaySalesChannelImport

    import_type = getattr(import_process, "type", EbaySalesChannelImport.TYPE_SCHEMA)

    if import_type == EbaySalesChannelImport.TYPE_SCHEMA:
        factory = EbaySchemaImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        factory.run()
    elif import_type == EbaySalesChannelImport.TYPE_PRODUCTS:
        # factory = EbayProductsAsyncImportProcessor(
        #     import_process=import_process,
        #     sales_channel=sales_channel,
        # )
        # factory.run()
        # @TODO: Temporary disabled this until propert testing
        pass


@db_task()
def ebay_product_import_item_task(
    import_process_id: int,
    sales_channel_id: int,
    product_data: dict,
    is_last: bool = False,
    updated_with: int | None = None,
):
    from imports_exports.models import Import
    from sales_channels.integrations.ebay.factories.imports.products_imports import (
        EbayProductItemFactory,
    )
    from sales_channels.integrations.ebay.models import EbaySalesChannel

    process = Import.objects.get(id=import_process_id)
    channel = EbaySalesChannel.objects.get(id=sales_channel_id)
    factory = EbayProductItemFactory(
        product_data=product_data,
        import_process=process,
        sales_channel=channel,
        is_last=is_last,
        updated_with=updated_with,
    )
    factory.run()


@db_task()
def ebay_translate_property_task(property_id: int):
    from sales_channels.integrations.ebay.models import EbayProperty

    instance = EbayProperty.objects.get(id=property_id)
    flow = TranslateRemotePropertyFlow(
        instance=instance,
        integration_label="eBay",
        remote_name_fields=("localized_name", "remote_id"),
        translation_field="translated_name",
        remote_identifier_attr="remote_id",
    )
    flow.flow()


@db_task()
def ebay_translate_select_value_task(select_value_id: int):
    from sales_channels.integrations.ebay.models import EbayPropertySelectValue

    instance = EbayPropertySelectValue.objects.get(id=select_value_id)
    flow = TranslateRemoteSelectValueFlow(
        instance=instance,
        integration_label="eBay",
        remote_name_fields=("localized_value", "remote_id"),
        translation_field="translated_value",
        property_name_attr="ebay_property.localized_name",
        property_code_attr="ebay_property.remote_id",
    )
    flow.flow()


@db_task()
def ebay_translate_product_type_task(product_type_id: int):
    from sales_channels.integrations.ebay.models import EbayProductType

    instance = EbayProductType.objects.get(id=product_type_id)
    flow = TranslateRemotePropertyFlow(
        instance=instance,
        integration_label="eBay",
        remote_name_fields=("name", "remote_id"),
        translation_field="translated_name",
        remote_identifier_attr="remote_id",
    )
    flow.flow()
