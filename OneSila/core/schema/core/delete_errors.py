from collections import defaultdict
from typing import Iterable

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import ProtectedError
from django.utils.translation import gettext_lazy as _


def _describe_property(*, property_id: int | None) -> str:
    if property_id is None:
        return _("Property")

    from properties.models import Property

    translated_name = (
        Property.objects.all().with_translated_name()
        .filter(pk=property_id)
        .values_list("translated_name", flat=True)
        .first()
    )
    if translated_name:
        return translated_name

    property_obj = Property._base_manager.filter(pk=property_id).first()
    if property_obj and property_obj.internal_name:
        return property_obj.internal_name

    return _("Property #%(pk)s") % {"pk": property_id}


def _describe_property_select_value(*, value_id: int | None) -> str:
    if value_id is None:
        return _("Property select value")

    from properties.models import Property, PropertySelectValue

    translated_value = (
        PropertySelectValue.objects.all().with_translated_value()
        .filter(pk=value_id)
        .values_list("translated_value", flat=True)
        .first()
    )
    if translated_value is None:
        translated_value = _("Value #%(pk)s") % {"pk": value_id}

    property_id = (
        PropertySelectValue._base_manager.filter(pk=value_id)
        .values_list("property_id", flat=True)
        .first()
    )
    property_name = _describe_property(property_id=property_id)
    return f"{translated_value} <{property_name}>"


def _describe_rule(*, rule_id: int | None) -> str:
    if rule_id is None:
        return _("Product properties rule")

    from properties.models import ProductPropertiesRule

    rule = (
        ProductPropertiesRule._base_manager.select_related("product_type")
        .filter(pk=rule_id)
        .first()
    )
    if rule is None:
        return _("Product properties rule #%(pk)s") % {"pk": rule_id}

    if rule.product_type_id:
        return _describe_property_select_value(value_id=rule.product_type_id)

    return _("Product type #%(pk)s") % {"pk": rule_id}


def _describe_rule_item(*, item_id: int | None) -> str:
    if item_id is None:
        return _("Product properties rule item")

    from properties.models import ProductPropertiesRuleItem

    item = (
        ProductPropertiesRuleItem._base_manager.select_related("property", "rule")
        .filter(pk=item_id)
        .first()
    )
    if item is None:
        return _("Product properties rule item #%(pk)s") % {"pk": item_id}

    return _describe_rule(rule_id=item.rule_id)


def _describe_product_property(*, product_property_id: int | None) -> str:
    if product_property_id is None:
        return _("Product property")

    from properties.models import ProductProperty

    row = ProductProperty._base_manager.filter(pk=product_property_id).values_list(
        "product__sku",
        "property_id",
    ).first()
    if row is None:
        return _("Product property #%(pk)s") % {"pk": product_property_id}

    product_sku, _property_id = row
    product_sku = product_sku or _("No SKU")
    return f"{product_sku}"


def _describe_protected_instance(instance: models.Model) -> str:
    model_name = instance._meta.model_name

    if model_name == "property":
        return _describe_property(property_id=instance.pk)

    if model_name == "propertyselectvalue":
        return _describe_property_select_value(value_id=instance.pk)

    if model_name == "productpropertiesrule":
        return _describe_rule(rule_id=instance.pk)

    if model_name == "productpropertiesruleitem":
        return _describe_rule_item(item_id=instance.pk)

    if model_name == "productproperty":
        return _describe_product_property(product_property_id=instance.pk)

    frontend_name = getattr(instance, "frontend_name", None)
    if frontend_name:
        return str(frontend_name)

    return f"{instance._meta.verbose_name} #{instance.pk}"


def _get_reference_section_title(*, model_name: str, verbose_name_plural: str) -> str:
    if model_name == "productpropertiesruleitem":
        return _("is still used in rules")
    if model_name == "propertyselectvalue":
        return _("is still used in values")
    if model_name == "productproperty":
        return _("is still used in products")
    return verbose_name_plural


def build_protected_delete_validation_error(*, protected_objects: Iterable[models.Model]) -> ValidationError:
    """
    Convert Django's ProtectedError into a GraphQL-safe ValidationError.

    We avoid stringifying the protected model instances directly because their __str__
    implementations may touch lazy relations and trigger synchronous DB access while
    Strawberry formats the exception.
    """
    grouped_labels: dict[str, list[str]] = defaultdict(list)
    section_titles: dict[str, str] = {}

    for protected_object in protected_objects:
        key = protected_object._meta.model_name
        grouped_labels[key].append(
            _describe_protected_instance(protected_object)
        )
        section_titles[key] = _get_reference_section_title(
            model_name=protected_object._meta.model_name,
            verbose_name_plural=protected_object._meta.verbose_name_plural,
        )

    if not grouped_labels:
        return ValidationError(_("This object cannot be deleted because it is still referenced."))

    parts = []
    for model_name in sorted(grouped_labels):
        label = section_titles[model_name]
        entries = sorted(grouped_labels[model_name])
        if len(entries) > 20:
            remaining = len(entries) - 20
            entries = [*entries[:20], _("+%(count)s others") % {"count": remaining}]
        parts.append(f"{label}: {', '.join(entries)}")

    return ValidationError(
        _("This object cannot be deleted because it is still referenced by:\n%(references)s")
        % {"references": "\n".join(parts)}
    )


def raise_protected_delete_validation_error(*, protected_error: ProtectedError) -> None:
    raise build_protected_delete_validation_error(
        protected_objects=protected_error.protected_objects,
    )
