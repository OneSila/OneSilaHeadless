from django.db import models
from django.db.models import Q

from sales_channels.factories.properties.perfect_match_mapping import (
    BasePerfectMatchPropertyMappingFactory,
    BasePerfectMatchSelectValueMappingFactory,
)
from sales_channels.integrations.shein.models import (
    SheinProperty,
    SheinPropertySelectValue,
    SheinRemoteLanguage,
)


class SheinPerfectMatchSelectValueMappingFactory(BasePerfectMatchSelectValueMappingFactory):
    """
    Maps unmapped SheinPropertySelectValue rows to local PropertySelectValue instances by searching
    perfect matches against PropertySelectValueTranslation.value for each available remote language.

    Matches by `value` first, then `value_en`.
    """

    def __init__(self, *, sales_channel):
        super().__init__(sales_channel=sales_channel)

    def get_remote_languages_in_order(self):
        return (
            SheinRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=False,
            )
            .order_by("id")
        )

    def get_local_language_code(self, *, remote_language):
        return remote_language.local_instance

    def get_remote_scope_for_language(self, *, remote_language):
        return self.sales_channel

    def get_candidates_queryset(self, *, remote_scope):
        return (
            SheinPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=True,
                remote_property__local_instance__isnull=False,
            )
            .exclude(Q(value="") & Q(value_en=""))
            .annotate(local_property_id=models.F("remote_property__local_instance_id"))
            .only("id", "value", "value_en", "local_instance_id", "remote_property_id")
        )

    def iter_candidate_match_values(self, *, remote_instance):
        value = getattr(remote_instance, "value", None)
        if value:
            cleaned = value.strip()
            if cleaned:
                yield cleaned

        value_en = getattr(remote_instance, "value_en", None)
        if value_en:
            cleaned = value_en.strip()
            if cleaned:
                yield cleaned


class SheinPerfectMatchPropertyMappingFactory(BasePerfectMatchPropertyMappingFactory):

    def get_remote_languages_in_order(self):
        return (
            SheinRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=False,
            )
            .order_by("id")
        )

    def get_local_language_code(self, *, remote_language):
        return remote_language.local_instance

    def get_remote_scope_for_language(self, *, remote_language):
        return self.sales_channel

    def get_candidates_queryset(self, *, remote_scope):
        return (
            SheinProperty.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=True,
            )
            .exclude(Q(name="") & Q(name_en=""))
            .only("id", "name", "name_en", "local_instance_id", "type")
        )

    def iter_candidate_match_values(self, *, remote_instance):
        name = getattr(remote_instance, "name", None)
        if name:
            cleaned = name.strip()
            if cleaned:
                yield cleaned

        name_en = getattr(remote_instance, "name_en", None)
        if name_en:
            cleaned = name_en.strip()
            if cleaned:
                yield cleaned
