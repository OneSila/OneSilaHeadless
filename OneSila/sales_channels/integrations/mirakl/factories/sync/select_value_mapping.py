from __future__ import annotations

from django.db.models import Q

from sales_channels.integrations.mirakl.models import MiraklProperty, MiraklPropertySelectValue


class MiraklPropertySelectValueSiblingMappingFactory:
    """Propagate a mapped Mirakl select value across sibling mapped properties."""

    def __init__(self, *, remote_select_value: MiraklPropertySelectValue) -> None:
        self.remote_select_value = remote_select_value

    def run(self) -> int:
        sibling_property_ids = self._get_sibling_property_ids()
        if not sibling_property_ids:
            return 0

        filters = self._build_match_filters()
        if filters is None:
            return 0

        queryset = MiraklPropertySelectValue.objects.filter(
            sales_channel=self.remote_select_value.sales_channel,
            remote_property_id__in=sibling_property_ids,
            local_instance__isnull=True,
        ).filter(filters)
        return queryset.update(local_instance=self.remote_select_value.local_instance)

    def _get_sibling_property_ids(self) -> list[int]:
        remote_property = getattr(self.remote_select_value, "remote_property", None)
        if remote_property is None:
            return []

        if not self.remote_select_value.local_instance_id:
            return []

        local_property_id = getattr(remote_property, "local_instance_id", None)
        if not local_property_id:
            return []

        queryset = MiraklProperty.objects.filter(
            sales_channel=self.remote_select_value.sales_channel,
            local_instance_id=local_property_id,
        ).exclude(id=remote_property.id)
        return list(queryset.values_list("id", flat=True))

    def _build_match_filters(self) -> Q | None:
        filters = Q()
        has_match = False

        normalized_code = self._clean_string(self.remote_select_value.code)
        if normalized_code:
            filters |= Q(code=normalized_code)
            has_match = True

        normalized_value = self._clean_string(self.remote_select_value.value)
        if normalized_value:
            filters |= Q(value=normalized_value)
            has_match = True

        if not has_match:
            return None
        return filters

    def _clean_string(self, value) -> str:
        return str(value or "").strip()
