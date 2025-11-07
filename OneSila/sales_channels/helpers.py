from django.db import models

from sales_channels.integrations.magento2.models import MagentoSalesChannel
from typing import Iterable, Optional

from sales_channels.models import RemoteProduct


def get_all_product_rules_for_sales_channel(*, sales_channel):
    """Return channel-specific rules plus defaults without duplicates."""
    from properties.models import ProductPropertiesRule

    if sales_channel is None:
        raise ValueError("sales_channel must be provided")

    multi_tenant_company = sales_channel.multi_tenant_company

    channel_rules = list(
        ProductPropertiesRule.objects.filter(
            multi_tenant_company=multi_tenant_company,
            sales_channel=sales_channel,
        )
    )

    product_type_ids = {rule.product_type_id for rule in channel_rules}

    fallback_rules = list(
        ProductPropertiesRule.objects.filter(
            multi_tenant_company=multi_tenant_company,
            sales_channel__isnull=True,
        ).exclude(product_type_id__in=product_type_ids)
    )

    return channel_rules + fallback_rules


def get_preferred_product_rule_for_sales_channel(*, rule, sales_channel):
    """Return channel-specific rule when available for the same product type."""
    from properties.models import ProductPropertiesRule

    if rule is None or sales_channel is None:
        return rule

    if getattr(rule, "sales_channel_id", None) == sales_channel.id:
        return rule

    specialized_rule = ProductPropertiesRule.objects.filter(
        multi_tenant_company=rule.multi_tenant_company,
        product_type=rule.product_type,
        sales_channel=sales_channel,
    ).first()

    return specialized_rule or rule


def _rebuild_amazon_product_type_items(*, product_type, rule):
    from sales_channels.integrations.amazon.models import AmazonProductTypeItem

    existing_items = list(
        AmazonProductTypeItem.objects.filter(amazon_rule=product_type)
        .select_related(
            "local_instance",
            "remote_property",
            "remote_property__local_instance",
        )
    )

    AmazonProductTypeItem.objects.filter(amazon_rule=product_type).delete()

    rule_items_by_property = {
        item.property_id: item for item in rule.items.select_related("property")
    }

    for item in existing_items:
        property_id: Optional[int] = None

        if item.local_instance_id:
            property_id = item.local_instance.property_id
        elif getattr(item.remote_property, "local_instance_id", None):
            property_id = item.remote_property.local_instance_id

        if property_id is None:
            AmazonProductTypeItem.objects.create(
                multi_tenant_company=product_type.multi_tenant_company,
                sales_channel=product_type.sales_channel,
                amazon_rule=product_type,
                remote_property=item.remote_property,
                local_instance=None,
                remote_type=item.remote_type,
            )
            continue

        rule_item = rule_items_by_property.get(property_id)
        if not rule_item:
            continue

        AmazonProductTypeItem.objects.create(
            multi_tenant_company=product_type.multi_tenant_company,
            sales_channel=product_type.sales_channel,
            amazon_rule=product_type,
            remote_property=item.remote_property,
            local_instance=rule_item,
            remote_type=item.remote_type or rule_item.type,
        )


def rebind_amazon_product_type_to_rule(*, product_type, rule):
    if rule is None:
        return

    preferred_rule = get_preferred_product_rule_for_sales_channel(
        rule=rule,
        sales_channel=product_type.sales_channel,
    )

    if preferred_rule is None:
        return

    if product_type.local_instance_id != preferred_rule.id:
        type(product_type).objects.filter(pk=product_type.pk).update(
            local_instance=preferred_rule,
        )
        product_type.local_instance = preferred_rule

        _rebuild_amazon_product_type_items(product_type=product_type, rule=preferred_rule)


def rebind_amazon_product_types_for_rule(rule):
    if getattr(rule, "sales_channel_id", None) is None:
        return

    from properties.models import ProductPropertiesRule
    from sales_channels.integrations.amazon.models import AmazonProductType

    default_rule = ProductPropertiesRule.objects.filter(
        multi_tenant_company=rule.multi_tenant_company,
        product_type=rule.product_type,
        sales_channel__isnull=True,
    ).first()

    product_types = AmazonProductType.objects.filter(
        multi_tenant_company=rule.multi_tenant_company,
        sales_channel=rule.sales_channel,
    )

    if default_rule:
        product_types = product_types.filter(
            models.Q(local_instance=rule) | models.Q(local_instance=default_rule)
        )
    else:
        product_types = product_types.filter(local_instance=rule)

    for product_type in product_types.iterator():
        rebind_amazon_product_type_to_rule(product_type=product_type, rule=rule)


