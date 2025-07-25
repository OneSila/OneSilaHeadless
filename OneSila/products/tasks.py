from huey.contrib.djhuey import db_task
from core.decorators import run_task_after_commit


@run_task_after_commit
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

