from huey.contrib.djhuey import db_task
from core.huey import HIGH_PRIORITY, VERY_LOW_PRIORITY
from core.decorators import run_task_after_commit
from products_inspector.factories.inspector import ResyncInspectorFactory


@run_task_after_commit
@db_task(priority=0)
def resync_inspector_task(inspector_id):
    from products_inspector.models import Inspector
    """
    Asynchronous task to resync all blocks for a given inspector.
    This task will run the ResyncInspectorFactory for the specified inspector.
    """
    inspector = Inspector.objects.get(id=inspector_id)
    factory = ResyncInspectorFactory(inspector)
    factory.run()


@run_task_after_commit
@db_task(priority=0)
def resync_inspector_block_task(block_id):
    from products_inspector.factories.inspector_block import InspectorBlockFactoryRegistry
    from products_inspector.models import InspectorBlock
    """
    Asynchronous task to resync a specific block for a given inspector.
    """
    block = InspectorBlock.objects.get(id=block_id)
    block_factory = InspectorBlockFactoryRegistry.get_factory(block.error_code)(block, save_inspector=True)
    block_factory.run()


@run_task_after_commit
@db_task(priority=0)
def trigger_rule_dependent_inspector_blocks_task(rule_id):
    from properties.models import ProductPropertiesRule
    from .flows.inspector_block import trigger_product_inspectors_for_rule_flow
    """
    Asynchronous task to retrigger inspector blocks that depends on the rule for all the products using that rule.
    """
    rule = ProductPropertiesRule.objects.get(id=rule_id)
    trigger_product_inspectors_for_rule_flow(rule)


def trigger_rule_dependent_inspector_blocks_delete_task(rule):
    from .flows.inspector_block import trigger_product_inspectors_for_rule_flow
    """
    The difference between this one and the above one is that this one gives the rule from memory so we
    can run it on post_delete signal.
    """
    trigger_product_inspectors_for_rule_flow(rule)


@run_task_after_commit
@db_task(priority=0)
def products_inspector__tasks__bulk_refresh_inspector(
    *,
    multi_tenant_company_id: int,
    product_ids: list[int | str],
) -> None:
    from core.models import MultiTenantCompany
    from products_inspector.flows.inspector import bulk_refresh_inspector_flow

    multi_tenant_company = MultiTenantCompany.objects.get(id=multi_tenant_company_id)
    bulk_refresh_inspector_flow(
        multi_tenant_company=multi_tenant_company,
        product_ids=product_ids,
    )
