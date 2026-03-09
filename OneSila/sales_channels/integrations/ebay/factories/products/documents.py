from __future__ import annotations

import os
import time
from collections.abc import Mapping
from typing import Any

from ebay_rest.api.sell_inventory.rest import ApiException
from ebay_rest.error import Error as EbayApiError

from sales_channels.exceptions import PreFlightCheckError
from sales_channels.factories.products.documents import (
    RemoteDocumentCreateFactory,
    RemoteDocumentDeleteFactory,
    RemoteDocumentProductThroughCreateFactory,
    RemoteDocumentProductThroughDeleteFactory,
    RemoteDocumentProductThroughUpdateFactory,
    RemoteDocumentUpdateFactory,
)
from sales_channels.integrations.ebay.constants import (
    EBAY_DOCUMENT_ALLOWED_EXTENSIONS,
    EBAY_DOCUMENT_LANGUAGE_BY_LOCAL_CODE,
    EBAY_DOCUMENT_MAX_FILE_SIZE_BYTES,
)
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.factories.products.mixins import EbayInventoryItemPushMixin
from sales_channels.helpers import describe_document
from sales_channels.integrations.ebay.models import (
    EbayDocumentThroughProduct,
    EbayDocumentType,
    EbayProduct,
    EbayRemoteDocument,
)


class EbayRemoteDocumentFactoryBase(GetEbayAPIMixin):
    PENDING_DOCUMENT_STATUSES = {
        EbayRemoteDocument.STATUS_PENDING_UPLOAD,
        EbayRemoteDocument.STATUS_SUBMITTED,
    }
    FAILED_DOCUMENT_STATUSES = {
        EbayRemoteDocument.STATUS_REJECTED,
        EbayRemoteDocument.STATUS_EXPIRED,
    }

    def sync_remote_document(self):
        remote_document = super().sync_remote_document()
        return self._wait_until_document_is_accepted(remote_document=remote_document)

    def _get_document_label(self):
        return describe_document(
            media=self.media,
            media_through=self.media_through,
            remote_document_type=self.remote_document_type,
        )

    def resolve_remote_document_type(self):
        if not getattr(self.media, "document_type_id", None):
            return None

        mapped_queryset = EbayDocumentType.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=self.media.document_type,
        ).exclude(remote_id__in=(None, ""))
        mapped_ids = list(mapped_queryset.values_list("id", flat=True))
        if not mapped_ids:
            return None

        if self.remote_document_type is not None and self.remote_document_type.id in mapped_ids:
            return self.remote_document_type

        if (
            self.remote_document is not None
            and self.remote_document.remote_document_type_id
            and self.remote_document.remote_document_type_id in mapped_ids
        ):
            self.remote_document_type = self.remote_document.remote_document_type
            return self.remote_document_type

        count = len(mapped_ids)

        if count > 1:
            label = describe_document(media=self.media, media_through=self.media_through)
            raise PreFlightCheckError(
                f"{label} has multiple eBay document type mappings. Keep exactly one mapping for this flow."
            )

        self.remote_document_type = mapped_queryset.first()
        return self.remote_document_type

    def _extract_document_status(self, *, payload: Any) -> str | None:
        if isinstance(payload, Mapping):
            status = payload.get("documentStatus") or payload.get("document_status")
            if status:
                return str(status).strip().upper()
            return None

        for attr in ("document_status", "documentStatus"):
            value = getattr(payload, attr, None)
            if value:
                return str(value).strip().upper()

        to_dict = getattr(payload, "to_dict", None)
        if callable(to_dict):
            try:
                return self._extract_document_status(payload=to_dict() or {})
            except Exception:
                return None
        return None

    def _status_retry_sleep_seconds(self, *, retry: int) -> int:
        return (retry + 1) * 5

    def _wait_until_document_is_accepted(self, *, remote_document):
        label = self._get_document_label()
        document_id = str(remote_document.remote_id or "").strip()
        if not document_id:
            raise PreFlightCheckError(f"{label} cannot be status-checked because no eBay document ID exists.")

        for retry in range(self.max_status_retries + 1):
            try:
                response = self.api.commerce_media_get_document(document_id=document_id)
            except (EbayApiError, ApiException) as exc:
                raise PreFlightCheckError(f"{label} status check failed on eBay. Error: {exc}") from exc

            status = self._extract_document_status(payload=response)
            if status and status != remote_document.status:
                remote_document.status = status
                remote_document.save(update_fields=["status"])

            if status == EbayRemoteDocument.STATUS_ACCEPTED:
                return remote_document

            if status in self.FAILED_DOCUMENT_STATUSES:
                raise PreFlightCheckError(
                    f"{label} was rejected by eBay with status '{status}'. Replace the document and retry."
                )

            if status in self.PENDING_DOCUMENT_STATUSES:
                if retry >= self.max_status_retries:
                    raise PreFlightCheckError(
                        f"{label} is still processing on eBay ({status}). Please retry in a few minutes."
                    )
                time.sleep(self._status_retry_sleep_seconds(retry=retry))
                continue

            if retry >= self.max_status_retries:
                raise PreFlightCheckError(f"{label} status could not be confirmed on eBay.")
            time.sleep(self._status_retry_sleep_seconds(retry=retry))

        return remote_document


