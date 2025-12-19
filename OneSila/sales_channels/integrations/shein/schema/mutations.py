"""GraphQL mutation mixins for the Shein integration."""

from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from media.models import Image
from media.schema.types.input import ImagePartialInput
from strawberry import Info
import strawberry_django

from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.mutations import List, create, delete, type, update
from sales_channels.integrations.shein.factories.sales_channels import (
    SheinCategorySuggestionFactory,
    FetchRemoteIssuesFactory,
)
from sales_channels.integrations.shein.schema.types.input import (
    SheinInternalPropertyOptionPartialInput,
    SheinInternalPropertyPartialInput,
    SheinProductCategoryInput,
    SheinProductCategoryPartialInput,
    SheinPropertyPartialInput,
    SheinPropertySelectValuePartialInput,
    SheinProductTypePartialInput,
    SheinRemoteCurrencyPartialInput,
    SheinSalesChannelImportInput,
    SheinSalesChannelImportPartialInput,
    SheinSalesChannelInput,
    SheinSalesChannelPartialInput,
    SheinSalesChannelViewPartialInput,
    SheinValidateAuthInput,
)
from sales_channels.integrations.shein.schema.types.types import (
    SheinInternalPropertyOptionType,
    SheinInternalPropertyType,
    SheinProductCategoryType,
    SheinPropertySelectValueType,
    SheinPropertyType,
    SheinProductTypeType,
    SheinRemoteCurrencyType,
    SheinRedirectUrlType,
    SheinSalesChannelMappingSyncPayload,
    SheinSalesChannelImportType,
    SheinSalesChannelType,
    SheinSalesChannelViewType,
    SuggestedSheinCategory,
    SuggestedSheinCategoryEntry,
)
from sales_channels.schema.types.input import SalesChannelViewPartialInput
from sales_channels.schema.types.input import RemoteProductPartialInput
from sales_channels.schema.types.types import RemoteProductType
from products.schema.types.input import ProductPartialInput


