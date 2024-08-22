from huey import crontab
from huey.contrib.djhuey import db_task, db_periodic_task


@db_task()
def buy_dropshippingproducts_task(order):
    from purchasing.flows import buy_dropshippingproducts_flow
    buy_dropshippingproducts_flow(order)
