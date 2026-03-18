from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from core.huey import CRUCIAL_PRIORITY
from integrations.factories.remote_task import BaseRemoteTask
from sales_channels.integrations.mirakl.factories.imports.schema_imports import (
    MiraklSchemaImportProcessor,
)
from sales_channels.integrations.mirakl.factories.imports.products import (
    MiraklProductsImportProcessor,
)
from sales_channels.decorators import remote_task
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelImport


@db_task()
def mirakl_import_db_task(*, import_process, sales_channel):
    """Dispatch the Mirakl import processor."""
    import_type = getattr(import_process, "type", MiraklSalesChannelImport.TYPE_SCHEMA)
    if import_type == MiraklSalesChannelImport.TYPE_SCHEMA:
        factory = MiraklSchemaImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        factory.run()
    elif import_type == MiraklSalesChannelImport.TYPE_PRODUCTS:
        factory = MiraklProductsImportProcessor(
            import_process=import_process,
            sales_channel=sales_channel,
        )
        factory.run()


@db_task()
def mirakl_map_perfect_match_select_values_db_task(*, sales_channel_id: int):
    from sales_channels.integrations.mirakl.factories.auto_import import (
        MiraklPerfectMatchSelectValueMappingFactory,
    )

    sales_channel = MiraklSalesChannel.objects.get(id=sales_channel_id)
    return MiraklPerfectMatchSelectValueMappingFactory(sales_channel=sales_channel).run()


@db_task()
def mirakl_map_perfect_match_properties_db_task(*, sales_channel_id: int):
    from sales_channels.integrations.mirakl.factories.auto_import import (
        MiraklPerfectMatchPropertyMappingFactory,
    )

    sales_channel = MiraklSalesChannel.objects.get(id=sales_channel_id)
    return MiraklPerfectMatchPropertyMappingFactory(sales_channel=sales_channel).run()


@db_periodic_task(crontab(minute="*/20"))
def sales_channels__tasks__sync_mirakl_product_feeds__cronjob():
    from sales_channels.integrations.mirakl.flows import process_mirakl_gathering_product_feeds

    process_mirakl_gathering_product_feeds()


@db_periodic_task(crontab(minute="*/15"))
def sales_channels__tasks__sync_mirakl_product_import_statuses__cronjob():
    from sales_channels.integrations.mirakl.flows import sync_mirakl_product_import_statuses

    sync_mirakl_product_import_statuses()


@db_periodic_task(crontab(minute="*/30"))
def sales_channels__tasks__refresh_mirakl_product_issues_differential__cronjob():
    from sales_channels.integrations.mirakl.flows import refresh_mirakl_product_issues_differential

    return refresh_mirakl_product_issues_differential()


@db_periodic_task(crontab(hour="*/12", minute="0"))
def sales_channels__tasks__refresh_mirakl_product_issues_full__cronjob():
    from sales_channels.integrations.mirakl.flows import refresh_mirakl_product_issues_full

    return refresh_mirakl_product_issues_full()


@db_task()
def sales_channels__tasks__sync_mirakl_product_feeds(*, sales_channel_id: int | None = None, force: bool = False):
    from sales_channels.integrations.mirakl.flows import process_mirakl_gathering_product_feeds

    return process_mirakl_gathering_product_feeds(sales_channel_id=sales_channel_id, force=force)


@db_task()
def sales_channels__tasks__sync_mirakl_product_import_statuses(*, sales_channel_id: int | None = None):
    from sales_channels.integrations.mirakl.flows import sync_mirakl_product_import_statuses

    return sync_mirakl_product_import_statuses(sales_channel_id=sales_channel_id)


@db_task()
def sales_channels__tasks__refresh_mirakl_product_issues_differential(*, sales_channel_id: int | None = None):
    from sales_channels.integrations.mirakl.flows import refresh_mirakl_product_issues_differential

    return refresh_mirakl_product_issues_differential(sales_channel_id=sales_channel_id)


@db_task()
def sales_channels__tasks__refresh_mirakl_product_issues_full(*, sales_channel_id: int | None = None):
    from sales_channels.integrations.mirakl.flows import refresh_mirakl_product_issues_full

    return refresh_mirakl_product_issues_full(sales_channel_id=sales_channel_id)


def _get_mirakl_remote_product_ids_for_product(*, sales_channel_id: int, product_id: int) -> list[int]:
    from sales_channels.integrations.mirakl.models import MiraklProduct

    return list(
        MiraklProduct.objects.filter(
            sales_channel_id=sales_channel_id,
            local_instance_id=product_id,
        ).values_list("id", flat=True)
    )


