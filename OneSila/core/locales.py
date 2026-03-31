from __future__ import annotations

from typing import Iterable

from django.utils.translation import gettext_lazy as _


LANGUAGE_MAX_LENGTH = 16

CANONICAL_LANGUAGES = (
    ("en-gb", _("English (United Kingdom)")),
    ("fr-fr", _("French (France)")),
    ("nl-nl", _("Dutch (Netherlands)")),
    ("de-de", _("German (Germany)")),
    ("it-it", _("Italian (Italy)")),
    ("es-es", _("Spanish (Spain)")),
    ("pt-pt", _("Portuguese (Portugal)")),
    ("pl-pl", _("Polish (Poland)")),
    ("ro-ro", _("Romanian (Romania)")),
    ("bg-bg", _("Bulgarian (Bulgaria)")),
    ("hr-hr", _("Croatian (Croatia)")),
    ("cs-cz", _("Czech (Czech Republic)")),
    ("da-dk", _("Danish (Denmark)")),
    ("et-ee", _("Estonian (Estonia)")),
    ("fi-fi", _("Finnish (Finland)")),
    ("el-gr", _("Greek (Greece)")),
    ("hu-hu", _("Hungarian (Hungary)")),
    ("lv-lv", _("Latvian (Latvia)")),
    ("lt-lt", _("Lithuanian (Lithuania)")),
    ("sk-sk", _("Slovak (Slovakia)")),
    ("sl-si", _("Slovenian (Slovenia)")),
    ("sv-se", _("Swedish (Sweden)")),
    ("th-th", _("Thai (Thailand)")),
    ("ja-jp", _("Japanese (Japan)")),
    ("zh-cn", _("Chinese (Simplified)")),
    ("hi-in", _("Hindi (India)")),
    ("pt-br", _("Portuguese (Brazil)")),
    ("ru-ru", _("Russian (Russia)")),
    ("af-za", _("Afrikaans (South Africa)")),
    ("ar-sa", _("Arabic (Saudi Arabia)")),
    ("he-il", _("Hebrew (Israel)")),
    ("tr-tr", _("Turkish (Turkey)")),
    ("id-id", _("Indonesian (Indonesia)")),
    ("ko-kr", _("Korean (South Korea)")),
    ("ms-my", _("Malay (Malaysia)")),
    ("vi-vn", _("Vietnamese (Vietnam)")),
    ("fa-ir", _("Persian (Iran)")),
    ("ur-pk", _("Urdu (Pakistan)")),

    # legacy languages, keep for better transition
    ("en", _("English")),
    ("fr", _("French")),
    ("nl", _("Dutch")),
    ("de", _("German")),
    ("it", _("Italian")),
    ("es", _("Spanish")),
    ("pt", _("Portuguese")),
    ("pl", _("Polish")),
    ("ro", _("Romanian")),
    ("bg", _("Bulgarian")),
    ("hr", _("Croatian")),
    ("cs", _("Czech")),
    ("da", _("Danish")),
    ("et", _("Estonian")),
    ("fi", _("Finnish")),
    ("el", _("Greek")),
    ("hu", _("Hungarian")),
    ("lv", _("Latvian")),
    ("lt", _("Lithuanian")),
    ("sk", _("Slovak")),
    ("sl", _("Slovenian")),
    ("sv", _("Swedish")),
    ("th", _("Thai")),
    ("ja", _("Japanese")),
    ("zh-hans", _("Chinese (Simplified)")),
    ("hi", _("Hindi")),
    ("pt-br", _("Portuguese (Brazil)")),
    ("ru", _("Russian")),
    ("af", _("Afrikaans")),
    ("ar", _("Arabic")),
    ("he", _("Hebrew")),
    ("tr", _("Turkish")),
    ("id", _("Indonesian")),
    ("ko", _("Korean")),
    ("ms", _("Malay")),
    ("vi", _("Vietnamese")),
    ("fa", _("Persian")),
    ("ur", _("Urdu")),
)

INTERFACE_LANGUAGES = (
    ("en-gb", _("English (United Kingdom)")),
    ("nl-nl", _("Dutch (Netherlands)")),
)

DEFAULT_LANGUAGE_CODE = "en-gb"

LEGACY_LANGUAGE_CONVERTOR = {
    "en": "en-gb",
    "fr": "fr-fr",
    "nl": "nl-nl",
    "de": "de-de",
    "it": "it-it",
    "es": "es-es",
    "pt": "pt-pt",
    "pl": "pl-pl",
    "ro": "ro-ro",
    "bg": "bg-bg",
    "hr": "hr-hr",
    "cs": "cs-cz",
    "da": "da-dk",
    "et": "et-ee",
    "fi": "fi-fi",
    "el": "el-gr",
    "hu": "hu-hu",
    "lv": "lv-lv",
    "lt": "lt-lt",
    "sk": "sk-sk",
    "sl": "sl-si",
    "sv": "sv-se",
    "th": "th-th",
    "ja": "ja-jp",
    "zh-hans": "zh-cn",
    "hi": "hi-in",
    "pt-br": "pt-br",
    "ru": "ru-ru",
    "af": "af-za",
    "ar": "ar-sa",
    "he": "he-il",
    "tr": "tr-tr",
    "id": "id-id",
    "ko": "ko-kr",
    "ms": "ms-my",
    "vi": "vi-vn",
    "fa": "fa-ir",
    "ur": "ur-pk",
}

_SUPPORTED_LANGUAGE_CODES = {code for code, _ in CANONICAL_LANGUAGES}
_LOWERCASE_SUPPORTED_LANGUAGE_CODES = {code.lower(): code for code in _SUPPORTED_LANGUAGE_CODES}


def get_language_root(*, code: str | None) -> str:
    normalized = str(code or "").strip()
    if not normalized:
        return ""
    return normalized.split("-")[0].lower()


def normalize_language_code(*, code: str | None, default: str | None = DEFAULT_LANGUAGE_CODE) -> str:
    normalized = str(code or "").strip()
    if not normalized:
        return default or DEFAULT_LANGUAGE_CODE

    exact = _LOWERCASE_SUPPORTED_LANGUAGE_CODES.get(normalized.lower())
    if exact:
        return exact

    lowered = normalized.lower()
    legacy = LEGACY_LANGUAGE_CONVERTOR.get(lowered)
    if legacy:
        return legacy

    language_root = get_language_root(code=normalized)
    if language_root:
        legacy = LEGACY_LANGUAGE_CONVERTOR.get(language_root)
        if legacy:
            return legacy

    return default or DEFAULT_LANGUAGE_CODE


def normalize_language_list(*, values: Iterable[str] | None) -> list[str]:
    if not values:
        return []

    normalized_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_language_code(code=value)
        if normalized in seen:
            continue
        seen.add(normalized)
        normalized_values.append(normalized)
    return normalized_values


def is_supported_language_code(*, code: str | None) -> bool:
    normalized = str(code or "").strip()
    if not normalized:
        return False
    return normalize_language_code(code=normalized, default="") in _SUPPORTED_LANGUAGE_CODES


def get_languages() -> tuple[tuple[str, str], ...]:
    return CANONICAL_LANGUAGES


def get_interface_languages() -> tuple[tuple[str, str], ...]:
    return INTERFACE_LANGUAGES
