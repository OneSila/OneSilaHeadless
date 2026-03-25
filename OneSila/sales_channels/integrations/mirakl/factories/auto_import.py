from __future__ import annotations

from typing import Iterable, Iterator, Optional

from django.db import models
from django.db.models import Q

from sales_channels.factories.properties.perfect_match_mapping import (
    BasePerfectMatchPropertyMappingFactory,
    BasePerfectMatchSelectValueMappingFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklRemoteLanguage,
)


def _iter_json_translation_values(*, translations) -> Iterator[str]:
    seen: set[str] = set()
    for entry in translations or []:
        if not isinstance(entry, dict):
            continue
        value = str(entry.get("value") or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        yield value


class MiraklPerfectMatchSelectValueMappingFactory(BasePerfectMatchSelectValueMappingFactory):
    def get_remote_languages_in_order(self):
        languages = list(
            MiraklRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=False,
            ).order_by("-is_default", "id")
        )
        return languages or [None]

    def get_local_language_code(self, *, remote_language):
        if remote_language is None:
            return getattr(self.sales_channel.multi_tenant_company, "language", None)
        return remote_language.local_instance

    def get_remote_scope_for_language(self, *, remote_language):
        return self.sales_channel

    def get_candidates_queryset(self, *, remote_scope):
        return (
            MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=True,
                remote_property__local_instance__isnull=False,
            )
            .annotate(local_property_id=models.F("remote_property__local_instance_id"))
            .only(
                "id",
                "value",
                "code",
                "label_translations",
                "value_label_translations",
                "local_instance_id",
                "remote_property_id",
            )
        )

    def iter_candidate_match_values(self, *, remote_instance):
        value = getattr(remote_instance, "value", None)
        if value:
            cleaned = value.strip()
            if cleaned:
                yield cleaned

        for translated in _iter_json_translation_values(
            translations=getattr(remote_instance, "label_translations", None),
        ):
            yield translated

        for translated in _iter_json_translation_values(
            translations=getattr(remote_instance, "value_label_translations", None),
        ):
            yield translated


class MiraklPerfectMatchPropertyMappingFactory(BasePerfectMatchPropertyMappingFactory):
    def get_remote_languages_in_order(self):
        languages = list(
            MiraklRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=False,
            ).order_by("-is_default", "id")
        )
        return languages or [None]

    def get_local_language_code(self, *, remote_language):
        if remote_language is None:
            return getattr(self.sales_channel.multi_tenant_company, "language", None)
        return remote_language.local_instance

    def get_remote_scope_for_language(self, *, remote_language):
        return self.sales_channel

    def get_candidates_queryset(self, *, remote_scope):
        return (
            MiraklProperty.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=True,
            )
            .exclude(Q(name="") & Q(label_translations=[]))
            .only(
                "id",
                "name",
                "type",
                "label_translations",
                "local_instance_id",
            )
        )

    def iter_candidate_match_values(self, *, remote_instance):
        name = getattr(remote_instance, "name", None)
        if name:
            cleaned = name.strip()
            if cleaned:
                yield cleaned

        for translated in _iter_json_translation_values(
            translations=getattr(remote_instance, "label_translations", None),
        ):
            yield translated
