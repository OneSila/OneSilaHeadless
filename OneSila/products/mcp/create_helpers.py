from __future__ import annotations

from types import SimpleNamespace

from core.models.multi_tenant import MultiTenantCompany
from currencies.models import Currency
from imports_exports.factories.products import ImportProductInstance
from products.mcp.catalog_helpers import get_product_type_match, get_vat_rate_match
from products.mcp.types import CreateProductPayload
from products.mcp.update_helpers import get_product_detail_payload


def build_product_create_process(*, multi_tenant_company: MultiTenantCompany):
    return SimpleNamespace(
        multi_tenant_company=multi_tenant_company,
        create_only=True,
        update_only=False,
        override_only=False,
    )


def get_default_company_currency_code(*, multi_tenant_company: MultiTenantCompany) -> str:
    currency = Currency.objects.filter(
        multi_tenant_company=multi_tenant_company,
        is_default_currency=True,
    ).first()
    if currency is None:
        raise ValueError(
            "No default company currency is configured. Add a default currency before creating product prices."
        )
    return currency.iso_code


def run_product_create(
    *,
    multi_tenant_company: MultiTenantCompany,
    product_data: dict,
):
    import_instance = ImportProductInstance(
        product_data,
        import_process=build_product_create_process(
            multi_tenant_company=multi_tenant_company,
        ),
    )
    import_instance.process()
    return import_instance


def build_create_product_payload(
    *,
    multi_tenant_company: MultiTenantCompany,
    product,
    sku_was_generated: bool,
) -> CreateProductPayload:
    return {
        "created": True,
        "sku_was_generated": sku_was_generated,
        "product": get_product_detail_payload(
            multi_tenant_company=multi_tenant_company,
            product=product,
        ),
    }


def build_create_product_data(
    *,
    multi_tenant_company: MultiTenantCompany,
    name: str,
    product_type_code: str,
    sku: str | None,
    product_type_id: int | None,
    product_type_value: str | None,
    price,
    rrp,
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

    if price is not None or rrp is not None:
        product_data["prices"] = [
            {
                "currency": get_default_company_currency_code(
                    multi_tenant_company=multi_tenant_company,
                ),
                "price": price,
                "rrp": rrp,
            }
        ]

    return product_data, sku_was_generated
