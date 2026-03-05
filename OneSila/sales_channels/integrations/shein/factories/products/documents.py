from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from sales_channels.exceptions import PreFlightCheckError
from sales_channels.factories.products.documents import (
    RemoteDocumentCreateFactory,
    RemoteDocumentDeleteFactory,
    RemoteDocumentProductThroughCreateFactory,
    RemoteDocumentProductThroughDeleteFactory,
    RemoteDocumentProductThroughUpdateFactory,
    RemoteDocumentUpdateFactory,
)
from sales_channels.helpers import describe_document
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import (
    SheinDocument,
    SheinDocumentThroughProduct,
    SheinDocumentType,
    SheinProduct,
)


class SheinRemoteDocumentFactoryBase(SheinSignatureMixin):
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
    MIME_BY_EXTENSION = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }

    def __init__(
        self,
        *args: Any,
        allowed_remote_document_type_ids: set[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self.allowed_remote_document_type_ids = set(
            str(value).strip()
            for value in (allowed_remote_document_type_ids or set())
            if str(value).strip()
        )
        super().__init__(*args, **kwargs)

    def _document_label(self) -> str:
        return describe_document(
            media=self.media,
            media_through=self.media_through,
            remote_document_type=self.remote_document_type,
        )

    def get_api(self):
        return self

    def resolve_remote_document_type(self):
        if not getattr(self.media, "document_type_id", None):
            return None

        mapped_queryset = SheinDocumentType.objects.filter(
            sales_channel=self.sales_channel,
            local_instance_id=self.media.document_type_id,
        ).exclude(remote_id__in=(None, ""))

        if self.allowed_remote_document_type_ids:
            mapped_queryset = mapped_queryset.filter(remote_id__in=self.allowed_remote_document_type_ids)

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

        if len(mapped_ids) > 1:
            raise PreFlightCheckError(
                f"{self._document_label()} has multiple Shein document mappings. Keep exactly one mapping."
            )

        self.remote_document_type = mapped_queryset.first()
        return self.remote_document_type

    def _get_document_source_field(self):
        if getattr(self.media, "is_document_image", False) and getattr(self.media, "image", None):
            return self.media.image
        return getattr(self.media, "file", None)

    def _get_document_source_name(self) -> str:
        source_field = self._get_document_source_field()
        source_name = getattr(source_field, "name", "") if source_field is not None else ""
        return os.path.basename(str(source_name or "").strip())

    def _get_document_extension(self) -> str:
        source_name = self._get_document_source_name()
        return os.path.splitext(source_name)[1].lower()

    def _read_document_bytes(self) -> bytes:
        source_field = self._get_document_source_field()
        if source_field is None:
            return b""
        with source_field.open("rb") as source:
            return source.read()

    def _validate_document_upload_requirements(self) -> tuple[str, bytes, str]:
        source_field = self._get_document_source_field()
        if source_field is None:
            raise PreFlightCheckError(f"{self._document_label()} has no file/image source to upload.")

        filename = self._get_document_source_name()
        extension = self._get_document_extension()
        if extension not in self.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(self.ALLOWED_EXTENSIONS))
            raise PreFlightCheckError(
                f"{self._document_label()} uses unsupported type '{extension or 'unknown'}'. Allowed: {allowed}."
            )

        source_size = getattr(source_field, "size", None)
        if source_size and source_size > self.MAX_FILE_SIZE_BYTES:
            raise PreFlightCheckError(f"{self._document_label()} exceeds Shein's 20MB certificate limit.")

        content = self._read_document_bytes()
        if not content:
            raise PreFlightCheckError(f"{self._document_label()} file content is empty.")
        if len(content) > self.MAX_FILE_SIZE_BYTES:
            raise PreFlightCheckError(f"{self._document_label()} exceeds Shein's 20MB certificate limit.")

        mime_type = self.MIME_BY_EXTENSION.get(extension, "application/octet-stream")
        return filename or f"certificate{extension or '.pdf'}", content, mime_type

    @staticmethod
    def _extract_info_dict(*, payload: Any) -> dict[str, Any]:
        if isinstance(payload, Mapping):
            info = payload.get("info")
            if isinstance(info, Mapping):
                return dict(info)
        return {}

    def _extract_upload_certificate_url(self, *, payload: Any) -> str:
        info = self._extract_info_dict(payload=payload)
        return str(info.get("certificateUrl") or "").strip()

    def _extract_certificate_pool_id(self, *, payload: Any) -> str:
        info = self._extract_info_dict(payload=payload)
        value = info.get("certificatePoolId")
        return str(value).strip() if value not in (None, "") else ""

    def _resolve_remote_document_type_remote_id(self) -> int:
        remote_type_id = str(getattr(self.remote_document_type, "remote_id", "") or "").strip()
        if not remote_type_id:
            raise PreFlightCheckError(f"{self._document_label()} mapped Shein document type has no remote ID.")
        try:
            return int(remote_type_id)
        except (TypeError, ValueError) as exc:
            raise PreFlightCheckError(
                f"{self._document_label()} mapped Shein document type remote ID must be numeric."
            ) from exc

    def _resolve_existing_pool_id(self) -> int | None:
        remote_id = str(getattr(self.remote_document, "remote_id", "") or "").strip()
        if not remote_id:
            return None
        try:
            return int(remote_id)
        except (TypeError, ValueError):
            return None


class SheinRemoteDocumentCreateFactory(SheinRemoteDocumentFactoryBase, RemoteDocumentCreateFactory):
    remote_model_class = SheinDocument

    def create_remote_document(self):
        filename, file_bytes, content_type = self._validate_document_upload_requirements()
        certificate_type_id = self._resolve_remote_document_type_remote_id()

        try:
            upload_payload = self.upload_certificate_file(
                filename=filename,
                file_bytes=file_bytes,
                content_type=content_type,
            )
        except Exception as exc:
            raise PreFlightCheckError(f"{self._document_label()} failed to upload certificate to Shein: {exc}") from exc

        uploaded_certificate_url = self._extract_upload_certificate_url(payload=upload_payload)
        if not uploaded_certificate_url:
            raise PreFlightCheckError(f"{self._document_label()} upload did not return a Shein certificate URL.")

        certificate_pool_payload = {
            "certificateTypeId": certificate_type_id,
            "certificateUrl": uploaded_certificate_url,
            "certificateUrlName": filename,
            "certificatePoolId": self._resolve_existing_pool_id(),
        }
        # TODO: If expiration validation becomes an issue, send certificateRelationInfoList for expiry.
        # Example: [{"certificateRelationNameId": 178, "certificateRelationValue": "1970-01-01 00:00:00"}]
        # Shein docs note that 1970-01-01 00:00:00 means "never expires".
        # where 178 is documented as "Certificate Expiration Date" for some Shein certificate presets.
        try:
            pool_payload = self.save_or_update_certificate_pool(
                certificate_type_id=certificate_type_id,
                certificate_url=uploaded_certificate_url,
                certificate_url_name=filename,
                certificate_pool_id=certificate_pool_payload.get("certificatePoolId"),
            )
        except Exception as exc:
            raise PreFlightCheckError(f"{self._document_label()} failed to create/update Shein certificate pool: {exc}") from exc

        certificate_pool_id = self._extract_certificate_pool_id(payload=pool_payload)
        if not certificate_pool_id:
            raise PreFlightCheckError(f"{self._document_label()} pool creation did not return a certificatePoolId.")

        update_fields: list[str] = []
        if self.remote_document.remote_id != certificate_pool_id:
            self.remote_document.remote_id = certificate_pool_id
            update_fields.append("remote_id")
        if self.remote_document.remote_url != uploaded_certificate_url:
            self.remote_document.remote_url = uploaded_certificate_url
            update_fields.append("remote_url")
        if self.remote_document.remote_filename != filename:
            self.remote_document.remote_filename = filename
            update_fields.append("remote_filename")

        if update_fields:
            self.remote_document.save(update_fields=update_fields)

        return self.remote_document


class SheinRemoteDocumentUpdateFactory(SheinRemoteDocumentFactoryBase, RemoteDocumentUpdateFactory):
    remote_model_class = SheinDocument
    create_factory_class = SheinRemoteDocumentCreateFactory

    def _build_create_factory_kwargs(self):
        kwargs = super()._build_create_factory_kwargs()
        kwargs["allowed_remote_document_type_ids"] = self.allowed_remote_document_type_ids
        return kwargs

    def should_delegate_to_create(self):
        if self.remote_document is None:
            return True
        remote_id = str(getattr(self.remote_document, "remote_id", "") or "").strip()
        remote_url = str(getattr(self.remote_document, "remote_url", "") or "").strip()
        return not remote_id or not remote_url

    def update_remote_document(self):
        self.remote_document_type = self.resolve_remote_document_type()
        if self.remote_document_type is None:
            return None
        return self.remote_document


class SheinDocumentThroughProductBase(SheinSignatureMixin):
    remote_model_class = SheinDocumentThroughProduct
    remote_document_assign_model_class = SheinDocumentThroughProduct
    has_remote_document_instance = True
    remote_document_model_class = SheinDocument
    remote_document_create_factory = SheinRemoteDocumentCreateFactory
    remote_document_update_factory = SheinRemoteDocumentUpdateFactory

    def __init__(
        self,
        *args: Any,
        allowed_remote_document_type_ids: set[str] | None = None,
        get_value_only: bool = False,
        **kwargs: Any,
    ) -> None:
        self.allowed_remote_document_type_ids = set(
            str(value).strip()
            for value in (allowed_remote_document_type_ids or set())
            if str(value).strip()
        )
        self.get_value_only = get_value_only
        self.value: dict[str, Any] | None = None
        super().__init__(*args, **kwargs)

    def get_api(self):
        return self

    def serialize_response(self, response):
        if response is None:
            return {}
        if isinstance(response, dict):
            return response
        response_json = getattr(response, "json", None)
        if callable(response_json):
            try:
                return response_json() or {}
            except Exception:
                return {}
        return {}

    def _document_label(self) -> str:
        media_through = getattr(self, "local_instance", None)
        media = getattr(media_through, "media", None)
        remote_document_type = (
            getattr(getattr(self, "remote_document_instance", None), "remote_document_type", None)
            if getattr(self, "remote_document_instance", None) is not None
            else None
        )
        return describe_document(
            media=media,
            media_through=media_through,
            remote_document_type=remote_document_type,
        )

    def _build_skc_certificate_pool_relation_payload(self) -> list[dict[str, Any]]:
        remote_product = getattr(self, "remote_product", None)
        if remote_product is None:
            raise PreFlightCheckError("Remote product is required for Shein certificate binding.")

        remote_document = getattr(self, "remote_document_instance", None)
        if remote_document is None:
            raise PreFlightCheckError(f"{self._document_label()} has no synced Shein certificate pool.")

        pool_id_raw = str(getattr(remote_document, "remote_id", "") or "").strip()
        if not pool_id_raw:
            raise PreFlightCheckError(f"{self._document_label()} has no Shein certificate pool ID to bind.")
        try:
            pool_id = int(pool_id_raw)
        except (TypeError, ValueError) as exc:
            raise PreFlightCheckError(f"{self._document_label()} certificate pool ID must be numeric.") from exc

        spu_name = str(
            getattr(remote_product, "spu_name", None)
            or getattr(getattr(remote_product, "remote_parent_product", None), "spu_name", None)
            or getattr(remote_product, "remote_id", None)
            or ""
        ).strip()
        if not spu_name:
            raise PreFlightCheckError("Cannot bind Shein certificate pool without an SPU name.")

        skc_name = str(getattr(remote_product, "skc_name", None) or "").strip()
        if not skc_name and hasattr(remote_product, "url_skc_name"):
            skc_name = str(getattr(remote_product, "url_skc_name", None) or "").strip()
        if not skc_name:
            raise PreFlightCheckError("Cannot bind Shein certificate pool without an SKC name.")

        return [
            {
                "spuName": spu_name,
                "skcName": skc_name,
                "certificatePoolIdList": [pool_id],
            }
        ]

    def _sync_remote_instance_after_bind(self):
        if self.remote_instance is None:
            return

        update_fields: list[str] = []
        remote_document = getattr(self, "remote_document_instance", None)
        remote_url = str(getattr(remote_document, "remote_url", "") or "").strip() if remote_document else ""
        if remote_url and self.remote_instance.remote_url != remote_url:
            self.remote_instance.remote_url = remote_url
            update_fields.append("remote_url")

        if self.remote_instance.missing_status != SheinDocumentThroughProduct.STATUS_PENDING:
            self.remote_instance.missing_status = SheinDocumentThroughProduct.STATUS_PENDING
            update_fields.append("missing_status")

        if update_fields and self.remote_instance.pk:
            self.remote_instance.save(update_fields=update_fields)

    def _bind_certificate_pool(self):
        payload = self._build_skc_certificate_pool_relation_payload()
        self.value = {"skcCertificatePoolRelationList": payload}
        if self.get_value_only:
            return self.value

        try:
            self.save_certificate_pool_skc_bind(
                skc_certificate_pool_relation_list=payload,
            )
        except Exception as exc:
            raise PreFlightCheckError(f"{self._document_label()} failed to bind Shein certificate pool: {exc}") from exc

        self._sync_remote_instance_after_bind()
        return {"status": "BOUND"}

    def _create_remote_document(self, *, remote_document_instance=None):
        if not self.remote_document_create_factory:
            raise ValueError(
                f"{self.__class__.__name__} requires remote_document_create_factory when has_remote_document_instance=True."
            )

        factory = self.remote_document_create_factory(
            sales_channel=self.sales_channel,
            media=self.local_instance.media,
            remote_document=remote_document_instance,
            api=self.api,
            media_through=self.local_instance,
            remote_product=self.remote_product,
            allowed_remote_document_type_ids=self.allowed_remote_document_type_ids,
            get_value_only=self.get_value_only,
        )
        remote_document = factory.run()
        self.api = factory.api
        return remote_document

    def _update_remote_document(self, *, remote_document_instance):
        if not self.remote_document_update_factory:
            return remote_document_instance

        factory = self.remote_document_update_factory(
            sales_channel=self.sales_channel,
            media=self.local_instance.media,
            remote_document=remote_document_instance,
            api=self.api,
            media_through=self.local_instance,
            remote_product=self.remote_product,
            allowed_remote_document_type_ids=self.allowed_remote_document_type_ids,
            get_value_only=self.get_value_only,
        )
        remote_document = factory.run()
        self.api = factory.api
        return remote_document

    def customize_remote_instance_data(self):
        self.remote_instance_data["remote_product"] = self.remote_product
        if getattr(self, "remote_document_instance", None) is not None:
            self.remote_instance_data["remote_document"] = self.remote_document_instance
        self.remote_instance_data["require_document"] = True
        return self.remote_instance_data


class SheinDocumentThroughProductCreateFactory(
    SheinDocumentThroughProductBase,
    RemoteDocumentProductThroughCreateFactory,
):
    def create_remote(self):
        return self._bind_certificate_pool()


class SheinDocumentThroughProductUpdateFactory(
    SheinDocumentThroughProductBase,
    RemoteDocumentProductThroughUpdateFactory,
):
    create_factory_class = SheinDocumentThroughProductCreateFactory

    def update_remote(self):
        if (
            self.remote_instance is not None
            and self.remote_instance.missing_status in {
                SheinDocumentThroughProduct.STATUS_PENDING,
                SheinDocumentThroughProduct.STATUS_ACCEPTED,
            }
        ):
            return {"status": "ALREADY_BOUND"}
        return self._bind_certificate_pool()

    def needs_update(self):
        return True


class SheinDocumentThroughProductDeleteFactory(
    SheinDocumentThroughProductBase,
    RemoteDocumentProductThroughDeleteFactory,
):
    delete_remote_instance = True

    def delete_remote(self):
        return {"status": "DELETED_LOCAL_ASSOC"}


class SheinRemoteDocumentDeleteFactory(SheinSignatureMixin, RemoteDocumentDeleteFactory):
    remote_model_class = SheinDocument
    has_remote_document_instance = True
    delete_document_through_factory = SheinDocumentThroughProductDeleteFactory
    document_remote_through_model_class = SheinDocumentThroughProduct
    remote_product_model_class = SheinProduct