class EbayRemoteDocumentCreateFactory(EbayRemoteDocumentFactoryBase, RemoteDocumentCreateFactory):
    remote_model_class = EbayRemoteDocument
    remote_document_default_status = EbayRemoteDocument.STATUS_PENDING_UPLOAD

    def __init__(
        self,
        *,
        sales_channel,
        media,
        remote_document=None,
        remote_document_type=None,
        api=None,
        media_through=None,
        remote_product=None,
        view=None,
        get_value_only: bool = False,
        max_status_retries: int = 5,
    ):
        super().__init__(
            sales_channel=sales_channel,
            media=media,
            remote_document=remote_document,
            remote_document_type=remote_document_type,
            api=api,
            media_through=media_through,
            remote_product=remote_product,
            view=view,
            get_value_only=get_value_only,
        )
        self.max_status_retries = max_status_retries
        self._validated_document_url: str | None = None

    def validate_document_before_sync(self):
        if self.get_value_only:
            return
        self._validated_document_url = self._get_validated_document_url()

    def sync_existing_remote_document(self):
        return self.remote_document

    def create_remote_document(self):
        label = self._get_document_label()
        remote_document_type_id = str(self.remote_document_type.remote_id or "").strip()
        if not remote_document_type_id:
            raise PreFlightCheckError(
                f"{label} cannot be pushed because the mapped eBay document type has no remote ID."
            )

        document_url = self._validated_document_url or self._get_validated_document_url()
        payload = {
            "documentType": remote_document_type_id,
            "documentUrl": document_url,
            "languages": self._get_document_languages(),
        }

        try:
            response = self.api.commerce_media_create_document_from_url(
                content_type="application/json",
                body=payload,
            )
        except (EbayApiError, ApiException) as exc:
            raise PreFlightCheckError(f"{label} failed to upload to eBay. Error: {exc}") from exc

        document_id = self._extract_document_id(payload=response)
        if not document_id:
            raise PreFlightCheckError(f"{label} upload did not return a valid eBay document identifier.")

        self.remote_document.remote_id = document_id
        self.remote_document.status = EbayRemoteDocument.STATUS_SUBMITTED
        self.remote_document.save(update_fields=["remote_id", "status"])
        return self.remote_document

    def _extract_document_id(self, *, payload: Any) -> str | None:
        if isinstance(payload, Mapping):
            for key in ("documentId", "document_id", "id"):
                value = payload.get(key)
                if value:
                    return str(value)
            return None

        for attr in ("document_id", "documentId", "id"):
            value = getattr(payload, attr, None)
            if value:
                return str(value)

        to_dict = getattr(payload, "to_dict", None)
        if callable(to_dict):
            try:
                return self._extract_document_id(payload=to_dict() or {})
            except Exception:
                return None
        return None

    def _get_document_languages(self) -> list[str]:
        local_language = (
            str(
                self.media.document_language
                or getattr(self.sales_channel.multi_tenant_company, "language", "")
                or ""
            )
            .strip()
            .lower()
        )
        if not local_language:
            return ["OTHER"]

        remote_language = EBAY_DOCUMENT_LANGUAGE_BY_LOCAL_CODE.get(local_language)
        if remote_language:
            return [remote_language]

        language_root = local_language.split("-")[0]
        remote_language = EBAY_DOCUMENT_LANGUAGE_BY_LOCAL_CODE.get(language_root)
        if remote_language:
            return [remote_language]

        return ["OTHER"]

    def _get_validated_document_url(self) -> str:
        label = self._get_document_label()
        document_url = self.media.get_real_document_file()
        if not document_url:
            raise PreFlightCheckError(
                f"{label} does not have a public URL. Upload the file/image before syncing to eBay."
            )

        source = self.media.image if self.media.is_document_image else self.media.file
        source_name = getattr(source, "name", "") or ""
        extension = os.path.splitext(source_name)[1].lower()
        if extension not in EBAY_DOCUMENT_ALLOWED_EXTENSIONS:
            allowed_extensions = ", ".join(sorted(EBAY_DOCUMENT_ALLOWED_EXTENSIONS))
            raise PreFlightCheckError(
                f"{label} uses unsupported file type '{extension or 'unknown'}'. Allowed types: {allowed_extensions}."
            )

        source_size = getattr(source, "size", None)
        if source_size and source_size > EBAY_DOCUMENT_MAX_FILE_SIZE_BYTES:
            raise PreFlightCheckError(f"{label} exceeds eBay's 10 MB limit. Reduce file size and retry.")

        return document_url


