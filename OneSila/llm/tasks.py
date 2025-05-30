from huey.contrib.djhuey import db_task
from core.decorators import run_task_after_commit
from llm.flows.translate_ai_content import BulkAiTranslateContentFlow


@run_task_after_commit
@db_task()
def llm__ai_translate__run_bulk_ai_translation_flow(
    multi_tenant_company_id: int,
    from_language_code: str,
    to_language_codes: list[str],
    product_ids: list[int | str],
    property_ids: list[int | str],
    value_ids: list[int | str],
    override_translation: bool,
):
    from products.models import Product
    from properties.models import Property, PropertySelectValue
    from core.models import MultiTenantCompany

    multi_tenant_company = MultiTenantCompany.objects.get(id=multi_tenant_company_id)
    products = Product.objects.filter(id__in=product_ids, multi_tenant_company=multi_tenant_company)
    properties = Property.objects.filter(id__in=property_ids, multi_tenant_company=multi_tenant_company)
    values = PropertySelectValue.objects.filter(id__in=value_ids, multi_tenant_company=multi_tenant_company)

    flow = BulkAiTranslateContentFlow(
        multi_tenant_company=multi_tenant_company,
        from_language_code=from_language_code,
        to_language_codes=to_language_codes,
        products=products,
        properties=properties,
        values=values,
        override_translation=override_translation,
    )
    flow.run()
