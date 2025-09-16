"""Huey tasks for the eBay integration."""

from huey.contrib.djhuey import db_task

from llm.factories.translations import StringTranslationLLM


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

    remote_name = instance.localized_name or instance.remote_id
    if not remote_name:
        return

    remote_language_obj = instance.marketplace.remote_languages.first()
    remote_lang = remote_language_obj.local_instance if remote_language_obj else None
    company_lang = instance.sales_channel.multi_tenant_company.language

    if not remote_lang or remote_lang == company_lang:
        translated = remote_name
    else:
        translator = StringTranslationLLM(
            to_translate=remote_name,
            from_language_code=remote_lang,
            to_language_code=company_lang,
            multi_tenant_company=instance.sales_channel.multi_tenant_company,
            sales_channel=instance.sales_channel,
        )
        try:
            translated = translator.translate()
        except Exception:
            translated = remote_name

    if instance.translated_name != translated:
        instance.translated_name = translated
        instance.save(update_fields=["translated_name"])


@db_task()
def ebay_translate_select_value_task(select_value_id: int):
    from sales_channels.integrations.ebay.models import EbayPropertySelectValue

    instance = EbayPropertySelectValue.objects.get(id=select_value_id)

    remote_name = instance.localized_value or instance.remote_id
    if not remote_name:
        return

    remote_language_obj = instance.marketplace.remote_languages.first()
    remote_lang = remote_language_obj.local_instance if remote_language_obj else None
    company_lang = instance.sales_channel.multi_tenant_company.language

    if not remote_lang or remote_lang == company_lang:
        translated = remote_name
    else:
        translator = StringTranslationLLM(
            to_translate=remote_name,
            from_language_code=remote_lang,
            to_language_code=company_lang,
            multi_tenant_company=instance.sales_channel.multi_tenant_company,
            sales_channel=instance.sales_channel,
        )
        try:
            translated = translator.translate()
        except Exception:
            translated = remote_name

    if instance.translated_value != translated:
        instance.translated_value = translated
        instance.save(update_fields=["translated_value"])
