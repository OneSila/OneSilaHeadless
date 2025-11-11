from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from sales_channels.exceptions import VariationAlreadyExistsOnWebsite
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.shopify.models import ShopifySalesChannel


def validate_sku_conflicts(data, info):
    product = data['product'].pk
    view = data['sales_channel_view'].pk

    sales_channel = view.sales_channel.get_real_instance()

    if isinstance(sales_channel, ShopifySalesChannel):
        return

    if product.is_configurable():
        variations = product.get_configurable_variations(active_only=True)
        variation_ids = [v.id for v in variations]
        conflicted_ids = SalesChannelViewAssign.objects.filter(
            product_id__in=variation_ids,
            sales_channel=sales_channel,
            remote_product__isnull=False,
        ).values_list("product_id", flat=True)

        if conflicted_ids:
            sku_map = {v.id: v.sku for v in variations}
            conflicted_skus = [sku_map[pid] for pid in conflicted_ids]
            skus = ", ".join(conflicted_skus)
            raise VariationAlreadyExistsOnWebsite(
                f"Variations with SKU(s) {skus} already exist on this sales channel. "
                "Remove them before syncing as a configurable product."
            )
    else:
        parents = list(product.configurables.all())
        parent_ids = [p.id for p in parents]
        conflicted_parent_ids = SalesChannelViewAssign.objects.filter(
            product_id__in=parent_ids,
            sales_channel=sales_channel,
        ).values_list("product_id", flat=True)

        if conflicted_parent_ids:
            sku_map = {p.id: p.sku for p in parents}
            conflicted_skus = [sku_map[pid] for pid in conflicted_parent_ids]
            skus = ", ".join(conflicted_skus)
            raise VariationAlreadyExistsOnWebsite(
                f"Parent product(s) with SKU(s) {skus} already exist on this sales channel. "
                "Remove them before syncing this variation independently."
            )


def validate_amazon_assignment(data, info):
    product = data['product'].pk
    view = data['sales_channel_view'].pk
    sales_channel = view.sales_channel.get_real_instance()

    from sales_channels.integrations.amazon.models import (
        AmazonExternalProductId,
        AmazonGtinExemption,
        AmazonSalesChannel,
        AmazonSalesChannelView,
        AmazonProductBrowseNode,
        AmazonVariationTheme,
    )

    if isinstance(sales_channel, AmazonSalesChannel):
        views = [view]
        default_view = AmazonSalesChannelView.objects.filter(
            sales_channel=sales_channel,
            is_default=True,
        ).first()

        if default_view and default_view != view:
            views.append(default_view)

        has_gtin_exemption = AmazonGtinExemption.objects.filter(
            product=product,
            view__in=views,
            value=True,
        ).exists()

        has_external_id = (
            AmazonExternalProductId.objects.filter(
                product=product,
                view__in=views,
            )
            .exclude(value__isnull=True)
            .exclude(value__exact="")
            .exists()
        )

        has_ean_code = bool(product.ean_code)
        is_configurable = product.is_configurable()
        has_required_identifier = any((has_gtin_exemption, has_external_id, has_ean_code))

        if not is_configurable and not has_required_identifier:
            raise ValidationError(
                {
                    '__all__': _(
                        'Amazon listings require a GTIN exemption, external product id, EAN code, or configurable product.'
                    )
                }
            )

        if is_configurable:
            variations = product.get_configurable_variations(active_only=True)
            missing_variation_skus = []

            for variation in variations:
                variation_has_gtin_exemption = AmazonGtinExemption.objects.filter(
                    product=variation,
                    view__in=views,
                    value=True,
                ).exists()

                variation_has_external_id = (
                    AmazonExternalProductId.objects.filter(
                        product=variation,
                        view__in=views,
                    )
                    .exclude(value__isnull=True)
                    .exclude(value__exact="")
                    .exists()
                )

                variation_has_ean_code = bool(variation.ean_code)

                if not any((variation_has_gtin_exemption, variation_has_external_id, variation_has_ean_code)):
                    missing_variation_skus.append(variation.sku or str(variation.pk))

            if missing_variation_skus:
                skus = ", ".join(missing_variation_skus)
                raise ValidationError(
                    {
                        '__all__': _(
                            'Amazon configurable products require each variation to have a GTIN exemption, external product id, or EAN code. Missing for SKU(s): %(skus)s.'
                        )
                        % {'skus': skus}
                    }
                )

        exists = SalesChannelViewAssign.objects.filter(
            product=product,
            sales_channel_view__sales_channel=sales_channel,
        ).exists()

        if not exists:
            if not AmazonProductBrowseNode.objects.filter(
                product=product,
                sales_channel=sales_channel,
                view__in=views,
            ).exists():
                raise ValidationError(
                    {'__all__': _('Amazon products require a browse node for the first assignment.')}
                )

            if product.is_configurable() and not AmazonVariationTheme.objects.filter(
                product=product,
                view__in=views,
            ).exists():
                raise ValidationError(
                    {
                        '__all__': _(
                            'Amazon configurable products require a variation theme for the first assignment.'
                        )
                    }
                )
        else:
            has_asin = (
                AmazonExternalProductId.objects.filter(
                    product=product,
                    view__in=views,
                )
                .exclude(value__isnull=True)
                .exclude(value__exact="")
                .filter(
                    Q(created_asin__isnull=False) & ~Q(created_asin__exact="")
                    | Q(type=AmazonExternalProductId.TYPE_ASIN)
                )
                .exists()
            )

            if not has_asin:
                raise ValidationError(
                    {
                        '__all__': _(
                            'To create a new Amazon assignment there must be at least one completed assignment validated by Amazon with an ASIN. Wait for validation or provide an ASIN manually.'
                        )
                    }
                )


