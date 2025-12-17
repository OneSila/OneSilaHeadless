"""Huey tasks for the eBay integration."""

from huey.contrib.djhuey import db_task

from core.huey import CRUCIAL_PRIORITY
from integrations.factories.remote_task import BaseRemoteTask
from llm.flows.remote_translations import (
    TranslateRemotePropertyFlow,
    TranslateRemoteSelectValueFlow,
)
from sales_channels.decorators import remote_task


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
        factory = EbayProductsAsyncImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        factory.run()


@db_task()
def ebay_product_import_item_task(
    import_process_id: int,
    sales_channel_id: int,
    data: dict,
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
        product_data=data["product"],
        offer_data=data["offer"],
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


@db_task()
def ebay_map_perfect_match_select_values_db_task(*, sales_channel_id: int):
    from sales_channels.integrations.ebay.factories.auto_import import (
        EbayPerfectMatchSelectValueMappingFactory,
    )
    from sales_channels.integrations.ebay.models import EbaySalesChannel

    sales_channel = EbaySalesChannel.objects.get(id=sales_channel_id)
    EbayPerfectMatchSelectValueMappingFactory(sales_channel=sales_channel).run()


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=2)
@db_task()
def ebay_product_type_rule_sync_task(*, product_type_id: int) -> None:
    """Synchronise local rule metadata for the mapped eBay category."""
    from sales_channels.integrations.ebay.flows.product_type_rules import (
        EbayProductTypeRuleSyncFlow,
    )

    flow = EbayProductTypeRuleSyncFlow(product_type_id=product_type_id)
    flow.work()


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_ebay_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    view_id: int,
):
    """Run the eBay product creation factory."""
    from products.models import Product
    from sales_channels.integrations.ebay.factories.products import EbayProductCreateFactory
    from sales_channels.integrations.ebay.models import EbaySalesChannel, EbaySalesChannelView

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = EbayProductCreateFactory(
            sales_channel=EbaySalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            view=EbaySalesChannelView.objects.get(id=view_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def resync_ebay_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    remote_product_id: int,
    view_id: int,
):
    """Run the eBay product resync factory."""
    from products.models import Product
    from sales_channels.integrations.ebay.factories.products import EbayProductSyncFactory
    from sales_channels.integrations.ebay.models import (
        EbayProduct,
        EbaySalesChannel,
        EbaySalesChannelView,
    )

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = EbayProductSyncFactory(
            sales_channel=EbaySalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            remote_instance=EbayProduct.objects.get(id=remote_product_id),
            view=EbaySalesChannelView.objects.get(id=view_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_ebay_assign_offers_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    view_id: int,
):
    """Ensure offers exist for the given product/view assignment."""
    from products.models import Product
    from sales_channels.integrations.ebay.factories.products.assigns import (
        EbaySalesChannelViewAssignUpdateFactory,
    )
    from sales_channels.integrations.ebay.models import (
        EbaySalesChannel,
        EbaySalesChannelView,
    )

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = EbaySalesChannelViewAssignUpdateFactory(
            sales_channel=EbaySalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            view=EbaySalesChannelView.objects.get(id=view_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_ebay_assign_offers_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    view_id: int,
):
    """Withdraw and delete offers for a removed product/view assignment."""
    from products.models import Product
    from sales_channels.integrations.ebay.factories.products.assigns import (
        EbaySalesChannelViewAssignDeleteFactory,
    )
    from sales_channels.integrations.ebay.models import (
        EbaySalesChannel,
        EbaySalesChannelView,
    )

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = EbaySalesChannelViewAssignDeleteFactory(
            sales_channel=EbaySalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            view=EbaySalesChannelView.objects.get(id=view_id),
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_ebay_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    view_id: int,
):
    """Remove the remote product, offers, and inventory for a view."""
    from products.models import Product
    from sales_channels.integrations.ebay.factories.products import EbayProductDeleteFactory
    from sales_channels.integrations.ebay.models import (
        EbaySalesChannel,
        EbaySalesChannelView,
    )

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = EbayProductDeleteFactory(
            sales_channel=EbaySalesChannel.objects.get(id=sales_channel_id),
            local_instance=Product.objects.get(id=product_id),
            view=EbaySalesChannelView.objects.get(id=view_id),
        )
        factory.run()

    task.execute(actual_task)
