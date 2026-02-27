import logging

from django.db.models import Count, Q
from django.utils import timezone

from sales_channels.integrations.amazon.factories.sales_channels.full_schema import (
    AmazonProductTypeRuleFactory,
    ExportDefinitionFactory,
    UsageDefinitionFactory,
)
from sales_channels.integrations.amazon.models import (
    AmazonDefaultUnitConfigurator,
    AmazonSalesChannelView,
)
from sales_channels.integrations.amazon.models.properties import (
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonProperty,
    AmazonPublicDefinition,
)

logger = logging.getLogger(__name__)


class AmazonPublicDefinitionInternalSwitchFactory:
    """Sync a single Amazon public-definition transition between internal/non-internal."""

    def __init__(self, public_definition):
        self.public_definition: AmazonPublicDefinition = public_definition
        self.property_codes = self._resolve_property_codes()

    def run(self):
        if self.public_definition.is_internal:
            self._run_became_internal()
            return

        self._run_became_non_internal()

    def _resolve_property_codes(self):
        codes = []
        export_definition = self.public_definition.export_definition
        if isinstance(export_definition, list):
            for item in export_definition:
                if not isinstance(item, dict):
                    continue
                code = item.get("code")
                if code:
                    codes.append(str(code))

        if not codes and self.public_definition.code:
            codes.append(self.public_definition.code)

        return sorted(set(codes))

    def _property_code_filter(self):
        root_code = self.public_definition.code or ""
        filters = Q(code__in=self.property_codes)
        if root_code:
            filters |= Q(code=root_code) | Q(code__startswith=f"{root_code}__")
        return filters

    def _iter_product_types(self):
        return (
            AmazonProductType.objects.filter(
                product_type_code=self.public_definition.product_type_code,
            )
            .select_related("sales_channel")
            .order_by("id")
        )

    def _matching_views(self, sales_channel):
        return (
            AmazonSalesChannelView.objects.filter(
                sales_channel=sales_channel,
                api_region_code=self.public_definition.api_region_code,
            )
            .prefetch_related("remote_languages")
            .order_by("id")
        )

    def _is_default_view(self, view, sales_channel):
        language = view.remote_languages.first()
        remote_code = getattr(language, "remote_code", "") if language else ""
        return bool(remote_code and sales_channel.country and sales_channel.country in remote_code)

    def _ensure_export_and_usage_definitions(self):
        needs_regeneration = (
            not isinstance(self.public_definition.export_definition, list)
            or not self.public_definition.export_definition
            or not self.public_definition.usage_definition
            or self.public_definition.should_refresh()
        )
        if not needs_regeneration:
            return True

        if not self.public_definition.raw_schema:
            logger.warning(
                "Skipping Amazon public-definition reimport for %s because raw_schema is missing.",
                self.public_definition,
            )
            return False

        export_definition = ExportDefinitionFactory(self.public_definition).run()
        usage_definition = UsageDefinitionFactory(self.public_definition).run()

        self.public_definition.export_definition = export_definition
        self.public_definition.usage_definition = usage_definition
        self.public_definition.last_fetched = timezone.now()
        self.public_definition.save(
            update_fields=["export_definition", "usage_definition", "last_fetched"],
        )
        return True

    def _run_became_internal(self):
        property_filter = self._property_code_filter()

        for product_type in self._iter_product_types():
            remote_properties = AmazonProperty.objects.filter(
                sales_channel=product_type.sales_channel,
            ).filter(property_filter)
            if not remote_properties.exists():
                continue

            AmazonProductTypeItem.objects.filter(
                amazon_rule=product_type,
                remote_property__in=remote_properties,
            ).delete()

            views = self._matching_views(product_type.sales_channel)
            if views.exists():
                AmazonDefaultUnitConfigurator.objects.filter(
                    sales_channel=product_type.sales_channel,
                    marketplace__in=views,
                ).filter(property_filter).delete()

            orphan_ids = list(
                remote_properties.annotate(
                    product_type_item_count=Count("amazonproducttypeitem"),
                )
                .filter(product_type_item_count=0)
                .values_list("id", flat=True)
            )
            if orphan_ids:
                AmazonProperty.objects.filter(id__in=orphan_ids).delete()

    def _run_became_non_internal(self):
        if not self._ensure_export_and_usage_definitions():
            return

        for product_type in self._iter_product_types():
            views = self._matching_views(product_type.sales_channel)
            if not views.exists():
                continue

            factory = AmazonProductTypeRuleFactory(
                product_type_code=product_type.product_type_code,
                sales_channel=product_type.sales_channel,
                api=object(),
            )
            factory.product_type = product_type

            for view in views:
                is_default = self._is_default_view(view=view, sales_channel=product_type.sales_channel)
                factory.create_remote_properties(self.public_definition, view, is_default)
                factory.create_default_unit_configurator(self.public_definition, view, is_default)
