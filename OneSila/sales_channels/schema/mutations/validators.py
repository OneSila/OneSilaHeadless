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

        if not any((has_gtin_exemption, has_external_id, has_ean_code, is_configurable)):
            raise ValidationError(
                {
                    '__all__': _(
                        'Amazon listings require a GTIN exemption, external product id, EAN code, or configurable product.'
                    )
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
