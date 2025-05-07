# Asynchronous tasks for Woocommerce integration
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task
from .models import WoocommerceSalesChannel


@db_task()
def sync_products(sales_channel_id):
    """
    Sync products from Woocommerce
    """
    try:
        sales_channel = WoocommerceSalesChannel.objects.get(id=sales_channel_id)
        # Add implementation
    except WoocommerceSalesChannel.DoesNotExist:
        pass


@db_task()
def sync_orders(sales_channel_id):
    """
    Sync orders from Woocommerce
    """
    try:
        sales_channel = WoocommerceSalesChannel.objects.get(id=sales_channel_id)
        # Add implementation
    except WoocommerceSalesChannel.DoesNotExist:
        pass


@db_periodic_task(crontab(minute='*/30'))
def scheduled_product_sync():
    """
    Scheduled task to sync products every 30 minutes
    """
    for sales_channel in WoocommerceSalesChannel.objects.filter(is_active=True):
        sync_products(sales_channel.id)


@db_periodic_task(crontab(minute='*/15'))
def scheduled_order_sync():
    """
    Scheduled task to sync orders every 15 minutes
    """
    for sales_channel in WoocommerceSalesChannel.objects.filter(is_active=True):
        sync_orders(sales_channel.id)
