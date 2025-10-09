from django.core.exceptions import ValidationError

from sales_channels.integrations.ebay.factories.sales_channels import EbayCategorySuggestionFactory
from sales_channels.integrations.ebay.schema.types.input import (
    EbaySalesChannelInput,
    EbaySalesChannelPartialInput,
    EbayValidateAuthInput,
    EbayProductTypePartialInput,
    EbayInternalPropertyPartialInput,
    EbayInternalPropertyOptionInput,
    EbayInternalPropertyOptionPartialInput,
    EbayPropertyPartialInput,
    EbayPropertySelectValuePartialInput,
    EbaySalesChannelImportInput,
    EbaySalesChannelImportPartialInput,
    EbaySalesChannelViewPartialInput,
    EbayCurrencyPartialInput,
)
from sales_channels.integrations.ebay.schema.types.types import (
    EbaySalesChannelType,
    EbayRedirectUrlType,
    EbayProductTypeType,
    EbayInternalPropertyType,
    EbayInternalPropertyOptionType,
    EbayPropertyType,
    EbayPropertySelectValueType,
    EbaySalesChannelViewType,
    EbaySalesChannelImportType,
    EbayCurrencyType,
    SuggestedEbayCategory,
    SuggestedEbayCategoryEntry,
)
from sales_channels.schema.types.input import SalesChannelViewPartialInput
from core.schema.core.mutations import create, type, List, update
from strawberry import Info
import strawberry_django
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from django.utils.translation import gettext_lazy as _


@type(name="Mutation")
class EbaySalesChannelMutation:
    create_ebay_sales_channel: EbaySalesChannelType = create(EbaySalesChannelInput)
    create_ebay_sales_channels: List[EbaySalesChannelType] = create(EbaySalesChannelInput)

    update_ebay_sales_channel: EbaySalesChannelType = update(EbaySalesChannelPartialInput)

    update_ebay_product_type: EbayProductTypeType = update(EbayProductTypePartialInput)

    update_ebay_property: EbayPropertyType = update(EbayPropertyPartialInput)
    update_ebay_internal_property: EbayInternalPropertyType = update(EbayInternalPropertyPartialInput)
    update_ebay_internal_property_option: EbayInternalPropertyOptionType = update(EbayInternalPropertyOptionPartialInput)
    update_ebay_property_select_value: EbayPropertySelectValueType = update(EbayPropertySelectValuePartialInput)
    update_ebay_sales_channel_view: EbaySalesChannelViewType = update(EbaySalesChannelViewPartialInput)
    update_ebay_currency: EbayCurrencyType = update(EbayCurrencyPartialInput)

    create_ebay_import_process: EbaySalesChannelImportType = create(EbaySalesChannelImportInput)
    update_ebay_import_process: EbaySalesChannelImportType = update(EbaySalesChannelImportPartialInput)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def get_ebay_redirect_url(self, instance: EbaySalesChannelPartialInput, info: Info) -> EbayRedirectUrlType:
        from sales_channels.integrations.ebay.models import EbaySalesChannel
        from sales_channels.integrations.ebay.factories.sales_channels.oauth import GetEbayRedirectUrlFactory

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = EbaySalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company
        )

        factory = GetEbayRedirectUrlFactory(sales_channel=sales_channel)
        factory.run()

        return EbayRedirectUrlType(redirect_url=factory.redirect_url)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def validate_ebay_auth(self, instance: EbayValidateAuthInput, info: Info) -> EbaySalesChannelType:
        from sales_channels.integrations.ebay.models import EbaySalesChannel
        from sales_channels.integrations.ebay.factories.sales_channels.oauth import ValidateEbayAuthFactory

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        try:
            sales_channel = EbaySalesChannel.objects.get(
                state=instance.state,
                multi_tenant_company=multi_tenant_company
            )
        except EbaySalesChannel.DoesNotExist:
            raise ValidationError(_("Could not find eBay integration. Please restart the authorization process."))

        factory = ValidateEbayAuthFactory(
            sales_channel=sales_channel,
            code=instance.code,
        )
        factory.run()

        return sales_channel

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def suggest_ebay_category(
        self,
        name: str,
        marketplace: SalesChannelViewPartialInput,
        info: Info,
    ) -> SuggestedEbayCategory:
        """Return suggested eBay categories for a given marketplace."""
        from sales_channels.models import SalesChannelView

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        query = name.strip()
        if not query:
            raise ValidationError(_("Category name is required."))

        view = SalesChannelView.objects.select_related("sales_channel").get(
            id=marketplace.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )

        factory = EbayCategorySuggestionFactory(view=view, query=query)
        factory.run()

        return SuggestedEbayCategory(
            category_tree_id=factory.category_tree_id,
            categories=[
                SuggestedEbayCategoryEntry(
                    category_id=entry["category_id"],
                    category_name=entry["category_name"],
                    category_path=entry["category_path"],
                    leaf=entry["leaf"],
                )
                for entry in factory.categories
            ],
        )

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def create_ebay_product_types_from_local_rules(
        self,
        instance: EbaySalesChannelPartialInput,
        info: Info,
    ) -> List[EbayProductTypeType]:
        """Create eBay product types for every local product rule on the sales channel."""
        from properties.models import ProductPropertiesRule
        from sales_channels.integrations.ebay.models import (
            EbayProductType,
            EbaySalesChannel,
            EbaySalesChannelView,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        sales_channel = EbaySalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        marketplaces = list(
            EbaySalesChannelView.objects.filter(sales_channel=sales_channel)
        )
        if not marketplaces:
            return EbayProductType.objects.none()

        product_types: list[EbayProductType] = []
        for rule in ProductPropertiesRule.objects.filter(
            multi_tenant_company=multi_tenant_company,
        ).iterator():
            rule_name = getattr(rule.product_type, "value", None)
            for marketplace in marketplaces:
                defaults = {"imported": False}
                if rule_name:
                    defaults["name"] = rule_name

                create_kwargs = {
                    "sales_channel": sales_channel,
                    "multi_tenant_company": multi_tenant_company,
                    "local_instance": rule,
                    "marketplace": marketplace
                }
                product_type, _ = EbayProductType.objects.get_or_create(
                    defaults=defaults,
                    **create_kwargs,
                )
                product_types.append(product_type)

        return product_types
