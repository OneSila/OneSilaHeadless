from huey.contrib.djhuey import db_task
from core.decorators import run_task_after_commit


# @run_task_after_commit
@db_task()
def products__generate_variations_task(
    *,
    rule_id: int | str,
    config_product_id: int | str,
    select_value_ids: list[int | str],
    language: str | None = None,
) -> None:
    """Generate product variations asynchronously."""
    from products.factories.generate_variations import GenerateProductVariations
    from properties.models import ProductPropertiesRule, PropertySelectValue
    from products.models import Product

    rule = ProductPropertiesRule.objects.get(id=rule_id)
    config_product = Product.objects.get(id=config_product_id)
    select_values = PropertySelectValue.objects.filter(id__in=select_value_ids)

    factory = GenerateProductVariations(
        rule=rule,
        config_product=config_product,
        select_values=select_values,
        language=language,
    )
    factory.run()


@db_task()
def products__tasks__import_product_translations(
    *,
    multi_tenant_company_id: int,
    product_ids: list[int | str],
    source_channel_id: int | str | None,
    target_channel_id: int | str | None,
    language: str | None,
    override: bool,
    all_languages: bool,
    fields: list[str],
) -> None:
    from core.models import MultiTenantCompany
    from products.flows.translation_import import ProductTranslationImportFlow
    from products.models import Product
    from sales_channels.models import SalesChannel

    multi_tenant_company = MultiTenantCompany.objects.get(id=multi_tenant_company_id)
    products = Product.objects.filter(id__in=product_ids, multi_tenant_company=multi_tenant_company)

    source_channel = None
    if source_channel_id:
        source_channel = SalesChannel.objects.get(
            id=source_channel_id,
            multi_tenant_company=multi_tenant_company,
        )

    target_channel = None
    if target_channel_id:
        target_channel = SalesChannel.objects.get(
            id=target_channel_id,
            multi_tenant_company=multi_tenant_company,
        )

    flow = ProductTranslationImportFlow(
        multi_tenant_company=multi_tenant_company,
        products=products,
        source_channel=source_channel,
        target_channel=target_channel,
        language=language,
        override=override,
        all_languages=all_languages,
        fields=fields,
    )
    flow.flow()