def _rebuild_ebay_product_type_items(*, product_type, rule):
    from sales_channels.integrations.ebay.models import EbayProductTypeItem

    existing_items = list(
        product_type.items.select_related(
            "local_instance",
            "ebay_property",
            "ebay_property__local_instance",
        )
    )

    product_type.items.all().delete()

    rule_items_by_property = {
        item.property_id: item for item in rule.items.select_related("property")
    }

    for item in existing_items:
        property_id: Optional[int] = None

        if item.local_instance_id:
            property_id = item.local_instance.property_id
        elif getattr(item.ebay_property, "local_instance_id", None):
            property_id = item.ebay_property.local_instance_id

        if property_id is None:
            EbayProductTypeItem.objects.create(
                multi_tenant_company=product_type.multi_tenant_company,
                sales_channel=product_type.sales_channel,
                product_type=product_type,
                ebay_property=item.ebay_property,
                local_instance=None,
                remote_type=item.remote_type,
            )
            continue

        rule_item = rule_items_by_property.get(property_id)
        if not rule_item:
            continue

        EbayProductTypeItem.objects.create(
            multi_tenant_company=product_type.multi_tenant_company,
            sales_channel=product_type.sales_channel,
            product_type=product_type,
            ebay_property=item.ebay_property,
            local_instance=rule_item,
            remote_type=item.remote_type or rule_item.type,
        )


def rebind_ebay_product_type_to_rule(*, product_type, rule):
    if rule is None:
        return

    preferred_rule = get_preferred_product_rule_for_sales_channel(
        rule=rule,
        sales_channel=product_type.sales_channel,
    )

    if preferred_rule is None:
        return

    if product_type.local_instance_id != preferred_rule.id:
        type(product_type).objects.filter(pk=product_type.pk).update(
            local_instance=preferred_rule,
        )
        product_type.local_instance = preferred_rule

        _rebuild_ebay_product_type_items(product_type=product_type, rule=preferred_rule)


def rebind_ebay_product_types_for_rule(rule):
    if getattr(rule, "sales_channel_id", None) is None:
        return

    from properties.models import ProductPropertiesRule
    from sales_channels.integrations.ebay.models import EbayProductType

    default_rule = ProductPropertiesRule.objects.filter(
        multi_tenant_company=rule.multi_tenant_company,
        product_type=rule.product_type,
        sales_channel__isnull=True,
    ).first()

    product_types = EbayProductType.objects.filter(
        multi_tenant_company=rule.multi_tenant_company,
        sales_channel=rule.sales_channel,
    )

    if default_rule:
        product_types = product_types.filter(
            models.Q(local_instance=rule) | models.Q(local_instance=default_rule)
        )
    else:
        product_types = product_types.filter(local_instance=rule)

    for product_type in product_types.iterator():
        rebind_ebay_product_type_to_rule(product_type=product_type, rule=rule)


def _rebuild_magento_attribute_set_items(*, attribute_set, rule):
    from sales_channels.integrations.magento2.models.properties import (
        MagentoAttributeSetAttribute,
    )

    existing_items = list(
        MagentoAttributeSetAttribute.objects.filter(magento_rule=attribute_set)
        .select_related(
            "local_instance",
            "local_instance__property",
            "remote_property",
            "remote_property__local_instance",
        )
    )

    MagentoAttributeSetAttribute.objects.filter(magento_rule=attribute_set).delete()

    rule_items_by_property = {
        item.property_id: item for item in rule.items.select_related("property")
    }

    for item in existing_items:
        property_id: Optional[int] = None

        if item.local_instance_id:
            property_id = item.local_instance.property_id
        elif getattr(item.remote_property, "local_instance_id", None):
            property_id = item.remote_property.local_instance_id

        if property_id is None:
            MagentoAttributeSetAttribute.objects.create(
                multi_tenant_company=attribute_set.multi_tenant_company,
                sales_channel=attribute_set.sales_channel,
                magento_rule=attribute_set,
                remote_property=item.remote_property,
                local_instance=None,
            )
            continue

        rule_item = rule_items_by_property.get(property_id)
        if not rule_item:
            continue

        MagentoAttributeSetAttribute.objects.create(
            multi_tenant_company=attribute_set.multi_tenant_company,
            sales_channel=attribute_set.sales_channel,
            magento_rule=attribute_set,
            remote_property=item.remote_property,
            local_instance=rule_item,
        )


