from __future__ import annotations

from typing import Any

from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import EbayStoreCategory
from sales_channels.models.logs import RemoteLog


class EbayStoreCategoryPullFactory(GetEbayAPIMixin, PullRemoteInstanceMixin):
    """Pull and synchronize eBay store categories for a sales channel."""

    remote_model_class = EbayStoreCategory
    field_mapping = {
        "remote_id": "category_id",
        "name": "category_name",
        "order": "order",
        "level": "level",
        "is_leaf": "is_leaf",
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ["remote_id"]

    allow_create = True
    allow_update = True
    allow_delete = True
    is_model_response = False

    def fetch_remote_instances(self):
        response = self.get_store_categories()

        if not isinstance(response, dict):
            raise ValueError("Unexpected eBay store categories payload.")

        raw_categories = response.get("storeCategories")
        if raw_categories is None:
            raise ValueError("Missing 'storeCategories' in eBay response.")
        if not isinstance(raw_categories, list):
            raise ValueError("'storeCategories' must be a list.")

        self.remote_instances = self._flatten_categories(
            categories=raw_categories,
            parent_remote_id=None,
            fallback_level=1,
        )

    def _flatten_categories(
        self,
        *,
        categories: list[Any],
        parent_remote_id: str | None,
        fallback_level: int,
    ) -> list[dict[str, Any]]:
        flattened: list[dict[str, Any]] = []

        for index, category in enumerate(categories):
            if not isinstance(category, dict):
                continue

            category_id = category.get("categoryId")
            category_name = category.get("categoryName")
            if category_id is None or not category_name:
                continue

            raw_children = category.get("childrenCategories") or []
            children = raw_children if isinstance(raw_children, list) else []

            raw_level = category.get("level")
            level = raw_level if isinstance(raw_level, int) and raw_level > 0 else fallback_level

            raw_order = category.get("order")
            order = raw_order if isinstance(raw_order, int) else index

            normalized_entry = {
                "category_id": str(category_id),
                "category_name": str(category_name),
                "order": order,
                "level": level,
                "is_leaf": len(children) == 0,
                "parent_remote_id": str(parent_remote_id) if parent_remote_id else None,
            }
            flattened.append(normalized_entry)

            flattened.extend(
                self._flatten_categories(
                    categories=children,
                    parent_remote_id=normalized_entry["category_id"],
                    fallback_level=level + 1,
                )
            )

        return flattened

    def create_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        super().create_remote_instance_mirror(remote_data, remote_instance_mirror)
        self._set_parent(remote_instance_mirror=remote_instance_mirror, remote_data=remote_data)

    def add_fields_to_remote_instance_mirror(self, remote_data, remote_instance_mirror):
        self._set_parent(remote_instance_mirror=remote_instance_mirror, remote_data=remote_data)

    def _set_parent(self, *, remote_instance_mirror: EbayStoreCategory, remote_data: dict[str, Any]) -> None:
        parent_remote_id = remote_data.get("parent_remote_id")
        parent = None
        if parent_remote_id:
            parent = self.remote_model_class.objects.filter(
                sales_channel=self.sales_channel,
                remote_id=str(parent_remote_id),
            ).first()

        parent_id = parent.id if parent else None
        if remote_instance_mirror.parent_id != parent_id:
            remote_instance_mirror.parent = parent
            remote_instance_mirror.save(update_fields=["parent"])

    def needs_update(self, remote_instance_mirror, remote_data):
        if super().needs_update(remote_instance_mirror, remote_data):
            return True

        parent_remote_id = remote_data.get("parent_remote_id")
        current_parent_remote_id = (
            str(remote_instance_mirror.parent.remote_id)
            if remote_instance_mirror.parent and remote_instance_mirror.parent.remote_id
            else None
        )
        return (str(parent_remote_id) if parent_remote_id is not None else None) != current_parent_remote_id

    def delete_missing_remote_instance_mirrors(self, existing_remote_ids):
        existing_ids = {str(remote_id) for remote_id in existing_remote_ids if remote_id is not None}

        for remote_instance_mirror in self.remote_model_class.objects.filter(sales_channel=self.sales_channel):
            if str(remote_instance_mirror.remote_id) in existing_ids:
                continue

            remote_instance_mirror.delete()
