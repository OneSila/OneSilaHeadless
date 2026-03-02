"""Factories to translate Shein document type labels into company language."""

from __future__ import annotations

import re

from llm.flows.remote_translations import TranslateRemotePropertyFlow
from sales_channels.integrations.shein.models import SheinDocumentType


class SheinDocumentTypeTranslationFactory:
    """Translate a Shein document type name when ``translated_name`` is missing."""

    CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
    CERTIFICATE_TYPE_ID_RE = re.compile(
        r"(?i)\s*certificate[_\s-]*type[_\s-]*id\s*\d+\s*"
    )
    MULTI_SPACE_RE = re.compile(r"\s+")

    def __init__(self, *, document_type: SheinDocumentType) -> None:
        self.document_type = document_type

    def run(self) -> str | None:
        current_translated_name = (self.document_type.translated_name or "").strip()
        if current_translated_name:
            return current_translated_name

        source_name = self._build_source_name()
        if not source_name:
            return None

        if not self._contains_cjk(text=source_name):
            self._save_translated_name(translated_name=source_name)
            return source_name

        flow = TranslateRemotePropertyFlow(
            instance=self.document_type,
            integration_label="SHEIN",
            remote_name_fields=(lambda _instance: source_name,),
            translation_field="translated_name",
            remote_identifier_attr="remote_id",
            remote_language_getter=(lambda _instance: "zh"),
            target_language_getter=self._get_target_language,
        )
        translated_name = flow.flow() or source_name
        translated_name = self._clean_document_type_name(text=translated_name)
        if not translated_name:
            translated_name = source_name

        self._save_translated_name(translated_name=translated_name)
        return translated_name

    def _build_source_name(self) -> str:
        base_name = self.document_type.name or self.document_type.remote_id or ""
        return self._clean_document_type_name(text=base_name)

    @staticmethod
    def _get_target_language(instance: SheinDocumentType) -> str:
        company = getattr(instance.sales_channel, "multi_tenant_company", None)
        return getattr(company, "language", None) or "en"

    def _clean_document_type_name(self, *, text: str) -> str:
        value = str(text or "").strip()
        if not value:
            return ""

        value = self.CERTIFICATE_TYPE_ID_RE.sub(" ", value)
        value = self.MULTI_SPACE_RE.sub(" ", value).strip(" -_:;,")
        return value

    def _save_translated_name(self, *, translated_name: str) -> None:
        if self.document_type.translated_name == translated_name:
            return

        self.document_type.translated_name = translated_name
        self.document_type.save(update_fields=["translated_name"])

    @classmethod
    def _contains_cjk(cls, *, text: str) -> bool:
        return bool(cls.CJK_RE.search(text or ""))
