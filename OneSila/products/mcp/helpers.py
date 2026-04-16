from __future__ import annotations

from decimal import Decimal

from core.models.multi_tenant import MultiTenantCompany
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Exists, OuterRef, Prefetch, QuerySet
from get_absolute_url.helpers import generate_absolute_url

from imports_exports.factories.exports.helpers import (
    serialize_product_translation_payload,
    serialize_sales_channel_payload,
    serialize_product_property_value,
)
from media.models import Media, MediaProductThrough
from products.mcp.types import (
    ProductAssignedPropertyPayload,
    ProductAssignedPropertyValuePayload,
    ProductAssignedPropertyValueTranslationPayload,
    ProductDetailPayload,
    ProductImagePayload,
    ProductInspectorIssuePayload,
    ProductInspectorPayload,
    ProductPricePayload,
    ProductPropertyRequirementPayload,
    ProductPropertyRequirementsPayload,
    ProductRequirementProductTypePayload,
    ProductTranslationPayload,
    ProductSummaryPayload,
    ProductVatRatePayload,
    SalesChannelReferencePayload,
)
from products.models import Product, ProductTranslation
from products_inspector.models import InspectorBlock
from products_inspector.constants import GREEN, ORANGE, RED
from properties.mcp.helpers import serialize_property_reference
from properties.models import ProductPropertiesRule, ProductPropertiesRuleItem, ProductProperty
from sales_prices.models import SalesPrice


PRODUCT_TYPE_LABELS = {
    code: str(label)
    for code, label in Product.PRODUCT_TYPE_CHOICES
}
PRODUCT_INSPECTOR_STATUS_LABELS = {
    GREEN: "green",
    ORANGE: "orange",
    RED: "red",
}
PRODUCT_INSPECTOR_ISSUE_METADATA = {
    101: {
        "title": "Products Missing Images",
        "description": "Add at least one image to these products.",
    },
    102: {
        "title": "Products Missing Default Prices",
        "description": "Ensure these products have valid default prices.",
    },
    103: {
        "title": "Products with Inactive Bills of Materials",
        "description": "Activate all bills of materials for these manufacturable products.",
    },
    104: {
        "title": "Bundle Products with Inactive Items",
        "description": "Activate all items in these bundle products.",
    },
    105: {
        "title": "Products Missing Variations",
        "description": "Add required variations to these configurable products.",
    },
    106: {
        "title": "Bundle Products Missing Items",
        "description": "Add items to these bundle products.",
    },
    107: {
        "title": "Manufacturable Products Missing Bills of Materials",
        "description": "Add bills of materials to these manufacturable products.",
    },
    108: {
        "title": "Products Missing Supplier Products",
        "description": "Add supplier products to these products.",
    },
    109: {
        "title": "Products Missing EAN Codes",
        "description": "Provide EAN codes for these products.",
    },
    110: {
        "title": "Product Type Missing",
        "description": "Assign a product type to these products.",
    },
    111: {
        "title": "Products Missing Required Properties",
        "description": "Assign all required properties to these products.",
    },
    112: {
        "title": "Products Missing Optional Properties",
        "description": "Assign optional properties to these products as needed.",
    },
    113: {
        "title": "Supplier Products Missing Required Prices",
        "description": "Add required prices to these supplier products.",
    },
    114: {
        "title": "Products Missing Stock",
        "description": "Ensure these products have stock or allow backorder.",
    },
    115: {
        "title": "Products Missing Lead Time When Out of Stock",
        "description": "Specify lead times for these products when out of stock.",
    },
    116: {
        "title": "Manual Price List Prices Missing Override Prices",
        "description": "Add override prices to manual price list prices where auto-update is disabled.",
    },
    117: {
        "title": "Variation Product Type Mismatch",
        "description": "Ensure all variations have the same product type.",
    },
    118: {
        "title": "Items with Different Product Types",
        "description": "Ensure all items have the same product type.",
    },
    119: {
        "title": "Bills of Materials with Different Product Types",
        "description": "Ensure all bills of materials have the same product type.",
    },
    120: {
        "title": "Items with Missing Mandatory Information",
        "description": "Resolve missing mandatory information in these items' inspectors.",
    },
    121: {
        "title": "Variations with Missing Mandatory Information",
        "description": "Resolve missing mandatory information in these variations' inspectors.",
    },
    122: {
        "title": "Bills of Materials with Missing Mandatory Information",
        "description": "Resolve missing mandatory information in these bills of materials' inspectors.",
    },
    123: {
        "title": "Configurable Products with Duplicate Variations",
        "description": "Ensure variations in these configurable products have unique required properties.",
    },
    124: {
        "title": "Configurable Product Missing Rule Configuration",
        "description": "Define at least one configurator required item for these configurable products.",
    },
    125: {
        "title": "Products with Amazon Validation Issues",
        "description": "Review Amazon validation issues for these products in the Amazon tab.",
    },
    126: {
        "title": "Products with Amazon Remote Issues",
        "description": "Check the Amazon tab for remote issues reported by Amazon and resolve them.",
    },
    127: {
        "title": "Products Missing Required Document Types",
        "description": "Required document types are missing for one or more assigned marketplaces.",
    },
    128: {
        "title": "Products Missing Optional Document Types",
        "description": "Optional document types are missing for one or more assigned marketplaces.",
    },
}