@type(name="Mutation")
class SheinSalesChannelMutation:
    """Expose create/update helpers and OAuth entry-points for Shein."""

    create_shein_sales_channel: SheinSalesChannelType = create(SheinSalesChannelInput)
    create_shein_sales_channels: List[SheinSalesChannelType] = create(SheinSalesChannelInput)
    create_shein_product_category: SheinProductCategoryType = create(SheinProductCategoryInput)

    update_shein_sales_channel: SheinSalesChannelType = update(SheinSalesChannelPartialInput)
    update_shein_product_category: SheinProductCategoryType = update(SheinProductCategoryPartialInput)
    update_shein_sales_channel_view: SheinSalesChannelViewType = update(SheinSalesChannelViewPartialInput)
    update_shein_remote_currency: SheinRemoteCurrencyType = update(SheinRemoteCurrencyPartialInput)
    update_shein_property: SheinPropertyType = update(SheinPropertyPartialInput)
    update_shein_property_select_value: SheinPropertySelectValueType = update(
        SheinPropertySelectValuePartialInput,
    )
    update_shein_product_type: SheinProductTypeType = update(SheinProductTypePartialInput)
    update_shein_internal_property: SheinInternalPropertyType = update(
        SheinInternalPropertyPartialInput,
    )
    update_shein_internal_property_option: SheinInternalPropertyOptionType = update(
        SheinInternalPropertyOptionPartialInput,
    )
    create_shein_import_process: SheinSalesChannelImportType = create(
        SheinSalesChannelImportInput,
    )
    update_shein_import_process: SheinSalesChannelImportType = update(
        SheinSalesChannelImportPartialInput,
    )
    delete_shein_product_category: SheinProductCategoryType = delete()

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def sync_shein_sales_channel_mappings(
        self,
        source_sales_channel: SheinSalesChannelPartialInput,
        target_sales_channel: SheinSalesChannelPartialInput,
        info: Info,
    ) -> SheinSalesChannelMappingSyncPayload:
        """Enqueue mapping sync between two Shein sales channels."""
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.shein.tasks import (
            shein_sync_sales_channel_mappings_task,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        source = SheinSalesChannel.objects.get(
            id=source_sales_channel.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )
        target = SheinSalesChannel.objects.get(
            id=target_sales_channel.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        shein_sync_sales_channel_mappings_task(
            source_sales_channel_id=source.id,
            target_sales_channel_id=target.id,
        )

        return SheinSalesChannelMappingSyncPayload(success=True)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def get_shein_redirect_url(
        self,
        instance: SheinSalesChannelPartialInput,
        info: Info,
    ) -> SheinRedirectUrlType:
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.shein.factories.sales_channels.oauth import (
            GetSheinRedirectUrlFactory,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = SheinSalesChannel.objects.get(
            id=instance.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        factory = GetSheinRedirectUrlFactory(sales_channel=sales_channel)
        factory.run()

        return SheinRedirectUrlType(redirect_url=factory.redirect_url)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def validate_shein_auth(
        self,
        instance: SheinValidateAuthInput,
        info: Info,
    ) -> SheinSalesChannelType:
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.shein.factories.sales_channels.oauth import (
            ValidateSheinAuthFactory,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        try:
            sales_channel = SheinSalesChannel.objects.get(
                state=instance.state,
                multi_tenant_company=multi_tenant_company,
            )
        except SheinSalesChannel.DoesNotExist as exc:  # pragma: no cover - guard path
            raise ValueError(
                _("Could not find Shein integration for the provided state.")
            ) from exc

        factory = ValidateSheinAuthFactory(
            sales_channel=sales_channel,
            app_id=instance.app_id,
            temp_token=instance.temp_token,
            state=instance.state,
        )
        factory.run()

        return sales_channel

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def suggest_shein_category(
        self,
        marketplace: SalesChannelViewPartialInput,
        info: Info,
        name: Optional[str] = None,
        image: Optional[ImagePartialInput] = None,
        external_image_url: Optional[str] = None,
    ) -> SuggestedSheinCategory:
        """Return category suggestions for a Shein marketplace."""
        from sales_channels.models import SalesChannelView
        from sales_channels.integrations.shein.models import SheinSalesChannelView

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        view = SalesChannelView.objects.select_related("sales_channel").get(
            id=marketplace.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )
        shein_view = view.get_real_instance()
        if not isinstance(shein_view, SheinSalesChannelView):
            raise ValidationError(_("Provided marketplace is not a Shein storefront."))

        image_instance: Image | None = None
        if image is not None:
            if image.id is None:
                raise ValidationError(_("Image identifier is required."))
            try:
                image_instance = Image.objects.get(
                    id=image.id.node_id,
                    multi_tenant_company=multi_tenant_company,
                )
            except Image.DoesNotExist as exc:  # pragma: no cover - defensive guard path
                raise ValidationError(_("Image could not be found.")) from exc

        query = (name or "").strip()
        explicit_image_url = (external_image_url or "").strip()
        if not any([query, explicit_image_url, image_instance]):
            raise ValidationError(_("Provide a name or an image to fetch suggestions."))

        factory = SheinCategorySuggestionFactory(
            view=shein_view,
            query=query,
            image_url=explicit_image_url,
            image=image_instance,
        )
        factory.run()

        categories = [
            SuggestedSheinCategoryEntry(
                category_id=entry["category_id"],
                product_type_id=str(entry.get("product_type_id", "") or ""),
                category_name=entry["category_name"],
                category_path=entry["category_path"],
                leaf=entry["leaf"],
                order=entry["order"],
                vote=entry["vote"],
            )
            for entry in factory.categories
        ]

        return SuggestedSheinCategory(
            site_remote_id=shein_view.remote_id or "",
            categories=categories,
        )

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def map_shein_perfect_match_select_values(
        self,
        sales_channel: SheinSalesChannelPartialInput,
        info: Info,
    ) -> bool:
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.shein.tasks import (
            shein_map_perfect_match_select_values_db_task,
        )

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        channel = SheinSalesChannel.objects.get(
            id=sales_channel.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        shein_map_perfect_match_select_values_db_task(sales_channel_id=channel.id)
        return True

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def refresh_shein_latest_issues(
        self,
        remote_product: RemoteProductPartialInput,
        sales_channel: SheinSalesChannelPartialInput,
        info: Info,
    ) -> RemoteProductType:
        """Refresh audit/issues for a specific Shein remote product."""
        from sales_channels.models.products import RemoteProduct
        from sales_channels.integrations.shein.models import SheinSalesChannel

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        remote_product_obj = RemoteProduct.objects.select_related("sales_channel").get(
            id=remote_product.id.node_id,
            sales_channel__multi_tenant_company=multi_tenant_company,
        )

        sales_channel_obj = SheinSalesChannel.objects.get(
            id=sales_channel.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        factory = FetchRemoteIssuesFactory(
            remote_product=remote_product_obj,
            sales_channel=sales_channel_obj,
        )
        factory.run()

        return remote_product_obj

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def force_update_shein_product(
        self,
        product: ProductPartialInput,
        sales_channel: SheinSalesChannelPartialInput,
        info: Info,
    ) -> bool:
        """Force an update by running the create flow (publishOrEdit) again."""
        from products.models import Product
        from sales_channels.integrations.shein.models import SheinSalesChannel, SheinSalesChannelView
        from sales_channels.integrations.shein.flows.tasks_runner import (
            run_single_shein_product_task_flow,
        )
        from sales_channels.integrations.shein.tasks import create_shein_product_db_task

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        product_obj = Product.objects.get(
            id=product.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        channel = SheinSalesChannel.objects.get(
            id=sales_channel.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        view_obj = (
            SheinSalesChannelView.objects.filter(
                sales_channel=channel,
                is_default=True,
            ).first()
            or SheinSalesChannelView.objects.filter(sales_channel=channel).first()
        )
        if view_obj is None:
            raise ValidationError(_("Shein sales channel has no storefront views. Pull marketplaces first."))

        count = 1 + getattr(product_obj, "get_configurable_variations", lambda: [])().count()

        run_single_shein_product_task_flow(
            task_func=create_shein_product_db_task,
            view=view_obj,
            number_of_remote_requests=count,
            product_id=product_obj.id,
        )

        return True