def _queue_delete_rows_for_mirakl_remote_products(
    *,
    sales_channel_id: int,
    remote_product_ids: list[int],
    view_id: int | None = None,
) -> list[int]:
    from sales_channels.integrations.mirakl.factories.feeds import MiraklProductDeleteFactory
    from sales_channels.integrations.mirakl.models import MiraklProduct, MiraklSalesChannelView
    from sales_channels.models import SalesChannelViewAssign

    processed_remote_product_ids: list[int] = []
    remote_products = MiraklProduct.objects.filter(id__in=remote_product_ids).select_related("sales_channel", "local_instance")
    for remote_product in remote_products.iterator():
        processed_remote_product_ids.append(remote_product.id)
        if view_id is not None:
            views = list(
                MiraklSalesChannelView.objects.filter(
                    id=view_id,
                    sales_channel_id=sales_channel_id,
                )
            )
        else:
            assigned_view_ids = list(
                SalesChannelViewAssign.objects.filter(
                    sales_channel_id=sales_channel_id,
                    remote_product_id=remote_product.id,
                )
                .exclude(sales_channel_view_id__isnull=True)
                .values_list("sales_channel_view_id", flat=True)
                .distinct()
            )
            if assigned_view_ids:
                views = list(
                    MiraklSalesChannelView.objects.filter(
                        sales_channel_id=sales_channel_id,
                        id__in=assigned_view_ids,
                    ).order_by("id")
                )
            else:
                views = list(
                    MiraklSalesChannelView.objects.filter(
                        sales_channel_id=sales_channel_id,
                    ).order_by("id")
                )
        for view in views:
            MiraklProductDeleteFactory(
                sales_channel=remote_product.sales_channel,
                local_instance=remote_product.local_instance,
                remote_instance=remote_product,
                view=view,
            ).run()

    return processed_remote_product_ids


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def create_mirakl_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    view_id: int,
):
    from sales_channels.integrations.mirakl.models import MiraklSalesChannel

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        from products.models import Product
        from sales_channels.integrations.mirakl.factories.feeds import MiraklProductCreateFactory
        from sales_channels.integrations.mirakl.models import MiraklSalesChannelView

        sales_channel = MiraklSalesChannel.objects.get(id=sales_channel_id)
        product = Product.objects.get(id=product_id)
        view = MiraklSalesChannelView.objects.get(id=view_id)
        factory = MiraklProductCreateFactory(
            sales_channel=sales_channel,
            local_instance=product,
            view=view,
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def update_mirakl_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    remote_product_id: int | None = None,
    view_id: int,
):
    from sales_channels.integrations.mirakl.models import MiraklSalesChannel

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        from products.models import Product
        from sales_channels.integrations.mirakl.factories.feeds import MiraklProductUpdateFactory
        from sales_channels.integrations.mirakl.models import MiraklProduct, MiraklSalesChannelView

        sales_channel = MiraklSalesChannel.objects.get(id=sales_channel_id)
        product = Product.objects.get(id=product_id)
        view = MiraklSalesChannelView.objects.get(id=view_id)
        remote_product = MiraklProduct.objects.filter(id=remote_product_id).first() if remote_product_id else None
        factory = MiraklProductUpdateFactory(
            sales_channel=sales_channel,
            local_instance=product,
            remote_instance=remote_product,
            view=view,
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def resync_mirakl_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    product_id: int,
    remote_product_id: int,
    view_id: int,
):
    from sales_channels.integrations.mirakl.models import MiraklSalesChannel

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        from products.models import Product
        from sales_channels.integrations.mirakl.factories.feeds import MiraklProductSyncFactory
        from sales_channels.integrations.mirakl.models import MiraklProduct, MiraklSalesChannelView

        sales_channel = MiraklSalesChannel.objects.get(id=sales_channel_id)
        product = Product.objects.get(id=product_id)
        view = MiraklSalesChannelView.objects.get(id=view_id)
        remote_product = MiraklProduct.objects.get(id=remote_product_id)
        factory = MiraklProductSyncFactory(
            sales_channel=sales_channel,
            local_instance=product,
            remote_instance=remote_product,
            view=view,
        )
        factory.run()

    task.execute(actual_task)


@remote_task(priority=CRUCIAL_PRIORITY, number_of_remote_requests=1)
@db_task()
def delete_mirakl_product_db_task(
    task_queue_item_id,
    *,
    sales_channel_id: int,
    remote_instance: int | None = None,
    remote_product_id: int | None = None,
    product_id: int | None = None,
    view_id: int | None = None,
):
    from sales_channels.integrations.mirakl.models import MiraklProduct, MiraklSalesChannel

    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        sales_channel = MiraklSalesChannel.objects.get(id=sales_channel_id)
        if remote_product_id:
            remote_product_ids = [remote_product_id]
        elif remote_instance:
            remote_product_ids = [remote_instance]
        elif product_id:
            remote_product_ids = _get_mirakl_remote_product_ids_for_product(
                sales_channel_id=sales_channel_id,
                product_id=product_id,
            )
        else:
            remote_product_ids = []

        if not remote_product_ids and remote_instance:
            remote_product = MiraklProduct.objects.filter(id=remote_instance).first()
            if remote_product is not None:
                remote_product_ids = [remote_product.id]

        processed_remote_product_ids = _queue_delete_rows_for_mirakl_remote_products(
            sales_channel_id=sales_channel_id,
            remote_product_ids=remote_product_ids,
            view_id=view_id,
        )
        if not processed_remote_product_ids:
            return

    task.execute(actual_task)
