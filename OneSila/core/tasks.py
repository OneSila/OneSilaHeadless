from huey.contrib.djhuey import db_task

from .decorators import run_task_after_commit
from .demo_data import DemoDataLibrary

import logging
logger = logging.getLogger(__name__)


# @run_task_after_commit
@db_task()
def core__demo_data__create_task(multi_tenant_company):
    if not multi_tenant_company.demodatarelation_set.all().exists():
        fac = DemoDataLibrary()
        fac.run(multi_tenant_company=multi_tenant_company)


# @run_task_after_commit
@db_task()
def core__demo_data__delete_task(multi_tenant_company):
    if multi_tenant_company.demodatarelation_set.all().exists():
        fac = DemoDataLibrary()
        fac.delete_demo_data(multi_tenant_company=multi_tenant_company)
