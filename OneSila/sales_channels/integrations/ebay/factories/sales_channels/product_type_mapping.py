"""Utilities for mirroring eBay product type mappings across marketplaces."""

from typing import Iterable

from sales_channels.integrations.ebay.models import EbayCategory, EbayProductType


class EbayProductTypeRemoteMappingFactory:
    """Propagate a mapped eBay product type across sibling marketplaces."""

    def __init__(self, *, product_type: EbayProductType) -> None:
        self.product_type = product_type
        self.remote_id: str = ""
        self.source_tree_id: str = ""
        self.target_tree_ids: set[str] = set()
        self._related_product_types: list[EbayProductType] = []
        self._should_run = True

    def run(self) -> None:
        """Assign the product type's remote id to matching marketplaces."""

        self._initialize_context()
        self._load_target_tree_ids()
        self._load_related_product_types()
        self._apply_remote_id_to_related_product_types()

    def _initialize_context(self) -> None:
        self._should_run = True
        self.remote_id = ""
        self.source_tree_id = ""
        self.target_tree_ids = set()
        self._related_product_types = []

        product_type = self.product_type

        self.remote_id = (product_type.remote_id or "").strip()
        if not self.remote_id:
            self._should_run = False
            return

        if not product_type.local_instance_id:
            self._should_run = False
            return

        marketplace = product_type.marketplace
        if marketplace is None:
            self._should_run = False
            return

        self.source_tree_id = (
            getattr(marketplace, "default_category_tree_id", None) or ""
        ).strip()
        if not self.source_tree_id:
            self._should_run = False

    def _load_target_tree_ids(self) -> None:
        if not self._should_run:
            return

        self.target_tree_ids = self._collect_target_tree_ids(
            remote_id=self.remote_id,
            source_tree_id=self.source_tree_id,
        )

        if not self.target_tree_ids:
            self._should_run = False

    def _load_related_product_types(self) -> None:
        if not self._should_run:
            return

        product_type = self.product_type
        queryset = EbayProductType.objects.filter(
            sales_channel=product_type.sales_channel,
            multi_tenant_company=product_type.multi_tenant_company,
            local_instance=product_type.local_instance,
            marketplace__default_category_tree_id__in=self.target_tree_ids,
        ).exclude(pk=product_type.pk)

        self._related_product_types = list(queryset.iterator())

    def _apply_remote_id_to_related_product_types(self) -> None:
        if not self._should_run or not self._related_product_types:
            return

        updates: list[EbayProductType] = []
        for candidate in self._related_product_types:
            current_remote_id = (candidate.remote_id or "").strip()
            if current_remote_id and current_remote_id != self.remote_id:
                continue
            if current_remote_id == self.remote_id:
                continue
            candidate.remote_id = self.remote_id
            updates.append(candidate)

        for candidate in updates:
            candidate.save(update_fields=["remote_id"])

    def _collect_target_tree_ids(self, *, remote_id: str, source_tree_id: str) -> set[str]:
        """Return marketplace tree ids that share the given remote category id."""

        tree_ids: Iterable[str | None] = (
            EbayCategory.objects.filter(remote_id=remote_id)
            .exclude(marketplace_default_tree_id=source_tree_id)
            .values_list("marketplace_default_tree_id", flat=True)
        )
        return {tree_id for tree_id in tree_ids if tree_id}
