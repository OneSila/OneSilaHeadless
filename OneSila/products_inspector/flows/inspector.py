from products_inspector.factories.inspector import InspectorCreateOrUpdateFactory, ResyncInspectorFactory


def inspector_creation_flow(product):
    """
    This flow is responsible for creating the inspector and its related blocks
    based on the product's type.
    """
    factory = InspectorCreateOrUpdateFactory(product)
    factory.run()


def resync_inspector_flow(inspector, run_async=True):
    """
    Flow to resync all blocks for the given inspector.
    If run_async is True, the resync is performed asynchronously using a task (e.g., with Huey).
    If run_async is False, the resync is performed synchronously in the main thread.
    """
    from ..tasks import resync_inspector_task

    if run_async:
        # Run the resync asynchronously using the task (Huey)
        resync_inspector_task(inspector.id)
    else:
        # Run the resync synchronously (in the main thread)
        factory = ResyncInspectorFactory(inspector)
        factory.run()


def bulk_refresh_inspector_flow(*, multi_tenant_company, product_ids: list[int | str]) -> None:
    """
    Refresh inspectors for the provided product ids.
    """
    from products_inspector.models import Inspector

    if not product_ids:
        return

    unique_product_ids = list(dict.fromkeys(product_ids))
    inspectors = Inspector.objects.select_related("product").filter(
        product_id__in=unique_product_ids,
        product__multi_tenant_company=multi_tenant_company,
    )

    for inspector in inspectors.iterator():
        inspector.inspect_product(run_async=False)