def rebind_magento_attribute_set_to_rule(*, attribute_set, rule):
    if rule is None:
        return

    preferred_rule = get_preferred_product_rule_for_sales_channel(
        rule=rule,
        sales_channel=attribute_set.sales_channel,
    )

    if preferred_rule is None:
        return

    if attribute_set.local_instance_id != preferred_rule.id:
        type(attribute_set).objects.filter(pk=attribute_set.pk).update(
            local_instance=preferred_rule,
        )
        attribute_set.local_instance = preferred_rule

        _rebuild_magento_attribute_set_items(
            attribute_set=attribute_set,
            rule=preferred_rule,
        )


def rebind_magento_attribute_sets_for_rule(*, rule):
    if getattr(rule, "sales_channel_id", None) is None:
        return

    from properties.models import ProductPropertiesRule
    from sales_channels.integrations.magento2.models.properties import (
        MagentoAttributeSet,
    )

    default_rule = ProductPropertiesRule.objects.filter(
        multi_tenant_company=rule.multi_tenant_company,
        product_type=rule.product_type,
        sales_channel__isnull=True,
    ).first()

    attribute_sets = MagentoAttributeSet.objects.filter(
        multi_tenant_company=rule.multi_tenant_company,
        sales_channel=rule.sales_channel,
    )

    if default_rule:
        attribute_sets = attribute_sets.filter(
            models.Q(local_instance=rule) | models.Q(local_instance=default_rule)
        )
    else:
        attribute_sets = attribute_sets.filter(local_instance=rule)

    for attribute_set in attribute_sets.iterator():
        rebind_magento_attribute_set_to_rule(
            attribute_set=attribute_set,
            rule=rule,
        )


def mark_remote_products_for_feed_updates(*, product_ids: Iterable[int]) -> None:
    ids = {product_id for product_id in product_ids if product_id}
    if not ids:
        return
    RemoteProduct.objects.filter(
        local_instance_id__in=ids,
        sales_channel__gpt_enable=True,
    ).update(required_feed_sync=True)


def run_generic_sales_channel_factory(sales_channel_id, factory_class, local_instance_id=None, local_instance_class=None, factory_kwargs=None, sales_channel_class=MagentoSalesChannel):
    sales_channel = sales_channel_class.objects.get(id=sales_channel_id)

    local_instance = None
    if local_instance_class and local_instance_id:
        local_instance = local_instance_class.objects.get(id=local_instance_id)

    if factory_kwargs is None:
        factory_kwargs = {}

    factory_kwargs.update({'sales_channel': sales_channel, 'local_instance': local_instance})

    factory = factory_class(**factory_kwargs)
    factory.run()


def run_remote_product_dependent_sales_channel_factory(
    sales_channel_id,
    factory_class,
    local_instance_id=None,
    local_instance_class=None,
    remote_product_id=None,
    factory_kwargs=None,
    sales_channel_class=MagentoSalesChannel
):
    """
    Executes a generic Magento factory task with the provided parameters.

    :param sales_channel_id: ID of the sales channel.
    :param factory_class: The factory class to instantiate and run.
    :param local_instance_id: ID of the local instance (optional).
    :param local_instance_class: Class of the local instance (optional).
    :param remote_product_id: ID of the remote product (optional).
    :param factory_kwargs: Additional keyword arguments for the factory (optional).
    """
    sales_channel = sales_channel_class.objects.get(id=sales_channel_id)

    # Retrieve the remote product if remote_product_id is provided
    remote_product = None
    if remote_product_id:
        remote_product = RemoteProduct.objects.get(id=remote_product_id)
        if remote_product.sales_channel_id != sales_channel_id:
            raise ValueError("The remote product does not belong to the provided sales channel.")

    # Retrieve the local instance
    if local_instance_class and local_instance_id:
        local_instance = local_instance_class.objects.get(id=local_instance_id)
    elif remote_product:
        local_instance = remote_product.local_instance
    else:
        local_instance = None

    if factory_kwargs is None:
        factory_kwargs = {}

    # Update factory_kwargs with the retrieved instances
    factory_kwargs.update({
        'sales_channel': sales_channel,
        'local_instance': local_instance,
        'remote_product': remote_product,
    })

    factory = factory_class(**factory_kwargs)
    factory.run()
