from huey import crontab
from huey.contrib.djhuey import db_task, db_periodic_task


@db_task()
def prepare_shipments_task(order):
    from shipments.flows import prepare_shipments_flow
    prepare_shipments_flow(order)


@db_task()
def pre_approve_shipping_task(order):
    from shipments.flows import pre_approve_shipping_flow
    pre_approve_shipping_flow(order)
