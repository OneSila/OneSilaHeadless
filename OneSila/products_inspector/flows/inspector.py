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
