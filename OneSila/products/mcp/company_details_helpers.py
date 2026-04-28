from __future__ import annotations

from currencies.models import Currency
from core.models.multi_tenant import MultiTenantCompany
from products.mcp.catalog_helpers import (
    get_product_type_property,
    get_vat_rates_payload,
)
from products.mcp.types import (
    CompanyCurrenciesPayload,
    CompanyCurrencyPayload,
    CompanyDetailsPayload,
    CompanyWorkflowPayload,
    CompanyWorkflowsPayload,
    CompanyProductTypePayload,
    CompanyProductTypesPayload,
    WorkflowStateReferencePayload,
)
from properties.mcp.helpers import (
    serialize_company_languages,
    serialize_property_reference,
)
from properties.models import PropertySelectValue
from workflows.models import Workflow


def serialize_company_currency(*, currency: Currency) -> CompanyCurrencyPayload:
    return {
        "id": currency.id,
        "iso_code": currency.iso_code,
        "name": currency.name,
        "symbol": currency.symbol,
        "is_default": bool(currency.is_default_currency),
        "inherits_from_iso_code": currency.inherits_from.iso_code if currency.inherits_from else None,
    }


def get_company_currencies_payload(*, multi_tenant_company: MultiTenantCompany) -> CompanyCurrenciesPayload:
    currencies = list(
        Currency.objects.filter(multi_tenant_company=multi_tenant_company)
        .select_related("inherits_from")
        .order_by("-is_default_currency", "iso_code", "id")
    )
    default_currency = next((currency for currency in currencies if currency.is_default_currency), None)
    return {
        "count": len(currencies),
        "default_currency_code": default_currency.iso_code if default_currency else None,
        "results": [
            serialize_company_currency(currency=currency)
            for currency in currencies
        ],
    }


def serialize_company_product_type(
    *,
    select_value: PropertySelectValue,
    include_translations: bool,
    include_usage_counts: bool,
) -> CompanyProductTypePayload:
    payload: CompanyProductTypePayload = {
        "id": select_value.id,
        "value": select_value.value,
    }
    if include_translations:
        payload["translations"] = [
            {
                "language": translation.language,
                "value": translation.value,
            }
            for translation in select_value.propertyselectvaluetranslation_set.all()
        ]
    if include_usage_counts:
        payload["usage_count"] = getattr(select_value, "usage_count", 0)
    return payload


def get_company_product_types_payload(
    *,
    multi_tenant_company: MultiTenantCompany,
    include_translations: bool,
    include_usage_counts: bool,
) -> CompanyProductTypesPayload:
    product_type_property = get_product_type_property(
        multi_tenant_company=multi_tenant_company,
    )
    queryset = (
        PropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
            property=product_type_property,
        )
        .select_related("property")
        .prefetch_related(
            "propertyselectvaluetranslation_set",
            "property__propertytranslation_set",
        )
        .order_by("id")
    )
    if include_usage_counts:
        queryset = queryset.with_usage_count(multi_tenant_company_id=multi_tenant_company.id)

    select_values = list(queryset)
    return {
        "count": len(select_values),
        "property": serialize_property_reference(property_instance=product_type_property),
        "results": [
            serialize_company_product_type(
                select_value=select_value,
                include_translations=include_translations,
                include_usage_counts=include_usage_counts,
            )
            for select_value in select_values
        ],
    }


def serialize_workflow_state_reference(*, state) -> WorkflowStateReferencePayload:
    return {
        "id": state.id,
        "name": state.value,
        "code": state.code,
        "is_default": bool(state.is_default),
    }


def serialize_company_workflow(*, workflow: Workflow) -> CompanyWorkflowPayload:
    return {
        "id": workflow.id,
        "name": workflow.name,
        "code": workflow.code,
        "states": [
            serialize_workflow_state_reference(state=state)
            for state in workflow.states.all()
        ],
    }


def get_company_workflows_payload(*, multi_tenant_company: MultiTenantCompany) -> CompanyWorkflowsPayload:
    workflows = list(
        Workflow.objects.filter(multi_tenant_company=multi_tenant_company)
        .prefetch_related("states")
        .order_by("sort_order", "name", "id")
    )
    return {
        "count": len(workflows),
        "results": [
            serialize_company_workflow(workflow=workflow)
            for workflow in workflows
        ],
    }


def get_company_details_payload(
    *,
    multi_tenant_company: MultiTenantCompany,
    show_languages: bool,
    show_product_types: bool,
    show_product_types_translations: bool,
    show_product_types_usage_counts: bool,
    show_vat_rates: bool,
    show_currencies: bool,
    show_workflows: bool,
) -> CompanyDetailsPayload:
    include_product_types = (
        show_product_types
        or show_product_types_translations
        or show_product_types_usage_counts
    )
    if not any(
        [
            show_languages,
            include_product_types,
            show_vat_rates,
            show_currencies,
            show_workflows,
        ]
    ):
        return {
            "message": (
                "Set one or more show_* flags so the tool returns only the company "
                "reference data you need."
            ),
        }

    payload: CompanyDetailsPayload = {}
    if show_languages:
        payload["languages"] = serialize_company_languages(
            multi_tenant_company=multi_tenant_company,
        )
    if include_product_types:
        payload["product_types"] = get_company_product_types_payload(
            multi_tenant_company=multi_tenant_company,
            include_translations=show_product_types_translations,
            include_usage_counts=show_product_types_usage_counts,
        )
    if show_vat_rates:
        payload["vat_rates"] = get_vat_rates_payload(
            multi_tenant_company=multi_tenant_company,
        )
    if show_currencies:
        payload["currencies"] = get_company_currencies_payload(
            multi_tenant_company=multi_tenant_company,
        )
    if show_workflows:
        payload["workflows"] = get_company_workflows_payload(
            multi_tenant_company=multi_tenant_company,
        )
    return payload
