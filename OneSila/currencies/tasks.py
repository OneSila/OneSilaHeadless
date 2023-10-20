from huey import db_periodic_task, db_task, cronjob
from flows.update_rates import UpdateRateFlow


@db_task()
def currencies__currency__update_rates():
    return UpdateRateFlow().run()


@db_task(cronjob(hour=1, min=1))
def currencies__currency__update_rates__cronjob():
    return UpdateRateFlow().run()