def _get_product_image_exists_queryset():
    return MediaProductThrough.objects.filter(
        product_id=OuterRef("pk"),
        media__type=Media.IMAGE,
    )


def _get_product_image_prefetch() -> Prefetch:
    return Prefetch(
        "mediaproductthrough_set",
        queryset=(
            MediaProductThrough.objects.filter(media__type=Media.IMAGE)
            .select_related("media", "sales_channel")
            .order_by("sort_order", "id")
        ),
    )


def get_product_type_label(*, type_value: str) -> str:
    return PRODUCT_TYPE_LABELS[type_value]


def get_product_summary_queryset(*, multi_tenant_company: MultiTenantCompany) -> QuerySet[Product]:
    return (
        Product.objects.filter(multi_tenant_company=multi_tenant_company)
        .with_translated_name(language_code=multi_tenant_company.language)
        .select_related("vat_rate", "inspector")
        .annotate(has_images=Exists(_get_product_image_exists_queryset()))
        .prefetch_related(_get_product_image_prefetch())
    )


def get_product_detail_queryset(*, multi_tenant_company: MultiTenantCompany) -> QuerySet[Product]:
    product_property_queryset = (
        ProductProperty.objects.select_related("property", "value_select")
        .prefetch_related(
            "productpropertytexttranslation_set",
            "property__propertytranslation_set",
            "value_select__propertyselectvaluetranslation_set",
            "value_multi_select",
            "value_multi_select__propertyselectvaluetranslation_set",
        )
        .order_by("id")
    )
    sales_price_queryset = SalesPrice.objects.select_related("currency").order_by("id")
    translation_queryset = (
        ProductTranslation.objects.select_related("sales_channel")
        .prefetch_related("bullet_points")
        .order_by("language", "sales_channel_id", "id")
    )
    inspector_block_queryset = InspectorBlock.objects.order_by("error_code", "id")

    return get_product_summary_queryset(
        multi_tenant_company=multi_tenant_company,
    ).prefetch_related(
        Prefetch("productproperty_set", queryset=product_property_queryset),
        Prefetch("salesprice_set", queryset=sales_price_queryset),
        Prefetch("translations", queryset=translation_queryset),
        Prefetch("inspector__blocks", queryset=inspector_block_queryset),
    )


def _get_inspector_instance(*, product: Product):
    try:
        return product.inspector
    except ObjectDoesNotExist:
        return None


def _serialize_inspector_issue(*, block: InspectorBlock) -> ProductInspectorIssuePayload:
    metadata = PRODUCT_INSPECTOR_ISSUE_METADATA.get(
        block.error_code,
        {
            "title": str(block.get_error_code_display()),
            "description": str(block.get_error_code_display()),
        },
    )
    return {
        "code": block.error_code,
        "title": metadata["title"],
        "description": metadata["description"],
        "fixing_message": block.fixing_message or None,
    }


def serialize_product_inspector_issues(*, product: Product) -> list[ProductInspectorIssuePayload]:
    inspector = _get_inspector_instance(product=product)
    if inspector is None:
        return []

    return [
        _serialize_inspector_issue(block=block)
        for block in inspector.blocks.all()
        if not block.successfully_checked
    ]


def serialize_product_inspector(*, product: Product) -> ProductInspectorPayload:
    inspector = _get_inspector_instance(product=product)
    if inspector is None:
        return {
            "has_inspector": False,
            "has_missing_required_information": False,
            "has_missing_optional_information": False,
            "has_missing_information": False,
            "status_code": None,
            "status_label": None,
            "issues": [],
        }

    has_missing_required_information = bool(inspector.has_missing_information)
    has_missing_optional_information = bool(inspector.has_missing_optional_information)
    has_missing_information = has_missing_required_information or has_missing_optional_information

    if has_missing_required_information:
        status_code = RED
    elif has_missing_optional_information:
        status_code = ORANGE
    else:
        status_code = GREEN

    return {
        "has_inspector": True,
        "has_missing_required_information": has_missing_required_information,
        "has_missing_optional_information": has_missing_optional_information,
        "has_missing_information": has_missing_information,
        "status_code": status_code,
        "status_label": PRODUCT_INSPECTOR_STATUS_LABELS[status_code],
        "issues": serialize_product_inspector_issues(product=product),
    }


