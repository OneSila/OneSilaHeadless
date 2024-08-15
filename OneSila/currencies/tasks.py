from huey import crontab
from huey.contrib.djhuey import db_task, db_periodic_task

from currencies.flows import update_rate_flow


@db_periodic_task(crontab(day='*', hour='1', minute='3'))
def currencies__currency__update_rates__cronjob():
    return update_rate_flow()
