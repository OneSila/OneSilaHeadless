from typing import List
from urllib.parse import urlparse

from core.schema.core.queries import type, field, anonymous_field
from django.conf import settings
from django.utils.translation import activate, get_language_info, deactivate
from integrations.constants import (
    AMAZON_INTEGRATION,
    EBAY_INTEGRATION,
    MANUAL_INTEGRATION,
    SHEIN_INTEGRATION,
    INTEGRATIONS_TYPES_MAP,
)
from sales_channels.models import SalesChannel

from core.schema.core.helpers import get_multi_tenant_company, get_current_user
from core.schema.languages.types.types import ContentViewType, LanguageType


def _build_language_type(*, code: str) -> LanguageType:
    language_info = get_language_info(code)
    return LanguageType(
        bidi=language_info["bidi"],
        code=code,
        name=language_info["name"],
        name_local=language_info["name_local"],
        name_translated=language_info["name_translated"],
    )


def get_languages(info) -> List[LanguageType]:
    user = get_current_user(info)

    if not user.is_anonymous:
        activate(user.language)

    languages = [_build_language_type(code=code) for code, _ in settings.LANGUAGES]

    if not user.is_anonymous:
        deactivate()

    return languages


def get_interface_languages(info) -> List[LanguageType]:
    user = get_current_user(info)

    if not user.is_anonymous:
        activate(user.language)

    languages = [_build_language_type(code=code) for code, _ in settings.INTERFACE_LANGUAGES]

    if not user.is_anonymous:
        deactivate()

    return languages


def get_default_language() -> LanguageType:
    return _build_language_type(code=settings.LANGUAGE_CODE)


def get_current_user_language(info) -> LanguageType:
    user = get_current_user(info)
    activate(user.language)
    lang = _build_language_type(code=user.language)
    deactivate()
    return lang


def get_company_languages(info) -> List[LanguageType]:
    user = get_current_user(info)
    activate(user.language)

    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    allowed_codes = set(multi_tenant_company.languages or [multi_tenant_company.language])

    languages = [
        _build_language_type(code=code)
        for code, _ in settings.LANGUAGES
        if code in allowed_codes
    ]

    deactivate()
    return languages


def _format_sales_channel_label(*, sales_channel: SalesChannel) -> str:
    raw_label = str(getattr(sales_channel, "hostname", "") or "").strip()
    if not raw_label:
        return "Unknown"

    integration_type = INTEGRATIONS_TYPES_MAP.get(sales_channel.__class__)
    if integration_type in {AMAZON_INTEGRATION, EBAY_INTEGRATION, SHEIN_INTEGRATION, MANUAL_INTEGRATION}:
        return raw_label

    try:
        parsed = urlparse(
            raw_label if raw_label.startswith(("http://", "https://")) else f"https://{raw_label}"
        )
        hostname = (parsed.hostname or raw_label).strip()
        return hostname[4:] if hostname.lower().startswith("www.") else hostname
    except Exception:
        return raw_label


def get_company_content_views(info) -> List[ContentViewType]:
    user = get_current_user(info)
    activate(user.language)

    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    allowed_codes = set(multi_tenant_company.languages or [multi_tenant_company.language])

    language_data = [
        (code, get_language_info(code))
        for code, _ in settings.LANGUAGES
        if code in allowed_codes
    ]

    content_views = [
        ContentViewType(
            key=f"0.{code}",
            name=f"Default - {language_info['name']}",
        )
        for code, language_info in language_data
    ]

    sales_channels = SalesChannel.objects.filter(
        multi_tenant_company=multi_tenant_company
    ).order_by("id")

    for sales_channel in sales_channels:
        sales_channel_label = _format_sales_channel_label(sales_channel=sales_channel)
        for code, language_info in language_data:
            content_views.append(
                ContentViewType(
                    key=f"{sales_channel.id}.{code}",
                    name=f"{sales_channel_label} - {language_info['name']}",
                )
            )

    deactivate()
    return content_views


@type(name="Query")
class LanguageQuery:
    default_language: LanguageType = anonymous_field(resolver=get_default_language)
    current_user_language: LanguageType = field(resolver=get_current_user_language)
    languages: List[LanguageType] = anonymous_field(resolver=get_languages)
    interface_languages: List[LanguageType] = anonymous_field(resolver=get_interface_languages)
    company_languages: List[LanguageType] = field(resolver=get_company_languages)
    company_content_views: List[ContentViewType] = field(resolver=get_company_content_views)
