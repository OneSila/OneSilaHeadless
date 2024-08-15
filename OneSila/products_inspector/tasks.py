from huey.contrib.djhuey import db_task

from core.schema.core.subscriptions import refresh_subscription_receiver
from products_inspector.factories.inspector import ResyncInspectorFactory


@db_task()
def resync_inspector_task(inspector_id):
    from products_inspector.models import Inspector
    """
    Asynchronous task to resync all blocks for a given inspector.
    This task will run the ResyncInspectorFactory for the specified inspector.
    """
    inspector = Inspector.objects.get(id=inspector_id)
    factory = ResyncInspectorFactory(inspector)
    factory.run()

@db_task()
def resync_inspector_block_task(block_id):
    from products_inspector.factories.inspector_block import InspectorBlockFactoryRegistry
    from products_inspector.models import InspectorBlock
    """
    Asynchronous task to resync a specific block for a given inspector.
    """
    block = InspectorBlock.objects.get(id=block_id)
    block_factory = InspectorBlockFactoryRegistry.get_factory(block.error_code)(block, save_inspector=True)
    block_factory.run()

@db_task()
def trigger_rule_dependent_inspector_blocks(rule_id):
    from properties.models import ProductPropertiesRule
    from .flows.inspector_block import trigger_product_inspectors_for_rule_flow
    """
    Asynchronous task to retrigger inspector blocks that depends on the rule for all the products using that rule.
    """
    rule = ProductPropertiesRule.objects.get(id=rule_id)
    trigger_product_inspectors_for_rule_flow(rule)


@db_task()
def trigger_rule_dependent_inspector_blocks_delete(rule):
    from .flows.inspector_block import trigger_product_inspectors_for_rule_flow
    """
    The difference between this one and the above one is that this one gives the rule from memory so we
    can run it on post_delete signal.
    """
    trigger_product_inspectors_for_rule_flow(rule)