import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from llm.factories import ProductFeedPayloadFactory
from sales_channels.models import RemoteProduct, SalesChannel, SalesChannelViewAssign

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _AssignmentPayload:
    identifiers: Set[str]
    payloads: Dict[str, Dict[str, object]]


class SalesChannelGptProductFeedFactory:
    """Synchronise GPT product feeds for sales channels."""

    def __init__(self, *, sync_all: bool = False):
        self.sync_all = sync_all

    def work(self) -> None:
        remote_products = self._collect_remote_products()
        if not remote_products:
            return

        assignments_map = self._load_assignments(remote_products=remote_products)
        grouped = self._group_by_sales_channel(remote_products=remote_products)

        processed_remote_ids: Set[int] = set()

        for sales_channel, channel_products in grouped:
            processed_remote_ids.update(product.id for product in channel_products)
            channel_assignments = self._collect_channel_assignments(
                channel_products=channel_products,
                assignments_map=assignments_map,
            )
            existing_entries = self._load_existing_feed(sales_channel=sales_channel)
            updated_entries = self._merge_entries(
                sales_channel=sales_channel,
                existing_entries=existing_entries,
                assignments=channel_assignments,
            )

            if updated_entries is None:
                continue

            with transaction.atomic():
                self._persist_feed(
                    sales_channel=sales_channel,
                    entries=updated_entries,
                )
                self._send_feed(
                    sales_channel=sales_channel,
                    entries=updated_entries,
                )

        if processed_remote_ids:
            self._clear_required_flags(remote_product_ids=processed_remote_ids)

    def _collect_remote_products(self) -> List[RemoteProduct]:
        queryset = RemoteProduct.objects.filter(
            sales_channel__gpt_enable=True,
        )
        if not self.sync_all:
            queryset = queryset.filter(required_feed_sync=True)
        return list(
            queryset.select_related("sales_channel", "local_instance").order_by("sales_channel_id", "id")
        )

    def _load_assignments(
        self,
        *,
        remote_products: Sequence[RemoteProduct],
    ) -> Dict[int, List[SalesChannelViewAssign]]:
        remote_product_ids = {product.id for product in remote_products}
        if not remote_product_ids:
            return {}
        assignments = (
            SalesChannelViewAssign.objects.filter(remote_product_id__in=remote_product_ids)
            .select_related(
                "product",
                "sales_channel",
                "sales_channel_view",
                "sales_channel_view__sales_channel",
                "remote_product",
            )
            .order_by("remote_product_id", "id")
        )
        mapping: Dict[int, List[SalesChannelViewAssign]] = defaultdict(list)
        for assignment in assignments:
            mapping[assignment.remote_product_id].append(assignment)
        return mapping

    def _group_by_sales_channel(
        self,
        *,
        remote_products: Sequence[RemoteProduct],
    ) -> List[Tuple[SalesChannel, List[RemoteProduct]]]:
        grouped: Dict[int, List[RemoteProduct]] = defaultdict(list)
        channels: Dict[int, SalesChannel] = {}
        for product in remote_products:
            grouped[product.sales_channel_id].append(product)
            channels[product.sales_channel_id] = product.sales_channel
        return [(channels[channel_id], grouped[channel_id]) for channel_id in grouped]

    def _collect_channel_assignments(
        self,
        *,
        channel_products: Sequence[RemoteProduct],
        assignments_map: Dict[int, List[SalesChannelViewAssign]],
    ) -> Dict[int, _AssignmentPayload]:
        channel_assignments: Dict[int, _AssignmentPayload] = {}
        for remote_product in channel_products:
            assignments = assignments_map.get(remote_product.id, [])
            payloads: Dict[str, Dict[str, object]] = {}
            identifiers: Set[str] = set()

            if not assignments:
                sku = getattr(getattr(remote_product, "local_instance", None), "sku", None)
                if sku:
                    identifiers.add(str(sku))
                channel_assignments[remote_product.id] = _AssignmentPayload(
                    identifiers=identifiers,
                    payloads=payloads,
                )
                continue

            for assignment in assignments:
                payload_data = self._build_payload_for_assignment(assignment=assignment)
                payloads.update(payload_data.payloads)
                identifiers.update(payload_data.identifiers)

            channel_assignments[remote_product.id] = _AssignmentPayload(
                identifiers=identifiers,
                payloads=payloads,
            )
        return channel_assignments

    def _build_payload_for_assignment(
        self,
        *,
        assignment: SalesChannelViewAssign,
    ) -> _AssignmentPayload:
        identifiers: Set[str] = set()
        product = assignment.product
        sku = getattr(product, "sku", None)
        if sku:
            identifiers.add(str(sku))
        try:
            if product.is_configurable():
                for variation in product.get_configurable_variations(active_only=False):
                    variation_sku = getattr(variation, "sku", None)
                    if variation_sku:
                        identifiers.add(str(variation_sku))
        except AttributeError:
            pass

        payloads: Dict[str, Dict[str, object]] = {}
        try:
            factory = ProductFeedPayloadFactory(sales_channel_view_assign=assignment)
            for payload in factory.build():
                identifier = payload.get("id")
                if not identifier:
                    continue
                identifier_str = str(identifier)
                identifiers.add(identifier_str)
                payloads[identifier_str] = payload
        except Exception:  # pragma: no cover - safety net for factory failures
            logger.exception(
                "Failed to build GPT feed payload for assignment %s", assignment.pk
            )
        return _AssignmentPayload(identifiers=identifiers, payloads=payloads)

    def _load_existing_feed(
        self,
        *,
        sales_channel,
    ) -> Dict[str, Dict[str, object]]:
        existing = getattr(sales_channel, "gpt_feed_json", None) or []
        if isinstance(existing, dict):
            items = existing.get("items", [])
        else:
            items = existing
        entries: Dict[str, Dict[str, object]] = {}
        for item in items:
            identifier = item.get("id")
            if not identifier:
                continue
            entries[str(identifier)] = item
        return entries

    def _merge_entries(
        self,
        *,
        sales_channel,
        existing_entries: Dict[str, Dict[str, object]],
        assignments: Dict[int, _AssignmentPayload],
    ) -> Dict[str, Dict[str, object]] | None:
        if not assignments and not self.sync_all:
            return None

        merged = {} if self.sync_all else dict(existing_entries)

        for payload in assignments.values():
            for identifier, item in payload.payloads.items():
                merged[identifier] = item

        if not self.sync_all:
            for payload in assignments.values():
                for identifier in payload.identifiers:
                    if identifier not in payload.payloads:
                        merged.pop(identifier, None)

        if not self.sync_all and merged == existing_entries:
            return None

        return merged

    def _persist_feed(
        self,
        *,
        sales_channel,
        entries: Dict[str, Dict[str, object]],
    ) -> None:
        ordered = [entries[key] for key in sorted(entries.keys())]
        sales_channel.gpt_feed_json = ordered
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        filename = f"gpt-feed-{sales_channel.pk}-{timestamp}.json"
        content = json.dumps(ordered, ensure_ascii=False, indent=2, default=str)
        sales_channel.gpt_feed_file.save(filename, ContentFile(content), save=False)
        sales_channel.save(update_fields=["gpt_feed_json", "gpt_feed_file"])

    def _send_feed(
        self,
        *,
        sales_channel,
        entries: Dict[str, Dict[str, object]],
    ) -> None:
        logger.debug(
            "Mock send GPT feed for sales_channel_id=%s entries=%s",
            sales_channel.id,
            list(entries.keys()),
        )

    def _clear_required_flags(
        self,
        *,
        remote_product_ids: Iterable[int],
    ) -> None:
        ids = {remote_id for remote_id in remote_product_ids if remote_id}
        if not ids:
            return
        RemoteProduct.objects.filter(id__in=ids).update(required_feed_sync=False)
