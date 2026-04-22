from __future__ import annotations

from core.models.multi_tenant import MultiTenantCompany
from django.db import transaction
from imports_exports.factories.products import ImportProductInstance
from llm.models import McpToolRun
from products.mcp.catalog_helpers import get_product_type_match, get_vat_rate_match
from products.mcp.types import (
    ProductImageInputPayload,
    ProductPriceUpsertInputPayload,
    ProductPropertyValueUpdateInputPayload,
    ProductTranslationUpsertInputPayload,
)
from products.mcp.update_helpers import run_upsert_product_updates
from products.mcp.types import CreateProductPayload


def run_product_create(
    *,
    import_process: McpToolRun,
    product_data: dict,
):
    import_instance = ImportProductInstance(
        product_data,
        import_process=import_process,
    )
    import_instance.process()
    return import_instance


def build_create_product_payload(
    *,
    product,
    sku_was_generated: bool,
) -> CreateProductPayload:
    return {
        "created": True,
        "sku_was_generated": sku_was_generated,
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "message": "Created successfully. Use get_product for details.",
    }


def build_create_product_data(
    *,
    multi_tenant_company: MultiTenantCompany,
    name: str,
    product_type_code: str,
    sku: str | None,
    product_type_id: int | None,
    product_type_value: str | None,
    vat_rate_id: int | None,
    vat_rate: int | None,
) -> tuple[dict, bool]:
    product_data = {
        "name": name,
        "type": product_type_code,
    }
    sku_was_generated = not bool(sku)
    if sku:
        product_data["sku"] = sku

    product_type_select_value = get_product_type_match(
        multi_tenant_company=multi_tenant_company,
        product_type_id=product_type_id,
        product_type_value=product_type_value,
    )
    if product_type_select_value is not None:
        product_data["product_type"] = product_type_select_value.value

    vat_rate_instance = get_vat_rate_match(
        multi_tenant_company=multi_tenant_company,
        vat_rate_id=vat_rate_id,
        vat_rate=vat_rate,
    )
    if vat_rate_instance is not None:
        if vat_rate_instance.rate is not None:
            product_data["vat_rate"] = vat_rate_instance.rate
        else:
            product_data["vat_rate"] = vat_rate_instance.name
            product_data["use_vat_rate_name"] = True

    return product_data, sku_was_generated


def run_create_product_with_sections(
    *,
    import_process: McpToolRun,
    multi_tenant_company: MultiTenantCompany,
    product_data: dict,
    sku: str | None,
    sku_was_generated: bool,
    active: bool | None,
    ean_code: str | None,
    translations: list[ProductTranslationUpsertInputPayload] | None,
    prices: list[ProductPriceUpsertInputPayload] | None,
    properties: list[ProductPropertyValueUpdateInputPayload] | None,
    images: list[ProductImageInputPayload] | None,
    sales_channel_view_ids: list[int] | None,
) -> CreateProductPayload:
    with transaction.atomic():
        import_instance = run_product_create(
            import_process=import_process,
            product_data=product_data,
        )
        if not import_instance.created:
            if sku:
                raise ValueError(f"Product with sku {sku!r} already exists.")
            raise ValueError("Product was not created.")

        if any(
            [
                active is not None,
                ean_code is not None,
                translations is not None,
                prices is not None,
                properties is not None,
                images is not None,
                sales_channel_view_ids is not None,
            ]
        ):
            run_upsert_product_updates(
                import_process=import_process,
                multi_tenant_company=multi_tenant_company,
                product=import_instance.instance,
                vat_rate_id=None,
                vat_rate=None,
                active=active,
                ean_code=ean_code,
                translations=translations,
                prices=prices,
                properties=properties,
                images=images,
                sales_channel_view_ids=sales_channel_view_ids,
            )

        return build_create_product_payload(
            product=import_instance.instance,
            sku_was_generated=sku_was_generated,
        )
