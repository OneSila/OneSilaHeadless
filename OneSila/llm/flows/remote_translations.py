from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

from llm.factories.amazon import (
    RemotePropertyTranslationLLM,
    RemoteSelectValueTranslationLLM,
)


class BaseRemoteTranslationFlow:
    """Shared logic to translate remote entities using LLMs."""

    translator_class = None

    def __init__(
        self,
        *,
        instance: Any,
        integration_label: str,
        remote_name_fields: Iterable[Any] | Any,
        translation_field: str,
        remote_language_getter: Callable[[Any], str | None] | None = None,
        target_language_getter: Callable[[Any], str | None] | None = None,
    ) -> None:
        self.instance = instance
        self.integration_label = integration_label
        self.remote_name_fields = remote_name_fields
        self.translation_field = translation_field
        self.remote_language_getter = remote_language_getter or self._default_remote_language_getter
        self.target_language_getter = target_language_getter or self._default_target_language_getter

    def flow(self) -> str | None:
        remote_text = self._get_remote_text()
        if not remote_text:
            return None

        remote_lang = self._get_remote_language()
        target_lang = self._get_target_language()

        translated = self._translate(remote_text, remote_lang, target_lang)
        self._persist_translation(translated)
        return translated

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_remote_text(self) -> str | None:
        fields = self.remote_name_fields
        if isinstance(fields, (str, tuple)):
            fields_to_check: Sequence[Any] = (fields,) if isinstance(fields, str) else fields
        elif isinstance(fields, Iterable):
            fields_to_check = tuple(fields)
        else:
            fields_to_check = (fields,)

        for field in fields_to_check:
            value = self._resolve_attribute(field)
            if value:
                return value
        return None

    def _get_remote_language(self) -> str | None:
        getter = self.remote_language_getter
        return getter(self.instance) if callable(getter) else getter

    def _get_target_language(self) -> str | None:
        getter = self.target_language_getter
        return getter(self.instance) if callable(getter) else getter

    def _translate(self, remote_text: str, remote_lang: str | None, target_lang: str | None) -> str:
        if not remote_lang or not target_lang or remote_lang == target_lang:
            return remote_text

        translator = self._build_translator(remote_text, remote_lang, target_lang)
        try:
            return translator.translate()
        except Exception:
            return remote_text

    def _build_translator(self, remote_text: str, remote_lang: str, target_lang: str):
        if self.translator_class is None:
            raise ValueError("translator_class must be defined for the flow")

        kwargs = self._translator_kwargs(remote_text, remote_lang, target_lang)
        return self.translator_class(**kwargs)

    def _translator_kwargs(self, remote_text: str, remote_lang: str, target_lang: str) -> dict[str, Any]:
        raise NotImplementedError

    def _persist_translation(self, translated: str) -> None:
        current_value = getattr(self.instance, self.translation_field, None)
        if current_value != translated:
            setattr(self.instance, self.translation_field, translated)
            self.instance.save(update_fields=[self.translation_field])

    def _resolve_attribute(self, attr_path: Any) -> Any:
        if attr_path is None:
            return None

        if callable(attr_path):
            return attr_path(self.instance)

        value = self.instance

        if isinstance(attr_path, str):
            parts = attr_path.split(".")
        elif isinstance(attr_path, (list, tuple)):
            parts = list(attr_path)
        else:
            return getattr(value, attr_path, None)

        for part in parts:
            if value is None:
                return None
            value = getattr(value, part, None)
        return value

    @staticmethod
    def _default_remote_language_getter(instance: Any) -> str | None:
        marketplace = getattr(instance, "marketplace", None)
        if marketplace is None:
            return None

        remote_languages = getattr(marketplace, "remote_languages", None)
        if remote_languages is None:
            return None

        remote_language_obj = remote_languages.first()
        if not remote_language_obj:
            return None

        return getattr(remote_language_obj, "local_instance", None)

    @staticmethod
    def _default_target_language_getter(instance: Any) -> str | None:
        sales_channel = getattr(instance, "sales_channel", None)
        if sales_channel is None:
            return None

        company = getattr(sales_channel, "multi_tenant_company", None)
        if company is None:
            return None

        return getattr(company, "language", None)


class TranslateRemoteSelectValueFlow(BaseRemoteTranslationFlow):
    """Translate remote property select values and persist the result."""

    translator_class = RemoteSelectValueTranslationLLM

    def __init__(
        self,
        *,
        instance: Any,
        integration_label: str,
        remote_name_fields: Iterable[Any] | Any,
        translation_field: str,
        property_name_attr: Any | None = None,
        property_code_attr: Any | None = None,
        remote_language_getter: Callable[[Any], str | None] | None = None,
        target_language_getter: Callable[[Any], str | None] | None = None,
    ) -> None:
        super().__init__(
            instance=instance,
            integration_label=integration_label,
            remote_name_fields=remote_name_fields,
            translation_field=translation_field,
            remote_language_getter=remote_language_getter,
            target_language_getter=target_language_getter,
        )
        self.property_name_attr = property_name_attr
        self.property_code_attr = property_code_attr

    def _translator_kwargs(self, remote_text: str, remote_lang: str, target_lang: str) -> dict[str, Any]:
        return {
            "integration_label": self.integration_label,
            "remote_name": remote_text,
            "from_language_code": remote_lang,
            "to_language_code": target_lang,
            "property_name": self._resolve_attribute(self.property_name_attr),
            "property_code": self._resolve_attribute(self.property_code_attr),
        }


class TranslateRemotePropertyFlow(BaseRemoteTranslationFlow):
    """Translate remote property names and persist the result."""

    translator_class = RemotePropertyTranslationLLM

    def __init__(
        self,
        *,
        instance: Any,
        integration_label: str,
        remote_name_fields: Iterable[Any] | Any,
        translation_field: str,
        remote_identifier_attr: Any | None = None,
        remote_language_getter: Callable[[Any], str | None] | None = None,
        target_language_getter: Callable[[Any], str | None] | None = None,
    ) -> None:
        super().__init__(
            instance=instance,
            integration_label=integration_label,
            remote_name_fields=remote_name_fields,
            translation_field=translation_field,
            remote_language_getter=remote_language_getter,
            target_language_getter=target_language_getter,
        )
        self.remote_identifier_attr = remote_identifier_attr

    def _translator_kwargs(self, remote_text: str, remote_lang: str, target_lang: str) -> dict[str, Any]:
        return {
            "integration_label": self.integration_label,
            "remote_name": remote_text,
            "from_language_code": remote_lang,
            "to_language_code": target_lang,
            "remote_identifier": self._resolve_attribute(self.remote_identifier_attr),
        }