def _serialize_product_image(*, assignment: MediaProductThrough) -> ProductImagePayload:
    return {
        "image_url": assignment.media.image_url(),
        "thumbnail_url": assignment.media.onesila_thumbnail_url(),
        "type": assignment.media.image_type,
        "title": assignment.media.title,
        "description": assignment.media.description,
        "is_main_image": assignment.is_main_image,
        "sort_order": assignment.sort_order,
        "sales_channel": serialize_sales_channel_reference(
            sales_channel=assignment.sales_channel,
        ),
    }


def _get_image_assignments(*, product: Product) -> list[MediaProductThrough]:
    return list(product.mediaproductthrough_set.all())


def get_product_thumbnail_url(*, product: Product) -> str | None:
    assignments = _get_image_assignments(product=product)
    if not assignments:
        return None

    preferred_assignments = sorted(
        assignments,
        key=lambda item: (
            item.sales_channel_id is not None,
            not item.is_main_image,
            item.sort_order,
            item.id,
        ),
    )
    return preferred_assignments[0].media.onesila_thumbnail_url()


def build_product_onesila_paths(*, product: Product) -> tuple[str, str]:
    onesila_path = f"/products/product/{product.global_id}"
    onesila_url = f"{generate_absolute_url(trailing_slash=False).rstrip('/')}{onesila_path}"
    return onesila_path, onesila_url


def serialize_product_images(*, product: Product) -> list[ProductImagePayload]:
    return [
        _serialize_product_image(assignment=assignment)
        for assignment in _get_image_assignments(product=product)
    ]


