from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.conf import settings

from media.models import Media, MediaProductThrough
from sales_channels.exceptions import PreFlightCheckError
from get_absolute_url.helpers import generate_absolute_url
from sales_channels.factories.products.images import (
    RemoteMediaProductThroughCreateFactory,
    RemoteMediaProductThroughDeleteFactory,
    RemoteMediaProductThroughUpdateFactory,
)
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import SheinImageProductAssociation


class SheinMediaProductThroughBase(SheinSignatureMixin):
    """Build Shein-ready image payloads for product assignments."""

    remote_model_class = SheinImageProductAssociation

    _TESTING_IMAGE_SIZES: dict[int, tuple[int, int]] = {
        1: (1340, 1785),  # main
        2: (1340, 1785),  # detail
        5: (900, 900),  # square
        6: (80, 80),  # color block
        7: (900, 1200),  # detail page
    }

    def __init__(
        self,
        *args: Any,
        get_value_only: bool = False,
        product_instance: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        self.get_value_only = get_value_only
        self.value: Optional[Dict[str, Any]] = None
        self._transformed_cache: dict[str, str] = {}
        self.product_instance = product_instance
        super().__init__(*args, **kwargs)

    def run(self):  # type: ignore[override]
        if self.get_value_only:
            self.value = self._build_value()
            return self.value
        return super().run()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _collect_image_throughs(self) -> List[MediaProductThrough]:
        product = self.product_instance or getattr(self.remote_product, "local_instance", None)
        if product is None:
            return []
        return list(
            MediaProductThrough.objects.get_product_images(
                product=product,
                sales_channel=self.sales_channel,
            )
        )

    def _resolve_image_url(self, *, media: Media, image_type: int) -> Optional[str]:
        if getattr(settings, "TESTING", False):
            file_obj = getattr(media, "image_web", None)
            name = getattr(file_obj, "name", "") if file_obj is not None else ""
            fname = name.split("/")[-1] if name else ""
            if fname:
                width, height = self._TESTING_IMAGE_SIZES.get(image_type, (1340, 1785))
                return f"https://www.onesila.com/testing/{fname}?w={width}&h={height}"

        if media.image is not None:
            spec_attr = {
                1: "shein_main_image",
                2: "shein_detail_image",
                5: "shein_square_image",
                6: "shein_color_block_image",
                7: "shein_detail_page_image",
            }.get(image_type, "shein_detail_image")
            spec = getattr(media, spec_attr, None)
            url = getattr(spec, "url", None) if spec is not None else None
            if url:
                return f"{generate_absolute_url(trailing_slash=False)}{url}"

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
        return None

    def _transform_image(self, *, url: str, image_type: int) -> Optional[str]:
        if not url:
            return None
        cache_key = f"{image_type}:{url}"
        cached = self._transformed_cache.get(cache_key)
        if cached:
            return cached

        try:
            response = self.shein_post(
                path="/open-api/goods/transform-pic",
                payload={"image_type": image_type, "original_url": url},
            )
            data = response.json() if hasattr(response, "json") else {}
            info = data.get("info") if isinstance(data, dict) else {}
            transformed = info.get("transformed") if isinstance(info, dict) else None
            failure_reason = info.get("failure_reason") if isinstance(info, dict) else None
            code = data.get("code") if isinstance(data, dict) else None
            msg = data.get("msg") if isinstance(data, dict) else None
        except Exception:
            transformed = None
            failure_reason = None
            code = None
            msg = None

        final_url = str(transformed or "").strip()
        if not final_url:
            details = failure_reason or msg or code or "Unknown Shein transform failure."
            raise PreFlightCheckError(f"Shein image conversion failed: {details} (url={url})")

        self._transformed_cache[cache_key] = final_url
        return final_url

    def _build_image_entries(self) -> tuple[List[Dict[str, Any]], Optional[str]]:
        throughs = self._collect_image_throughs()
        if not throughs:
            return [], None

        main_through = next((t for t in throughs if getattr(t, "is_main_image", False)), None) or throughs[0]
        image_group_code: Optional[str] = None

        def build_entry(*, through: MediaProductThrough, image_type: int, sort: int) -> Optional[Dict[str, Any]]:
            image_url = self._resolve_image_url(media=through.media, image_type=image_type)
            if not image_url:
                return None

            association, _ = self.remote_model_class.objects.get_or_create(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
                local_instance=through,
            )

            nonlocal image_group_code
            if not image_group_code:
                image_group_code = getattr(association, "image_group_code", None)

            cached_remote_url = str(getattr(association, "remote_url", "") or "").strip()
            cached_original_url = str(getattr(association, "original_url", "") or "").strip()
            cached_type = getattr(association, "image_type", None)

            if cached_remote_url and cached_original_url == image_url and cached_type == image_type:
                transformed_url = cached_remote_url
            else:
                transformed_url = self._transform_image(url=image_url, image_type=image_type) or ""
                association.original_url = image_url
                association.image_type = image_type
                association.remote_url = transformed_url
                association.save(update_fields=["original_url", "image_type", "remote_url"])

            entry: Dict[str, Any] = {
                "image_sort": sort,
                "image_type": image_type,
                "image_url": transformed_url,
            }
            if getattr(association, "remote_id", None):
                entry["image_item_id"] = association.remote_id
            return entry

        entries: List[Dict[str, Any]] = []

        main_entry = build_entry(through=main_through, image_type=1, sort=1)
        if main_entry:
            entries.append(main_entry)

        remaining_throughs = [through for through in throughs if through != main_through]
        square_through = remaining_throughs[0] if remaining_throughs else main_through
        square_entry = build_entry(through=square_through, image_type=5, sort=2)
        if square_entry:
            entries.append(square_entry)

        product = self.product_instance or getattr(self.remote_product, "local_instance", None)
        is_variation = False
        if product is not None and hasattr(product, "configurables"):
            is_variation = product.is_simple() and product.configurables.exists()

        non_square_throughs = [through for through in remaining_throughs if through != square_through]
        detail_throughs = list(non_square_throughs)

        if is_variation:
            color_through = MediaProductThrough.objects.get_product_color_image(
                product=product,
                sales_channel=self.sales_channel,
            )
        else:
            color_through = None

        sort = 3
        for through in detail_throughs[:10]:
            detail_entry = build_entry(through=through, image_type=2, sort=sort)
            if detail_entry:
                entries.append(detail_entry)
                sort += 1

        if color_through:
            color_entry = build_entry(through=color_through, image_type=6, sort=sort)
            if color_entry:
                entries.append(color_entry)

        return entries, image_group_code

    def _build_value(self) -> Dict[str, Any]:
        image_entries, image_group_code = self._build_image_entries()
        image_info: Dict[str, Any] = {"image_info_list": image_entries}
        if image_group_code:
            image_info["image_group_code"] = image_group_code
        return {"image_info": image_info}

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
