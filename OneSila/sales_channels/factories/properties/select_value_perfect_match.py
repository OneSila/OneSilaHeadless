from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from django.db import models
from django.db.models import QuerySet

from properties.models import PropertySelectValueTranslation


@dataclass(frozen=True)
class PerfectMatchCandidate:
    remote_instance: models.Model
    local_property_id: int


class BasePerfectMatchSelectValueMappingFactory:
    """
    Skeleton for mapping remote select values to local PropertySelectValue instances using *perfect matches*
    (exact string equality against PropertySelectValueTranslation.value for a given language).
    """

    candidates_batch_size = 2000

    def __init__(self, *, sales_channel: Any):
        self.sales_channel = sales_channel

    def run(self) -> Dict[str, int]:
        return self._map_all_languages()

    def _map_all_languages(self) -> Dict[str, int]:
        stats = {
            "languages_processed": 0,
            "candidates_seen": 0,
            "mapped": 0,
        }

        for remote_language in self.get_remote_languages_in_order():
            stats["languages_processed"] += 1
            language_stats = self._map_language(remote_language=remote_language)
            stats["candidates_seen"] += language_stats["candidates_seen"]
            stats["mapped"] += language_stats["mapped"]

        return stats

    def _map_language(self, *, remote_language: Any) -> Dict[str, int]:
        language_code = self.get_local_language_code(remote_language=remote_language)
        remote_scope = self.get_remote_scope_for_language(remote_language=remote_language)
        if not language_code or remote_scope is None:
            return {"candidates_seen": 0, "mapped": 0}

        candidates_qs = self.get_candidates_queryset(remote_scope=remote_scope)
        mapped = 0
        seen = 0

        for candidates in self._iter_candidates_in_batches(candidates_qs=candidates_qs):
            seen += len(candidates)
            mapped += self._map_candidates_batch(language_code=language_code, candidates=candidates)

        return {"candidates_seen": seen, "mapped": mapped}

    def _iter_candidates_in_batches(
        self,
        *,
        candidates_qs: QuerySet[models.Model],
    ) -> Iterator[List[PerfectMatchCandidate]]:
        batch: List[PerfectMatchCandidate] = []
        for remote_instance in candidates_qs.iterator(chunk_size=self.candidates_batch_size):
            batch.append(
                PerfectMatchCandidate(
                    remote_instance=remote_instance,
                    local_property_id=remote_instance.local_property_id,
                )
            )
            if len(batch) >= self.candidates_batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def _map_candidates_batch(
        self,
        *,
        language_code: str,
        candidates: Sequence[PerfectMatchCandidate],
    ) -> int:
        property_ids: set[int] = set()
        values: set[str] = set()

        for candidate in candidates:
            property_ids.add(candidate.local_property_id)
            values.update(self.iter_candidate_match_values(remote_instance=candidate.remote_instance))

        if not property_ids or not values:
            return 0

        translation_map, select_value_id_to_property_id = self._build_translation_map(
            language_code=language_code,
            local_property_ids=list(property_ids),
            values=list(values),
        )
        if not translation_map:
            return 0

        mapped = 0
        for candidate in candidates:
            if getattr(candidate.remote_instance, "local_instance_id", None):
                continue

            local_select_value_id = None
            for value in self.iter_candidate_match_values(remote_instance=candidate.remote_instance):
                local_select_value_id = translation_map.get((candidate.local_property_id, value))
                if local_select_value_id:
                    break

            if not local_select_value_id:
                continue

            if select_value_id_to_property_id.get(local_select_value_id) != candidate.local_property_id:
                continue

            candidate.remote_instance.local_instance_id = local_select_value_id
            candidate.remote_instance.save(update_fields=["local_instance"])
            mapped += 1

        return mapped

    def _build_translation_map(
        self,
        *,
        language_code: str,
        local_property_ids: Sequence[int],
        values: Sequence[str],
    ) -> tuple[Dict[Tuple[int, str], int], Dict[int, int]]:
        qs = PropertySelectValueTranslation.objects.filter(
            language=language_code,
            value__in=values,
            propertyselectvalue__property_id__in=local_property_ids,
        )

        multi_tenant_company = getattr(self.sales_channel, "multi_tenant_company", None)
        if multi_tenant_company is not None:
            qs = qs.filter(multi_tenant_company=multi_tenant_company)

        translation_map: Dict[Tuple[int, str], int] = {}
        select_value_id_to_property_id: Dict[int, int] = {}
        for row in qs.values(
            "value",
            property_id=models.F("propertyselectvalue__property_id"),
            local_select_value_id=models.F("propertyselectvalue_id"),
        ):
            value = (row.get("value") or "").strip()
            if not value:
                continue

            select_value_id = row["local_select_value_id"]
            property_id = row["property_id"]
            translation_map[(property_id, value)] = select_value_id
            select_value_id_to_property_id[select_value_id] = property_id

        return translation_map, select_value_id_to_property_id

    def iter_candidate_match_values(self, *, remote_instance: models.Model) -> Iterator[str]:
        remote_name = getattr(remote_instance, "remote_name", None)
        if remote_name:
            value = remote_name.strip()
            if value:
                yield value

        translated_remote_name = getattr(remote_instance, "translated_remote_name", None)
        if translated_remote_name:
            value = translated_remote_name.strip()
            if value:
                yield value

    def get_remote_languages_in_order(self) -> Iterable[Any]:
        raise NotImplementedError

    def get_local_language_code(self, *, remote_language: Any) -> Optional[str]:
        raise NotImplementedError

    def get_remote_scope_for_language(self, *, remote_language: Any) -> Any:
        raise NotImplementedError

    def get_candidates_queryset(self, *, remote_scope: Any) -> QuerySet[models.Model]:
        """
        Must return a queryset yielding model instances annotated with `local_property_id` and having:
        - remote_name
        - translated_remote_name
        - local_instance / local_instance_id
        """
        raise NotImplementedError