def _format_decimal(*, value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def serialize_product_prices(*, product: Product) -> list[ProductPricePayload]:
    return [
        {
            "currency": sales_price.currency.iso_code,
            "rrp": _format_decimal(value=sales_price.rrp),
            "price": _format_decimal(value=sales_price.price),
        }
        for sales_price in product.salesprice_set.all()
    ]


def serialize_sales_channel_reference(*, sales_channel) -> SalesChannelReferencePayload | None:
    if sales_channel is None:
        return None

    payload = serialize_sales_channel_payload(sales_channel=sales_channel)
    payload["active"] = bool(sales_channel.active)
    return payload


def serialize_product_translations(*, product: Product) -> list[ProductTranslationPayload]:
    return [
        {
            **{
                key: value
                for key, value in serialize_product_translation_payload(
                    translation=translation,
                ).items()
                if key != "sales_channel"
            },
            "sales_channel": serialize_sales_channel_reference(
                sales_channel=translation.sales_channel,
            ),
        }
        for translation in sorted(
            product.translations.all(),
            key=lambda item: (
                item.language,
                item.sales_channel_id is not None,
                item.sales_channel.hostname if item.sales_channel_id else "",
                item.id,
            ),
        )
    ]


def serialize_vat_rate(*, product: Product) -> ProductVatRatePayload | None:
    if product.vat_rate_id is None:
        return None

    return {
        "id": product.vat_rate.id,
        "name": product.vat_rate.name,
        "rate": product.vat_rate.rate,
    }


def _normalize_value(*, value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_normalize_value(value=item) for item in value]
    return value


def _normalize_property_value_payload(*, raw_value: dict) -> ProductAssignedPropertyValuePayload:
    translations: list[ProductAssignedPropertyValueTranslationPayload] = [
        {
            "language": str(translation["language"]).lower(),
            "value": _normalize_value(value=translation.get("value")),
        }
        for translation in raw_value.get("translations", [])
    ]
    return {
        "id": raw_value.get("id"),
        "value": _normalize_value(value=raw_value.get("value")),
        "translations": translations,
    }


def serialize_product_assigned_properties(*, product: Product) -> list[ProductAssignedPropertyPayload]:
    language = product.multi_tenant_company.language
    payloads: list[ProductAssignedPropertyPayload] = []

    for product_property in product.productproperty_set.all():
        active_value, values = serialize_product_property_value(
            product_property=product_property,
            language=language,
            include_translations=True,
            include_value_ids=True,
        )
        payloads.append(
            {
                "property": serialize_property_reference(property_instance=product_property.property),
                "value": _normalize_value(value=active_value),
                "values": [
                    _normalize_property_value_payload(raw_value=value)
                    for value in values
                ],
            }
        )

    return payloads


def _serialize_current_value_summary(*, value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        non_empty_values = [str(item) for item in value if item not in (None, "")]
        return ", ".join(non_empty_values) or None
    if isinstance(value, str):
        stripped_value = value.strip()
        return stripped_value or None
    return str(value)


def _value_has_data(*, value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_value_has_data(value=item) for item in value)
    return True


def _get_requirement_key(*, property_internal_name: str | None, property_id: int) -> str:
    return property_internal_name or f"property_{property_id}"


def _serialize_requirement_product_type(
    *,
    property_payloads: list[ProductAssignedPropertyPayload],
) -> ProductRequirementProductTypePayload | None:
    for property_payload in property_payloads:
        property_reference = property_payload["property"]
        if not property_reference["is_product_type"]:
            continue

        select_value_id = next(
            (
                value_payload["id"]
                for value_payload in property_payload["values"]
                if value_payload["id"] is not None
            ),
            None,
        )
        if select_value_id is None:
            return None

        return {
            "id": select_value_id,
            "select_value": _serialize_current_value_summary(
                value=property_payload["value"],
            ) or "",
        }

    return None


def _get_product_properties_rule(
    *,
    product_type_id: int | None,
    product: Product,
) -> ProductPropertiesRule | None:
    if product_type_id is None:
        return None

    return (
        ProductPropertiesRule.objects.filter(
            multi_tenant_company=product.multi_tenant_company,
            product_type_id=product_type_id,
            sales_channel__isnull=True,
        )
        .prefetch_related("items__property__propertytranslation_set")
        .first()
    )


def _serialize_property_requirement(
    *,
    rule_item: ProductPropertiesRuleItem,
    property_payload_map: dict[int, ProductAssignedPropertyPayload],
) -> ProductPropertyRequirementPayload:
    assigned_property = property_payload_map.get(rule_item.property_id)
    current_value = assigned_property["value"] if assigned_property else None

    return {
        "property_id": rule_item.property_id,
        "property_name": rule_item.property.name,
        "requirement_type": rule_item.type,
        "effectively_required": rule_item.type != ProductPropertiesRuleItem.OPTIONAL,
        "has_value": _value_has_data(value=current_value),
        "current_value_summary": _serialize_current_value_summary(value=current_value),
    }


def serialize_product_property_requirements(
    *,
    product: Product,
    property_payloads: list[ProductAssignedPropertyPayload],
) -> ProductPropertyRequirementsPayload:
    product_type = _serialize_requirement_product_type(
        property_payloads=property_payloads,
    )
    if product_type is None:
        return {
            "product_type": None,
            "requirements": {},
        }

    property_payload_map = {
        property_payload["property"]["id"]: property_payload
        for property_payload in property_payloads
    }
    product_rule = _get_product_properties_rule(
        product_type_id=product_type["id"],
        product=product,
    )
    if product_rule is None:
        return {
            "product_type": product_type,
            "requirements": {},
        }

    requirements = {
        _get_requirement_key(
            property_internal_name=rule_item.property.internal_name,
            property_id=rule_item.property_id,
        ): _serialize_property_requirement(
            rule_item=rule_item,
            property_payload_map=property_payload_map,
        )
        for rule_item in product_rule.items.all()
    }
    return {
        "product_type": product_type,
        "requirements": requirements,
    }


def serialize_product_summary(
    *,
    product: Product,
    inspector_data: ProductInspectorPayload | None = None,
) -> ProductSummaryPayload:
    if inspector_data is None:
        inspector_data = serialize_product_inspector(product=product)
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "type": product.type,
        "type_label": get_product_type_label(type_value=product.type),
        "active": product.active,
        "vat_rate": product.vat_rate.rate if product.vat_rate_id else None,
        "thumbnail_url": get_product_thumbnail_url(product=product),
        "has_images": bool(getattr(product, "has_images", False) or _get_image_assignments(product=product)),
        "has_missing_required_information": inspector_data["has_missing_required_information"],
        "has_missing_optional_information": inspector_data["has_missing_optional_information"],
        "has_missing_information": inspector_data["has_missing_information"],
    }


def serialize_product_detail(*, product: Product) -> ProductDetailPayload:
    inspector_data = serialize_product_inspector(product=product)
    serialized_properties = serialize_product_assigned_properties(product=product)
    onesila_path, onesila_url = build_product_onesila_paths(product=product)
    return {
        **serialize_product_summary(product=product, inspector_data=inspector_data),
        "global_id": product.global_id,
        "onesila_path": onesila_path,
        "onesila_url": onesila_url,
        "allow_backorder": product.allow_backorder,
        "vat_rate_data": serialize_vat_rate(product=product),
        "inspector": inspector_data,
        "property_requirements": serialize_product_property_requirements(
            product=product,
            property_payloads=serialized_properties,
        ),
        "translations": serialize_product_translations(product=product),
        "images": serialize_product_images(product=product),
        "properties": serialized_properties,
        "prices": serialize_product_prices(product=product),
    }
