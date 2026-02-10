from typing import Optional

from django.db.models import Exists, OuterRef, Q
from strawberry import UNSET
from strawberry.relay import from_base64
from strawberry_django import filter_field as custom_filter

from core.managers import QuerySet
from core.schema.core.types.filters import AnnotationMergerMixin
from media.models import Media, MediaProductThrough


class ProductMediaFilterMixin(AnnotationMergerMixin):
    has_images_in_sales_channel: Optional[str]
    missing_images_in_sales_channel: Optional[str]
    has_documents_in_sales_channel: Optional[str]
    missing_documents_in_sales_channel: Optional[str]
    has_videos_in_sales_channel: Optional[str]
    missing_videos_in_sales_channel: Optional[str]

    @staticmethod
    def _parse_sales_channel_id(
        *,
        value: str,
    ) -> tuple[bool, Optional[int]]:
        if value in (None, "None", "none", "null", "NULL", ""):
            return True, None

        try:
            _, sales_channel_id = from_base64(value)
            return True, int(sales_channel_id)
        except Exception:
            if str(value).isdigit():
                return True, int(value)
            return False, None

    @staticmethod
    def _media_in_sales_channel_qs(
        *,
        media_type: str,
        sales_channel_id: Optional[int],
    ):
        filters = {
            "product_id": OuterRef("pk"),
            "media__type": media_type,
        }
        if sales_channel_id is None:
            filters["sales_channel__isnull"] = True
        else:
            filters["sales_channel_id"] = sales_channel_id
        return MediaProductThrough.objects.filter(**filters)

    def _filter_by_media_type(
        self,
        *,
        queryset: QuerySet,
        value: str,
        media_type: str,
        annotation_name: str,
        should_exist: bool,
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        is_valid, sales_channel_id = self._parse_sales_channel_id(value=value)
        if not is_valid:
            return queryset.none(), Q()

        media_qs = self._media_in_sales_channel_qs(
            media_type=media_type,
            sales_channel_id=sales_channel_id,
        )
        queryset = queryset.annotate(
            **{annotation_name: Exists(media_qs)}
        ).filter(
            **{annotation_name: should_exist}
        )
        return queryset, Q()

    @custom_filter
    def has_images_in_sales_channel(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        return self._filter_by_media_type(
            queryset=queryset,
            value=value,
            media_type=Media.IMAGE,
            annotation_name="has_images_in_sales_channel",
            should_exist=True,
        )

    @custom_filter
    def missing_images_in_sales_channel(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        return self._filter_by_media_type(
            queryset=queryset,
            value=value,
            media_type=Media.IMAGE,
            annotation_name="has_images_in_sales_channel",
            should_exist=False,
        )

    @custom_filter
    def has_documents_in_sales_channel(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        return self._filter_by_media_type(
            queryset=queryset,
            value=value,
            media_type=Media.FILE,
            annotation_name="has_documents_in_sales_channel",
            should_exist=True,
        )

    @custom_filter
    def missing_documents_in_sales_channel(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        return self._filter_by_media_type(
            queryset=queryset,
            value=value,
            media_type=Media.FILE,
            annotation_name="has_documents_in_sales_channel",
            should_exist=False,
        )

    @custom_filter
    def has_videos_in_sales_channel(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        return self._filter_by_media_type(
            queryset=queryset,
            value=value,
            media_type=Media.VIDEO,
            annotation_name="has_videos_in_sales_channel",
            should_exist=True,
        )

    @custom_filter
    def missing_videos_in_sales_channel(
        self,
        *,
        queryset: QuerySet,
        value: str,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        return self._filter_by_media_type(
            queryset=queryset,
            value=value,
            media_type=Media.VIDEO,
            annotation_name="has_videos_in_sales_channel",
            should_exist=False,
        )
