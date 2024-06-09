from huey.contrib.djhuey import db_task
from .demo_data import DemoDataLibrary

import logging
logger = logging.getLogger(__name__)

@db_task()
def core__demo_data__create_task(multi_tenant_company):
    fac = DemoDataLibrary()
    fac.run(multi_tenant_company=multi_tenant_company)

@db_task()
def core__demo_data__delete_task(multi_tenant_company):
    fac = DemoDataLibrary()
    fac.delete_demo_data(multi_tenant_company=multi_tenant_company)