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
    from sales_channels.integrations.ebay.models import EbaySalesChannelImport

    import_type = getattr(import_process, "type", EbaySalesChannelImport.TYPE_SCHEMA)

    if import_type == EbaySalesChannelImport.TYPE_SCHEMA:
        factory = EbaySchemaImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
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
