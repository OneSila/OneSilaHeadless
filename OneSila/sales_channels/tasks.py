from typing import Optional, Tuple, Dict
from django.db.models import Sum
from huey import crontab
from huey.contrib.djhuey import db_task, periodic_task
from django.core.exceptions import ValidationError
from core.huey import DEFAULT_PRIORITY
from products.product_types import CONFIGURABLE
from sales_channels.models.sales_channels import SalesChannel, RemoteTaskQueue
from sales_channels.helpers import resolve_function
import logging

logger = logging.getLogger(__name__)

@db_task()
def add_task_to_queue(
    *,
    sales_channel_id: str | int,
    task_func_path: str,
    task_args: Optional[Tuple] = None,
    task_kwargs: Optional[Dict] = None,
    number_of_remote_requests: Optional[int] = None,
    priority: Optional[int] = None
) -> None:

    sales_channel = SalesChannel.objects.get(id=sales_channel_id)
    task_func = resolve_function(task_func_path)

    # Validate the task function
    if not callable(task_func):
        raise ValidationError("The provided task function is not callable.")

    task_priority = priority if priority is not None else getattr(task_func, 'priority', DEFAULT_PRIORITY)
    remote_requests = number_of_remote_requests if number_of_remote_requests is not None else getattr(task_func, 'number_of_remote_requests', 1)

    # Check the total number of currently active requests (in PROCESSING and PENDING status)
    active_requests = RemoteTaskQueue.objects.filter(
        sales_channel=sales_channel,
        status__in=[RemoteTaskQueue.PROCESSING, RemoteTaskQueue.PENDING]
    ).aggregate(total=Sum('number_of_remote_requests'))['total'] or 0

    # Determine whether to process the task immediately based on requests per minute limit
    process_now = active_requests + remote_requests <= sales_channel.requests_per_minute

    logger.debug(
        f"Task for SalesChannel '{sales_channel.hostname}': Requests per minute limit is {sales_channel.requests_per_minute}. Currently active requests: {active_requests}. Processing now: {process_now}.")

    # Set task status based on whether it should be processed immediately or queued
    task_status = RemoteTaskQueue.PROCESSING if process_now else RemoteTaskQueue.PENDING


    # Create the RemoteTaskQueue entry with the appropriate parameters
    task_queue_item = RemoteTaskQueue.objects.create(
        sales_channel=sales_channel,
        task_name=task_func_path,
        task_args=task_args or {},
        task_kwargs=task_kwargs or {},
        status=task_status,
        number_of_remote_requests=remote_requests,
        priority=task_priority,
        multi_tenant_company=sales_channel.multi_tenant_company
    )

    logger.debug(
        f"Task '{task_func_path}' {'immediately processing' if process_now else 'added to the queue'} for SalesChannel '{sales_channel.hostname}' with priority {task_priority}.")

    # Dispatch the task immediately if conditions allow
    if process_now:
        task_queue_item.dispatch()


@periodic_task(crontab(minute="*"))
def sales_channels_process_remote_tasks_queue():
    print('---------------------------------------------- ??')
    print(SalesChannel.objects.filter(active=True))
    for sales_channel in SalesChannel.objects.filter(active=True):
        # Get the next batch of tasks that can be processed
        pending_tasks = RemoteTaskQueue.get_pending_tasks(sales_channel)
        print('--------------------------------------------------------------')
        print(pending_tasks)

        # Log the number of pending tasks found and the request limit
        logger.info(f"Found {len(pending_tasks)} tasks to process for SalesChannel '{sales_channel.hostname}' with a limit of {sales_channel.requests_per_minute} requests per minute.")

        # Dispatch each task in the batch
        for task_queue_item in pending_tasks:
            task_queue_item.dispatch()

@periodic_task(crontab(hour=0, minute=0))
def clean_up_processed_tasks():
    deleted_count, _ = RemoteTaskQueue.objects.filter(status=RemoteTaskQueue.PROCESSED).delete()
    logger.info(f"Cleaned up {deleted_count} processed tasks.")


@db_task()
def update_configurators_for_rule_db_task(rule):
    from products.models import Product
    from .models import RemoteProduct

    # Step 1: Filter products by the properties rule
    products = Product.objects.filter(type=CONFIGURABLE).filter_by_properties_rule(rule=rule)

    # Step 2: Filter out products with missing information
    products_with_valid_info = products.filter(inspector__has_missing_information=False)

    # Step 3: Retrieve remote products that are not variations and belong to the same tenant
    remote_products = RemoteProduct.objects.filter(
        local_instance_id__in=products_with_valid_info.values_list('id', flat=True),
        is_variation=False,
        multi_tenant_company=rule.multi_tenant_company
    )

    # Step 4: Iterate through remote products and update configurators
    for remote_product in remote_products.iterator():
        try:
            if remote_product.configurator:
                remote_product.configurator.update_if_needed(rule=rule, send_sync_signal=True)
        except RemoteProduct.configurator.RelatedObjectDoesNotExist:
            pass

@db_task()
def update_configurators_for_parent_product_db_task(parent_product):
    from sales_channels.models import RemoteProduct

    # Step 1: Retrieve remote products for the parent product and the multi-tenant company
    remote_products = RemoteProduct.objects.filter(
        local_instance=parent_product,
        is_variation=False,
        multi_tenant_company=parent_product.multi_tenant_company
    )

    # Step 2: Iterate through remote products and update configurators
    for remote_product in remote_products.iterator():
        if remote_product.configurator:
            remote_product.configurator.update_if_needed(send_sync_signal=True)

@db_task()
def update_configurators_for_product_property_db_task(product, property):
    from sales_channels.models import RemoteProduct
    from products.models import Product

    # Step 1: Get all parent product IDs where this product is a variation
    parent_product_ids = product.configurablevariation_through_variations.values_list('parent_id', flat=True)

    # Step 2: Retrieve all parent products in a single query
    parent_products = Product.objects.filter(id__in=parent_product_ids)

    # Step 3: Iterate through each parent product and check if we need to update the configurator
    for parent_product in parent_products:
        # Get the product rule for the parent product
        product_rule = parent_product.get_product_rule()

        # Check if the property is optional in the configurator
        optional_properties_in_configurator = parent_product.get_optional_in_configurator_properties(product_rule)
        if property not in optional_properties_in_configurator.values_list('property', flat=True):
            continue  # Skip if the property is not optional in configurator

        # Step 4: Retrieve remote products for the parent product
        remote_products = RemoteProduct.objects.filter(
            local_instance=parent_product,
            multi_tenant_company=parent_product.multi_tenant_company
        )

        # Step 5: Iterate through remote products and update configurators
        for remote_product in remote_products.iterator():
            if remote_product.configurator:
                remote_product.configurator.update_if_needed(rule=product_rule, send_sync_signal=True)