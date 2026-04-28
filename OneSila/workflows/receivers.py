import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.signals import post_create
from core.schema.core.subscriptions import refresh_subscription_receiver
from products.models import AliasProduct, BundleProduct, ConfigurableProduct, Product, SimpleProduct
from workflows.models import Workflow, WorkflowProductAssignment

logger = logging.getLogger(__name__)


def _create_auto_workflow_assignments_for_product(*, product):
    workflows = Workflow.objects.filter(
        multi_tenant_company=product.multi_tenant_company,
        auto_add_on_product=True,
    ).prefetch_related("states")

    for workflow in workflows:
        default_state = next(
            (state for state in workflow.states.all() if state.is_default),
            None,
        )
        if default_state is None:
            logger.warning(
                "Skipping auto workflow assignment for workflow=%s product=%s because no default state exists.",
                workflow.id,
                product.id,
            )
            continue

        WorkflowProductAssignment.objects.get_or_create(
            workflow=workflow,
            product=product,
            multi_tenant_company=product.multi_tenant_company,
            defaults={
                "workflow_state": default_state,
                "multi_tenant_company": product.multi_tenant_company,
            },
        )


@receiver(post_create, sender=Product)
@receiver(post_create, sender=SimpleProduct)
@receiver(post_create, sender=ConfigurableProduct)
@receiver(post_create, sender=BundleProduct)
@receiver(post_create, sender=AliasProduct)
def workflows__product__post_create_auto_assign(sender, instance, **kwargs):
    _create_auto_workflow_assignments_for_product(product=instance)


@receiver(post_save, sender=WorkflowProductAssignment)
@receiver(post_delete, sender=WorkflowProductAssignment)
def workflows__assignment__refresh_related_subscriptions(sender, instance, **kwargs):
    refresh_subscription_receiver(instance.product)
    refresh_subscription_receiver(instance.workflow)
