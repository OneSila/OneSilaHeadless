from huey.contrib.djhuey import db_task


@db_task()
def merge_property_select_value_db_task(multi_tenant_company_id, source_ids, target_id):
    from .factories.merge_property_select_value import MergePropertySelectValueFactory

    factory = MergePropertySelectValueFactory(
        multi_tenant_company_id=multi_tenant_company_id,
        source_ids=source_ids,
        target_id=target_id,
    )
    return factory.run()