def validate_ebay_assignment(data, info):
    from sales_channels.integrations.ebay.models import (
        EbaySalesChannel,
        EbaySalesChannelView,
        EbayProductCategory,
        EbayProductType,
    )

    def has_required_ebay_mapping(p, has_type_mapping):
        """Check for a category or, if present, a global product type mapping."""
        if has_type_mapping:
            return True

        return EbayProductCategory.objects.filter(
            product=p,
            view=view,
        ).exists()

    product = data['product'].pk
    view = data['sales_channel_view'].pk
    sales_channel = view.sales_channel.get_real_instance()

    # ✅ 1. Exit early if not eBay
    if not isinstance(sales_channel, EbaySalesChannel):
        return

    # ✅ 2. Ensure required eBay policies exist
    # @TODO: This is duplicate code, make a helper instead
    fulfillment_id = getattr(view, "fulfillment_policy_id", None)
    payment_id = getattr(view, "payment_policy_id", None)
    return_id = getattr(view, "return_policy_id", None)

    missing = []
    if not fulfillment_id:
        missing.append("fulfillment policy")
    if not payment_id:
        missing.append("payment policy")
    if not return_id:
        missing.append("return policy")

    if missing:
        raise ValidationError(
            {
                "__all__": _(
                    "Missing eBay listing policies (%(missing)s). Please configure the marketplace policies before pushing products."
                )
                % {"missing": ", ".join(missing)}
            }
        )

    # ✅ 3. Get the product rule once and check mappings
    product_rule = product.get_product_rule(sales_channel=sales_channel)

    has_type_mapping = False
    if product_rule:
        has_type_mapping = EbayProductType.objects.filter(
            local_instance=product_rule,
            marketplace=view,
        ).exists()


    # ✅ 4. Validate per product type
    if product.is_configurable():
        variations = product.get_configurable_variations(active_only=True)
        missing_skus = [v.sku or str(v.pk) for v in variations if not has_required_ebay_mapping(v, has_type_mapping)]

        if missing_skus:
            raise ValidationError(
                {
                    "__all__": _(
                        "eBay configurable products require each variation to have either a mapped product type or a category assigned. Missing for SKU(s): %(skus)s."
                    )
                    % {"skus": ", ".join(missing_skus)}
                }
            )
    else:
        if not has_required_ebay_mapping(product, has_type_mapping):
            raise ValidationError(
                {
                    "__all__": _(
                        "eBay products require either a mapped product type (EbayProductType) or a category (EbayProductCategory) before listing."
                    )
                }
            )