class EbayRemoteDocumentUpdateFactory(EbayRemoteDocumentFactoryBase, RemoteDocumentUpdateFactory):
    remote_model_class = EbayRemoteDocument
    create_factory_class = EbayRemoteDocumentCreateFactory

    def __init__(
        self,
        *,
        sales_channel,
        media,
        remote_document=None,
        remote_document_type=None,
        api=None,
        media_through=None,
        remote_product=None,
        view=None,
        max_status_retries: int = 5,
        get_value_only: bool = False,
    ):
        super().__init__(
            sales_channel=sales_channel,
            media=media,
            remote_document=remote_document,
            remote_document_type=remote_document_type,
            api=api,
            media_through=media_through,
            remote_product=remote_product,
            view=view,
            get_value_only=get_value_only,
        )
        self.max_status_retries = max_status_retries

    def _build_create_factory_kwargs(self):
        kwargs = super()._build_create_factory_kwargs()
        kwargs["max_status_retries"] = self.max_status_retries
        return kwargs

    def should_delegate_to_create(self):
        if self.remote_document is None:
            return True
        remote_id = str(getattr(self.remote_document, "remote_id", "") or "").strip()
        return not remote_id

    def update_remote_document(self):
        self.remote_document_type = self.resolve_remote_document_type()
        if self.remote_document_type is None:
            return None

        status = str(getattr(self.remote_document, "status", "") or "").strip().upper()
        if status in self.PENDING_DOCUMENT_STATUSES:
            self.set_api()
            return self._wait_until_document_is_accepted(remote_document=self.remote_document)

        return self.remote_document


class EbayDocumentThroughProductBase(EbayInventoryItemPushMixin):
    remote_model_class = EbayDocumentThroughProduct
    remote_document_assign_model_class = EbayDocumentThroughProduct
    remote_document_sync_factory = None
    has_remote_document_instance = True
    remote_document_model_class = EbayRemoteDocument
    remote_document_create_factory = EbayRemoteDocumentCreateFactory
    remote_document_update_factory = EbayRemoteDocumentUpdateFactory

    def __init__(self, *args: Any, view, get_value_only: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, view=view, get_value_only=get_value_only, **kwargs)

    def customize_remote_instance_data(self):
        self.remote_instance_data["remote_product"] = self.remote_product
        if getattr(self, "remote_document_instance", None) is not None:
            self.remote_instance_data["remote_document"] = self.remote_document_instance
        self.remote_instance_data["remote_url"] = self._get_local_document_url()
        return self.remote_instance_data

    def _get_local_document_url(self):
        media = getattr(self.local_instance, "media", None)
        if media is None:
            return None
        return media.get_real_document_file()

    def _sync_remote_url_on_remote_instance(self):
        if self.remote_instance is None:
            return

        document_url = self._get_local_document_url()
        if not document_url:
            return
        if self.remote_instance.remote_url == document_url:
            return

        self.remote_instance.remote_url = document_url
        self.remote_instance.save(update_fields=["remote_url"])


class EbayDocumentThroughProductCreateFactory(
    EbayDocumentThroughProductBase,
    RemoteDocumentProductThroughCreateFactory,
):
    def create_remote(self):
        return {"id": getattr(self.remote_instance, "remote_id", None)}


class EbayDocumentThroughProductUpdateFactory(
    EbayDocumentThroughProductBase,
    RemoteDocumentProductThroughUpdateFactory,
):
    create_factory_class = EbayDocumentThroughProductCreateFactory
    remote_document_sync_factory = None

    def update_remote(self):
        return {"id": getattr(self.remote_instance, "remote_id", None)}

    def needs_update(self):
        return True

    def post_update_process(self):
        self._sync_remote_url_on_remote_instance()


class EbayDocumentThroughProductDeleteFactory(
    EbayDocumentThroughProductBase,
    RemoteDocumentProductThroughDeleteFactory,
):
    remote_document_sync_factory = EbayDocumentThroughProductUpdateFactory

    def delete_remote(self):
        return {"status": "DELETED_LOCAL_ASSOC"}

    def run(self):
        super().run()
        if not self.get_value_only:
            self.send_offer()


class EbayRemoteDocumentDeleteFactory(GetEbayAPIMixin, RemoteDocumentDeleteFactory):
    remote_model_class = EbayRemoteDocument
    has_remote_document_instance = True
    delete_document_through_factory = EbayDocumentThroughProductDeleteFactory
    document_remote_through_model_class = EbayDocumentThroughProduct
    remote_product_model_class = EbayProduct
