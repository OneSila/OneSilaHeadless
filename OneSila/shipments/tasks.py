from huey import crontab
from huey.contrib.djhuey import db_task, db_periodic_task


@db_task()
def prepare_shipments_task(order):
    from shipments.flows import prepare_shipments_flow
    prepare_shipments_flow(order)
