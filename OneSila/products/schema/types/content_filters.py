from enum import Enum
from typing import Optional
import re

import strawberry
from django.db.models import Exists, OuterRef, Q
from strawberry import UNSET
from strawberry_django import filter_field as custom_filter

from core.managers import QuerySet
from core.models import MultiTenantCompany
from core.schema.core.types.filters import AnnotationMergerMixin
from products.models import ProductTranslation, ProductTranslationBulletPoint
from products.schema.types.enums import ContentField
from sales_channels.models import SalesChannel


@strawberry.input
class ProductContentFieldViewInput:
    content_view_key: str
    field: ContentField


class ProductContentFieldFilterMixin(AnnotationMergerMixin):
    content_field_in_view: Optional[ProductContentFieldViewInput]

    _EMPTY_RICH_TEXT = "<p><br></p>"
    _FIELD_TO_TRANSLATION_ATTR = {
        ContentField.DESCRIPTION.value: "description",
        ContentField.SHORT_DESCRIPTION.value: "short_description",
        ContentField.SUBTITLE.value: "subtitle",
        ContentField.NAME.value: "name",
        ContentField.URL_KEY.value: "url_key",
    }

    def _parse_content_view_key(
        self,
        *,
        content_view_key: str,
    ) -> tuple[Optional[int], Optional[str]]:
        try:
            sales_channel_raw, language_code = content_view_key.split(".", 1)
        except ValueError:
            return None, None

        language_code = (language_code or "").strip()
        if not language_code:
            return None, None

        sales_channel_raw = (sales_channel_raw or "").strip()
        if sales_channel_raw == "0":
            return 0, language_code

        try:
            return int(sales_channel_raw), language_code
        except (TypeError, ValueError):
            return None, None

    def _get_company_language_codes(
        self,
        *,
        company_id: Optional[int],
    ) -> set[str]:
        if not company_id:
            return set()

        company = (
            MultiTenantCompany.objects.filter(pk=company_id)
            .only("languages", "language")
            .first()
        )
        if company is None:
            return set()

        return set(company.languages or [company.language])

    def _is_valid_sales_channel(
        self,
        *,
        company_id: int,
        sales_channel_id: int,
    ) -> bool:
        return SalesChannel.objects.filter(
            pk=sales_channel_id,
            multi_tenant_company_id=company_id,
        ).exists()

    def _non_empty_text_q(
        self,
        *,
        field_name: str,
    ) -> Q:
        return (
            ~Q(**{f"{field_name}__isnull": True})
            & ~Q(**{field_name: ""})
            & ~Q(**{field_name: self._EMPTY_RICH_TEXT})
        )

    @staticmethod
    def _annotation_alias(
        *,
        field_value: str,
        sales_channel_id: int,
        language_code: str,
    ) -> str:
        raw_alias = f"has_content_field_{field_value}_{sales_channel_id}_{language_code}"
        return re.sub(r"[^0-9a-zA-Z_]", "_", raw_alias)

    @custom_filter
    def content_field_in_view(
        self,
        *,
        queryset: QuerySet,
        value: ProductContentFieldViewInput,
        prefix: str,
    ) -> tuple[QuerySet, Q]:
        if value in (None, UNSET):
            return queryset, Q()

        sales_channel_id, language_code = self._parse_content_view_key(
            content_view_key=value.content_view_key
        )
        if sales_channel_id is None or language_code is None:
            return queryset.none(), Q()

        company_id = queryset.values_list("multi_tenant_company_id", flat=True).first()
        if not company_id:
            return queryset.none(), Q()

        allowed_codes = self._get_company_language_codes(company_id=company_id)
        if language_code not in allowed_codes:
            return queryset.none(), Q()

        if sales_channel_id != 0 and not self._is_valid_sales_channel(
            company_id=company_id,
            sales_channel_id=sales_channel_id,
        ):
            return queryset.none(), Q()

        field_value = value.field.value if isinstance(value.field, Enum) else str(value.field)
        translation_filters = {
            "product_id": OuterRef("pk"),
            "language": language_code,
        }

        if sales_channel_id == 0:
            translation_filters["sales_channel__isnull"] = True
        else:
            translation_filters["sales_channel_id"] = sales_channel_id

        if field_value == ContentField.BULLET_POINTS.value:
            content_exists_qs = ProductTranslationBulletPoint.objects.filter(
                product_translation__product_id=OuterRef("pk"),
                product_translation__language=language_code,
            ).filter(
                Q(product_translation__sales_channel__isnull=True)
                if sales_channel_id == 0
                else Q(product_translation__sales_channel_id=sales_channel_id)
            ).exclude(
                Q(text__isnull=True) | Q(text="") | Q(text=self._EMPTY_RICH_TEXT)
            )
        else:
            translation_field = self._FIELD_TO_TRANSLATION_ATTR.get(field_value)
            if not translation_field:
                return queryset.none(), Q()

            content_exists_qs = ProductTranslation.objects.filter(
                **translation_filters
            ).filter(
                self._non_empty_text_q(field_name=translation_field)
            )

        annotation_name = self._annotation_alias(
            field_value=field_value,
            sales_channel_id=sales_channel_id,
            language_code=language_code,
        )
        queryset = queryset.annotate(
            **{annotation_name: Exists(content_exists_qs)}
        )
        return queryset, Q(**{annotation_name: True})
