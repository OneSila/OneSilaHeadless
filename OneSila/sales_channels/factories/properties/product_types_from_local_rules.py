from __future__ import annotations

from typing import Any

from sales_channels.helpers import get_all_product_rules_for_sales_channel


class BaseCreateProductTypesFromLocalRulesFactory:
    def __init__(self, *, sales_channel):
        self.sales_channel = sales_channel

    def run(self) -> list[Any]:
        product_types: list[Any] = []
        for rule in get_all_product_rules_for_sales_channel(
            sales_channel=self.sales_channel,
        ):
            product_types.extend(self.create_for_rule(rule=rule))
        return product_types

    def create_for_rule(self, *, rule) -> list[Any]:
        raise NotImplementedError


class AmazonCreateProductTypesFromLocalRulesFactory(BaseCreateProductTypesFromLocalRulesFactory):
    def create_for_rule(self, *, rule) -> list[Any]:
        from sales_channels.integrations.amazon.models import AmazonProductType

        product_type, _ = AmazonProductType.objects.get_or_create_from_local_instance(
            local_instance=rule,
            sales_channel=self.sales_channel,
        )
        return [product_type]


class EbayCreateProductTypesFromLocalRulesFactory(BaseCreateProductTypesFromLocalRulesFactory):
    def __init__(self, *, sales_channel):
        super().__init__(sales_channel=sales_channel)
        from sales_channels.integrations.ebay.models import EbaySalesChannelView

        self.marketplaces = list(
            EbaySalesChannelView.objects.filter(sales_channel=sales_channel),
        )

    def run(self) -> list[Any]:
        if not self.marketplaces:
            return []
        return super().run()

    def create_for_rule(self, *, rule) -> list[Any]:
        from sales_channels.integrations.ebay.models import EbayProductType

        product_types: list[EbayProductType] = []
        rule_name = getattr(rule.product_type, "value", None)
        for marketplace in self.marketplaces:
            defaults = {"imported": False}
            if rule_name:
                defaults["name"] = rule_name

            product_type, _ = EbayProductType.objects.get_or_create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                local_instance=rule,
                marketplace=marketplace,
                defaults=defaults,
            )
            product_types.append(product_type)
        return product_types


class SheinCreateProductTypesFromLocalRulesFactory(BaseCreateProductTypesFromLocalRulesFactory):
    def create_for_rule(self, *, rule) -> list[Any]:
        from sales_channels.integrations.shein.models import SheinProductType

        rule_name = getattr(rule.product_type, "value", None) or ""
        product_type, _ = SheinProductType.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            local_instance=rule,
            defaults={
                "imported": False,
                "name": rule_name,
                "translated_name": rule_name,
            },
        )
        return [product_type]


class MiraklCreateProductTypesFromLocalRulesFactory(BaseCreateProductTypesFromLocalRulesFactory):
    def create_for_rule(self, *, rule) -> list[Any]:
        from sales_channels.integrations.mirakl.models import MiraklProductType

        rule_name = getattr(rule.product_type, "value", None) or ""
        product_type, _ = MiraklProductType.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            local_instance=rule,
            defaults={
                "imported": False,
                "name": rule_name,
            },
        )
        return [product_type]


def create_product_types_from_local_rules_for_sales_channel(*, sales_channel) -> list[Any]:
    from sales_channels.integrations.amazon.models import AmazonSalesChannel
    from sales_channels.integrations.ebay.models import EbaySalesChannel
    from sales_channels.integrations.mirakl.models import MiraklSalesChannel
    from sales_channels.integrations.shein.models import SheinSalesChannel

    if isinstance(sales_channel, AmazonSalesChannel):
        return AmazonCreateProductTypesFromLocalRulesFactory(
            sales_channel=sales_channel,
        ).run()

    if isinstance(sales_channel, EbaySalesChannel):
        return EbayCreateProductTypesFromLocalRulesFactory(
            sales_channel=sales_channel,
        ).run()

    if isinstance(sales_channel, SheinSalesChannel):
        return SheinCreateProductTypesFromLocalRulesFactory(
            sales_channel=sales_channel,
        ).run()

    if isinstance(sales_channel, MiraklSalesChannel):
        return MiraklCreateProductTypesFromLocalRulesFactory(
            sales_channel=sales_channel,
        ).run()

    raise ValueError("Unsupported sales channel integration.")
