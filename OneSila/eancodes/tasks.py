from huey.contrib.djhuey import db_task

@db_task()
def eancodes__ean_code__generate_task(prefix, multi_tenant_company):
    from eancodes.flows.generate_eancodes import GenerateEancodesFlow

    eancode_generator = GenerateEancodesFlow(multi_tenant_company=multi_tenant_company, prefix=prefix)
    eancode_generator.flow()