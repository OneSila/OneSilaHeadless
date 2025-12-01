from __future__ import annotations

from typing import Any, Dict, List, Optional

from media.models import Media, MediaProductThrough
from sales_channels.factories.products.images import (
    RemoteMediaProductThroughCreateFactory,
    RemoteMediaProductThroughDeleteFactory,
    RemoteMediaProductThroughUpdateFactory,
)
from sales_channels.models.products import RemoteImageProductAssociation


class SheinMediaProductThroughBase:
    """Build Shein-ready image payloads for product assignments."""

    remote_model_class = RemoteImageProductAssociation

    def __init__(
        self,
        *args: Any,
        get_value_only: bool = False,
        **kwargs: Any,
    ) -> None:
        self.get_value_only = get_value_only
        self.value: Optional[Dict[str, Any]] = None
        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _collect_image_throughs(self) -> List[MediaProductThrough]:
        product = self.remote_product.local_instance
        queryset = MediaProductThrough._base_manager.filter(
            product=product,
        )
        if self.sales_channel:
            channel_qs = queryset.filter(sales_channel=self.sales_channel)
            queryset = channel_qs if channel_qs.exists() else queryset.filter(sales_channel__isnull=True)
        else:
            queryset = queryset.filter(sales_channel__isnull=True)

        return list(queryset.filter(media__type=Media.IMAGE).order_by("sort_order"))

    def _resolve_image_url(self, media: Media) -> Optional[str]:
        if hasattr(media, "image_url") and callable(getattr(media, "image_url")):
            url = media.image_url()
            if url:
                return url
        url = getattr(media, "image_url", None)
        if isinstance(url, str) and url.strip():
            return url.strip()
        if hasattr(media, "image_web_url") and getattr(media, "image_web_url"):
            return media.image_web_url
        if getattr(media, "video_url", None):
            return media.video_url
        if getattr(media, "description", None):
            return media.description
        if hasattr(media, "onesila_thumbnail_url"):
            thumb = media.onesila_thumbnail_url()
            if thumb:
                return thumb
        return None

    def _build_image_entries(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for idx, through in enumerate(self._collect_image_throughs(), start=1):
            image_url = self._resolve_image_url(through.media)
            if not image_url:
                continue

            image_type = 1 if through.is_main_image else 2

            entries.append(
                {
                    "image_sort": through.sales_channels_sort_order if hasattr(through, "sales_channels_sort_order") else idx,
                    "image_type": image_type,
                    "image_url": image_url,
                }
            )

        return entries

    def _build_value(self) -> Dict[str, Any]:
        return {
            "image_info": {
                "image_info_list": self._build_image_entries(),
            }
        }

    def set_api(self) -> None:
        if self.get_value_only:
            return
        super().set_api()

    def customize_remote_instance_data(self) -> dict[str, Any]:
        self.remote_instance_data["remote_product"] = self.remote_product
        return self.remote_instance_data

    def preflight_process(self):
        super().preflight_process()
        self.value = self._build_value()

    def needs_update(self) -> bool:
        return True

    def serialize_response(self, response):
        return response or {}


class SheinMediaProductThroughCreateFactory(
    SheinMediaProductThroughBase,
    RemoteMediaProductThroughCreateFactory,
):
    def create_remote(self):
        return self.value

    def set_remote_id(self, response):
        # Shein media payloads do not yield a remote id on value-only mode.
        pass


class SheinMediaProductThroughUpdateFactory(
    SheinMediaProductThroughBase,
    RemoteMediaProductThroughUpdateFactory,
):
    create_factory_class = SheinMediaProductThroughCreateFactory

    def update_remote(self):
        return self.value


class SheinMediaProductThroughDeleteFactory(
    SheinMediaProductThroughBase,
    RemoteMediaProductThroughDeleteFactory,
):
    delete_remote_instance = True

    def delete_remote(self):
        return self.value
