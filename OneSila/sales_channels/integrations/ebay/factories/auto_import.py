from django.db import models
from django.db.models import Q

from sales_channels.factories.properties.perfect_match_mapping import (
    BasePerfectMatchPropertyMappingFactory,
    BasePerfectMatchSelectValueMappingFactory,
)
from sales_channels.integrations.ebay.models import (
    EbayProperty,
    EbayPropertySelectValue,
    EbayRemoteLanguage,
)


class EbayPerfectMatchSelectValueMappingFactory(BasePerfectMatchSelectValueMappingFactory):
    """
    Maps unmapped EbayPropertySelectValue rows to local PropertySelectValue instances by searching
    perfect matches against PropertySelectValueTranslation.value for each marketplace language.

    Matches by `localized_value` first, then `translated_value`.
    """

    def __init__(self, *, sales_channel):
        super().__init__(sales_channel=sales_channel)

    def get_remote_languages_in_order(self):
        return (
            EbayRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                sales_channel_view__isnull=False,
                local_instance__isnull=False,
            )
            .select_related("sales_channel_view")
            .order_by("-sales_channel_view__is_default", "id")
        )

    def get_local_language_code(self, *, remote_language):
        return remote_language.local_instance

    def get_remote_scope_for_language(self, *, remote_language):
        return remote_language.sales_channel_view

    def get_candidates_queryset(self, *, remote_scope):
        return (
            EbayPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                marketplace=remote_scope,
                local_instance__isnull=True,
                ebay_property__local_instance__isnull=False,
            )
            .exclude(
                (Q(localized_value__isnull=True) | Q(localized_value=""))
                & (Q(translated_value__isnull=True) | Q(translated_value=""))
            )
            .annotate(local_property_id=models.F("ebay_property__local_instance_id"))
            .only("id", "localized_value", "translated_value", "local_instance_id", "ebay_property_id")
        )

    def iter_candidate_match_values(self, *, remote_instance):
        localized_value = getattr(remote_instance, "localized_value", None)
        if localized_value:
            value = localized_value.strip()
            if value:
                yield value

        translated_value = getattr(remote_instance, "translated_value", None)
        if translated_value:
            value = translated_value.strip()
            if value:
                yield value


class EbayPerfectMatchPropertyMappingFactory(BasePerfectMatchPropertyMappingFactory):
    """
    Maps unmapped EbayProperty rows to local Property instances by searching perfect matches
    against PropertyTranslation.name for each marketplace language.

    Matches by `localized_name` first, then `translated_name`.
    """

    def get_remote_languages_in_order(self):
        return (
            EbayRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                sales_channel_view__isnull=False,
                local_instance__isnull=False,
            )
            .select_related("sales_channel_view")
            .order_by("-sales_channel_view__is_default", "id")
        )

    def get_local_language_code(self, *, remote_language):
        return remote_language.local_instance

    def get_remote_scope_for_language(self, *, remote_language):
        return remote_language.sales_channel_view

    def get_candidates_queryset(self, *, remote_scope):
        return (
            EbayProperty.objects.filter(
                sales_channel=self.sales_channel,
                marketplace=remote_scope,
                local_instance__isnull=True,
            )
            .exclude(
                (Q(localized_name__isnull=True) | Q(localized_name=""))
                & (Q(translated_name__isnull=True) | Q(translated_name=""))
            )
            .only("id", "localized_name", "translated_name", "local_instance_id", "type")
        )

    def iter_candidate_match_values(self, *, remote_instance):
        localized_name = getattr(remote_instance, "localized_name", None)
        if localized_name:
            value = localized_name.strip()
            if value:
                yield value

        translated_name = getattr(remote_instance, "translated_name", None)
        if translated_name:
            value = translated_name.strip()
            if value:
                yield value
