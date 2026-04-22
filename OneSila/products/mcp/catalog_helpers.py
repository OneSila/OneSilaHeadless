from __future__ import annotations

from core.models.multi_tenant import MultiTenantCompany
from imports_exports.factories.exports.helpers import serialize_sales_channel_payload

from products.mcp.types import (
    GetProductTypesPayload,
    SearchSalesChannelsPayload,
    SalesChannelViewSummaryPayload,
    GetVatRatesPayload,
    SalesChannelReferencePayload,
    VatRateOptionPayload,
)
from properties.mcp.helpers import (
    get_property_select_value_detail_queryset,
    serialize_property_reference,
    serialize_property_select_value_summary,
)
from properties.models import Property, PropertySelectValue
from sales_channels.models import SalesChannel
from taxes.models import VatRate


def get_product_type_property(*, multi_tenant_company: MultiTenantCompany) -> Property:
    try:
        return Property.objects.get(
            multi_tenant_company=multi_tenant_company,
            is_product_type=True,
        )
    except Property.DoesNotExist as error:
        raise ValueError("Product type property is not configured for this company.") from error


def get_product_types_payload(*, multi_tenant_company: MultiTenantCompany) -> GetProductTypesPayload:
    product_type_property = get_product_type_property(
        multi_tenant_company=multi_tenant_company,
    )
    select_values = list(
        get_property_select_value_detail_queryset(
            multi_tenant_company=multi_tenant_company,
        )
        .filter(property=product_type_property)
        .order_by("id")
    )
    return {
        "count": len(select_values),
        "property": serialize_property_reference(property_instance=product_type_property),
        "results": [
            serialize_property_select_value_summary(select_value=select_value)
            for select_value in select_values
        ],
    }


def serialize_vat_rate_option(*, vat_rate: VatRate) -> VatRateOptionPayload:
    return {
        "id": vat_rate.id,
        "name": vat_rate.name,
        "rate": vat_rate.rate,
    }


def serialize_sales_channel_view_option(*, view) -> SalesChannelViewSummaryPayload:
    real_view = view.get_real_instance()
    return {
        "id": view.id,
        "name": view.name,
        "is_default": getattr(real_view, "is_default", None),
    }


def serialize_sales_channel_option(*, sales_channel: SalesChannel) -> SalesChannelReferencePayload:
    payload = serialize_sales_channel_payload(sales_channel=sales_channel)
    payload["active"] = bool(sales_channel.active)
    payload["views"] = [
        serialize_sales_channel_view_option(view=view)
        for view in sorted(sales_channel.saleschannelview_set.all(), key=lambda item: item.id)
    ]
    return payload


def search_sales_channels_payload(
    *,
    multi_tenant_company: MultiTenantCompany,
    search: str | None,
    active: bool | None,
    type_value: str | None,
    limit: int,
    offset: int,
) -> SearchSalesChannelsPayload:
    queryset = SalesChannel.objects.filter(
        multi_tenant_company=multi_tenant_company,
    ).prefetch_related("saleschannelview_set")
    if search:
        queryset = queryset.filter(hostname__icontains=search)
    if active is not None:
        queryset = queryset.filter(active=active)

    sales_channels = list(queryset.order_by("hostname", "id"))
    serialized_channels = [
        serialize_sales_channel_option(sales_channel=sales_channel)
        for sales_channel in sales_channels
    ]
    if type_value:
        normalized_type = type_value.strip().lower()
        serialized_channels = [
            payload
            for payload in serialized_channels
            if payload["type"].lower() == normalized_type
        ]

    total_count = len(serialized_channels)
    paginated_channels = serialized_channels[offset: offset + limit + 1]
    has_more = len(paginated_channels) > limit

    return {
        "total_count": total_count,
        "has_more": has_more,
        "offset": offset,
        "limit": limit,
        "results": paginated_channels[:limit],
    }


def get_vat_rates_payload(*, multi_tenant_company: MultiTenantCompany) -> GetVatRatesPayload:
    vat_rates = list(
        VatRate.objects.filter(multi_tenant_company=multi_tenant_company)
        .order_by("rate", "name", "id")
    )
    return {
        "count": len(vat_rates),
        "results": [
            serialize_vat_rate_option(vat_rate=vat_rate)
            for vat_rate in vat_rates
        ],
    }


def get_product_type_match(
    *,
    multi_tenant_company: MultiTenantCompany,
    product_type_id: int | None,
    product_type_value: str | None,
) -> PropertySelectValue | None:
    if product_type_id is None and not product_type_value:
        return None

    queryset = PropertySelectValue.objects.filter(
        multi_tenant_company=multi_tenant_company,
        property__is_product_type=True,
    )

    if product_type_id is not None:
        product_type = queryset.filter(id=product_type_id).first()
        if product_type is None:
            raise ValueError(f"Product type with id {product_type_id} not found.")
        return product_type

    product_type_value = str(product_type_value).strip()
    matching_ids = list(
        queryset.filter(
            propertyselectvaluetranslation__value__iexact=product_type_value,
        )
        .order_by("id")
        .values_list("id", flat=True)
        .distinct()[:2]
    )
    if not matching_ids:
        raise ValueError(
            f"Product type {product_type_value!r} not found. Use get_company_details with show_product_types=true first."
        )
    if len(matching_ids) > 1:
        raise ValueError(
            f"Multiple product types matched {product_type_value!r}. Use get_company_details with show_product_types=true and pass product_type_id."
        )
    return queryset.get(id=matching_ids[0])


def get_vat_rate_match(
    *,
    multi_tenant_company: MultiTenantCompany,
    vat_rate_id: int | None,
    vat_rate: int | None,
) -> VatRate | None:
    if vat_rate_id is None and vat_rate is None:
        return None

    queryset = VatRate.objects.filter(multi_tenant_company=multi_tenant_company)

    if vat_rate_id is not None:
        vat_rate_instance = queryset.filter(id=vat_rate_id).first()
        if vat_rate_instance is None:
            raise ValueError(f"VAT rate with id {vat_rate_id} not found.")
        return vat_rate_instance

    vat_rate_instance = queryset.filter(rate=vat_rate).first()
    if vat_rate_instance is None:
        raise ValueError(
            f"VAT rate {vat_rate!r} not found. Use get_company_details with show_vat_rates=true first."
        )
    return vat_rate_instance
