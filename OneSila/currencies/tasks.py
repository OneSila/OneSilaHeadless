from huey import crontab
from huey.contrib.djhuey import db_task, db_periodic_task

from currencies.flows import update_rate_flow


@db_task(cronjob(day="*", hour=1, min=1))
def currencies__currency__update_rates__cronjob():
    return update_rate_flow()
