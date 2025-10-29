import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from llm.factories import ProductFeedPayloadFactory
from sales_channels.models import (
    RemoteProduct,
    SalesChannel,
    SalesChannelGptFeed,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _RemoteProductPayload:
    identifiers: Set[str]
    payloads: Dict[str, Dict[str, object]]


class SalesChannelGptProductFeedFactory:
    """Synchronise GPT product feeds for sales channels."""

    def __init__(
        self,
        *,
        sync_all: bool = False,
        sales_channel_id: int | None = None,
        deleted_sku: str | None = None,
    ) -> None:
        self.sync_all = sync_all
        self.sales_channel_id = sales_channel_id
        self.deleted_sku = deleted_sku

    def run(self) -> None:
        if self.deleted_sku:
            self._run_deletion_flow()
            return

        self._run_sync_flow()

    def _run_sync_flow(self) -> None:
        remote_queryset = self._collect_remote_products()
        remote_products = list(remote_queryset)
        if not remote_products:
            return

        grouped = self._group_by_sales_channel(remote_products=remote_products)

        processed_remote_ids: Set[int] = set()

        for sales_channel, channel_products in grouped:
            processed_remote_ids.update(product.id for product in channel_products)
            payloads = [
                self._build_payload_for_remote_product(remote_product=remote_product)
                for remote_product in channel_products
            ]

            feed = self._get_feed_for_channel(sales_channel=sales_channel)
            existing_entries = self._load_existing_feed(feed=feed)
            updated_entries = self._merge_entries(
                existing_entries=existing_entries,
                payloads=payloads,
            )

            if updated_entries is None:
                continue

            with transaction.atomic():
                self._persist_feed(
                    feed=feed,
                    entries=updated_entries,
                )

        if processed_remote_ids:
            self._clear_required_flags(remote_product_ids=processed_remote_ids)

    def _collect_remote_products(self) -> List[RemoteProduct]:
        queryset = RemoteProduct.objects.filter(
            sales_channel__gpt_enable=True,
            is_variation=False,
            local_instance__active=True
        )
        if self.sales_channel_id is not None:
            queryset = queryset.filter(sales_channel_id=self.sales_channel_id)
        if not self.sync_all:
            queryset = queryset.filter(required_feed_sync=True)

        return (
            queryset
            .select_related("sales_channel", "local_instance")
            .order_by("sales_channel_id", "id")
        )

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

    def _build_payload_for_remote_product(
        self,
        *,
        remote_product: RemoteProduct,
    ) -> _RemoteProductPayload:
        identifiers: Set[str] = set()
        payloads: Dict[str, Dict[str, object]] = {}

        local_product = getattr(remote_product, "local_instance", None)
        sku = getattr(local_product, "sku", None)
        if sku:
            identifiers.add(str(sku))

        try:
            if local_product and local_product.is_configurable():
                for variation in local_product.get_configurable_variations(active_only=False):
                    variation_sku = getattr(variation, "sku", None)
                    if variation_sku:
                        identifiers.add(str(variation_sku))
        except AttributeError:
            pass

        try:
            factory = ProductFeedPayloadFactory(remote_product=remote_product)
            for payload in factory.build():
                identifier = payload.get("id")
                if not identifier:
                    continue
                identifier_str = str(identifier)
                identifiers.add(identifier_str)
                payloads[identifier_str] = payload
        except Exception:  # pragma: no cover - safety net for factory failures
            logger.exception(
                "Failed to build GPT feed payload for remote product %s",
                getattr(remote_product, "pk", None),
            )

        return _RemoteProductPayload(identifiers=identifiers, payloads=payloads)

    def _get_feed_for_channel(self, *, sales_channel: SalesChannel) -> SalesChannelGptFeed:
        return sales_channel.ensure_gpt_feed()

    def _load_existing_feed(
        self,
        *,
        feed: SalesChannelGptFeed,
    ) -> Dict[str, Dict[str, object]]:
        items = feed.items or []
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
        existing_entries: Dict[str, Dict[str, object]],
        payloads: Sequence[_RemoteProductPayload],
    ) -> Dict[str, Dict[str, object]] | None:
        if not payloads and not self.sync_all:
            return None

        merged = {} if self.sync_all else dict(existing_entries)

        for payload in payloads:
            for identifier, item in payload.payloads.items():
                merged[identifier] = item

        if not self.sync_all:
            for payload in payloads:
                for identifier in payload.identifiers:
                    if identifier not in payload.payloads:
                        merged.pop(identifier, None)

        if not self.sync_all and merged == existing_entries:
            return None

        return merged

    def _persist_feed(
        self,
        *,
        feed: SalesChannelGptFeed,
        entries: Dict[str, Dict[str, object]],
    ) -> None:
        ordered = [entries[key] for key in sorted(entries.keys())]
        feed.items = ordered
        company_id = getattr(feed.sales_channel, "multi_tenant_company_id", None) or 0
        unique_code = f"{company_id:08x}{feed.sales_channel_id:08x}{feed.id:08x}"
        seller_name = getattr(feed.sales_channel, "gpt_seller_name", None) or getattr(feed.sales_channel, "name", None) or str(feed.sales_channel.id)
        seller_slug = slugify(seller_name) or f"channel-{feed.sales_channel_id}"
        filename = f"gpt-feed-{feed.sales_channel_id}.{seller_slug}-{unique_code}.json"
        content = json.dumps(ordered, ensure_ascii=False, indent=2, default=str)
        if feed.file:
            feed.file.delete(save=False)
        feed.file.save(filename, ContentFile(content), save=False)
        feed.last_synced_at = timezone.now()
        feed.save(update_fields=["items", "file", "last_synced_at"])

    def _clear_required_flags(
        self,
        *,
        remote_product_ids: Iterable[int],
    ) -> None:
        ids = {remote_id for remote_id in remote_product_ids if remote_id}
        if not ids:
            return
        RemoteProduct.objects.filter(id__in=ids).update(required_feed_sync=False)

    def _run_deletion_flow(self) -> None:
        if not self.deleted_sku:
            return
        if self.sales_channel_id is None:
            logger.debug("Skipping GPT feed deletion without sales channel context.")
            return

        try:
            sales_channel = SalesChannel.objects.get(
                pk=self.sales_channel_id,
                gpt_enable=True,
            )
        except SalesChannel.DoesNotExist:
            return

        feed = self._get_feed_for_channel(sales_channel=sales_channel)
        existing_entries = self._load_existing_feed(feed=feed)
        identifier = str(self.deleted_sku)
        if identifier not in existing_entries:
            return

        existing_entries.pop(identifier, None)

        with transaction.atomic():
            self._persist_feed(feed=feed, entries=existing_entries)