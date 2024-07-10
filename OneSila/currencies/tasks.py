from huey import crontab
from huey.contrib.djhuey import db_task, db_periodic_task

# from currencies.flows.update_rates import UpdateRateFlow


# FIXME: UpdateRateFlow doesnt exist anymore.  verify if it's UpdateOfficialRateFlow or UpdateFollowerRateFlow or both?
# @db_task()
# def currencies__currency__update_rates():
#     return UpdateRateFlow().run()


# @db_task(cronjob(hour=1, min=1))
# def currencies__currency__update_rates__cronjob():
#     return UpdateRateFlow().run()
