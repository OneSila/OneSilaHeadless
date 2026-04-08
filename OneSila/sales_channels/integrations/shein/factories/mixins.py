"""Reusable helpers for interacting with the Shein Open API."""

import base64
import hashlib
import hmac
import io
import logging
import secrets
import string
import time
from typing import Any, Dict, Iterable, Optional, Tuple
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from sales_channels.integrations.shein import constants
from sales_channels.integrations.shein.decorators import retry_shein_request
from sales_channels.integrations.shein.exceptions import SheinResponseException

logger = logging.getLogger(__name__)


class SheinSignatureMixin:
    """Provide signature generation utilities for Shein API calls."""

    signature_random_key_length = 5
    signature_random_charset = string.ascii_letters + string.digits
    product_query_path = "/open-api/openapi-business-backend/product/query"
    product_info_path = "/open-api/goods/spu-info"
    store_info_path = "/open-api/openapi-business-backend/query-store-info"
    certificate_rule_path = "/open-api/goods/get-certificate-rule"
    upload_certificate_file_path = "/open-api/goods/upload-certificate-file"
    certificate_type_list_v2_path = "/open-api/goods/certificate/get-all-certificate-type-list-v2"
    save_or_update_certificate_pool_path = "/open-api/goods/save-or-update-certificate-pool"
    save_certificate_pool_skc_bind_path = "/open-api/goods/save-certificate-pool-skc-bind"
    certificate_rule_default_system_id = "spmp"

    def get_shein_open_key_id(self) -> str:
        open_key_id = self.sales_channel.open_key_id
        if not open_key_id:
            raise ValueError(_("Shein openKeyId is missing. Authorize the integration first."))
        return open_key_id

    def get_shein_secret_key(self) -> str:
        secret_key = self.sales_channel.secret_key
        if not secret_key:
            raise ValueError(_("Shein secret key is missing. Complete the authorization flow."))
        return secret_key

    def generate_shein_signature(
        self,
        *,
        path: str,
        timestamp: Optional[int] = None,
        random_key: Optional[str] = None,
    ) -> Tuple[str, int, str]:
        """Generate the Shein signature for a request path.

        Returns a tuple of ``(signature, timestamp, random_key)``.
        """

        if not path or not path.startswith('/'):
            raise ValueError(_("Shein API path must be provided and start with '/'."))

        open_key_id = self.get_shein_open_key_id()
        secret_key = self.get_shein_secret_key()
        ts = timestamp or int(time.time() * 1000)
        rnd = random_key or self._generate_random_key()

        value = f"{open_key_id}&{ts}&{path}"
        key = f"{secret_key}{rnd}"

        digest = hmac.new(key.encode('utf-8'), value.encode('utf-8'), hashlib.sha256).digest()
        hex_signature = digest.hex()
        base64_signature = base64.b64encode(hex_signature.encode('utf-8')).decode('utf-8')
        final_signature = f"{rnd}{base64_signature}"

        return final_signature, ts, rnd

    def build_shein_headers(
        self,
        *,
        path: str,
        add_language: bool = False,
        timestamp: Optional[int] = None,
        random_key: Optional[str] = None,
        content_type: str = "application/json;charset=UTF-8",
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[Dict[str, str], int, str]:
        """Construct the Shein HTTP headers for a given API path."""

        signature, effective_ts, effective_random = self.generate_shein_signature(
            path=path,
            timestamp=timestamp,
            random_key=random_key,
        )

        headers: Dict[str, str] = {
            "Content-Type": content_type,
            "x-lt-openKeyId": self.get_shein_open_key_id(),
            "x-lt-timestamp": str(effective_ts),
            "x-lt-signature": signature,
        }

        if add_language:
            language_header = self._resolve_shein_language()
            if language_header:
                headers["language"] = language_header

        if extra_headers:
            headers.update(extra_headers)

        return headers, effective_ts, effective_random

    @retry_shein_request()
    def _execute_post_request(
        self,
        *,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int,
        verify: bool,
    ) -> requests.Response:
        return requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
            verify=verify,
        )

    @retry_shein_request()
    def _execute_get_request(
        self,
        *,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int,
        verify: bool,
    ) -> requests.Response:
        return requests.get(
            url,
            params=payload,
            headers=headers,
            timeout=timeout,
            verify=verify,
        )

    def shein_post(
        self,
        *,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        add_language: bool = True,
        timeout: Optional[int] = None,
        raise_for_status: bool = True,
        timestamp: Optional[int] = None,
        random_key: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Execute a POST request against the Shein Open API."""

        headers, _, _ = self.build_shein_headers(
            path=path,
            add_language=add_language,
            timestamp=timestamp,
            random_key=random_key,
            extra_headers=extra_headers,
        )

        url = self._build_shein_url(path=path)
        request_timeout = timeout if timeout is not None else constants.DEFAULT_TIMEOUT

        try:
            response = self._execute_post_request(
                url=url,
                payload=payload or {},
                headers=headers,
                timeout=request_timeout,
                verify=self.sales_channel.verify_ssl,
            )
        except requests.RequestException as exc:  # pragma: no cover - network errors are mocked in tests
            logger.exception("Shein POST request failed for path %s", path)
            raise ValueError("Shein request failed: unable to reach remote service.") from exc

        if raise_for_status:
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:  # pragma: no cover - raised via mocks
                logger.exception("Shein POST request returned HTTP error for path %s", path)
                raise ValueError("Shein request returned an HTTP error.") from exc

        return response

    def shein_get(
        self,
        *,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        add_language: bool = True,
        timeout: Optional[int] = None,
        raise_for_status: bool = True,
        timestamp: Optional[int] = None,
        random_key: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Execute a GET request against the Shein Open API."""

        headers, _, _ = self.build_shein_headers(
            path=path,
            add_language=add_language,
            timestamp=timestamp,
            random_key=random_key,
            extra_headers=extra_headers,
        )

        url = self._build_shein_url(path=path)
        request_timeout = timeout if timeout is not None else constants.DEFAULT_TIMEOUT

        try:
            response = self._execute_get_request(
                url=url,
                payload=payload or {},
                headers=headers,
                timeout=request_timeout,
                verify=self.sales_channel.verify_ssl,
            )
        except requests.RequestException as exc:  # pragma: no cover - network errors are mocked in tests
            logger.exception("Shein GET request failed for path %s", path)
            raise ValueError(_("Shein request failed: unable to reach remote service.")) from exc

        if raise_for_status:
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:  # pragma: no cover - raised via mocks
                logger.exception("Shein GET request returned HTTP error for path %s", path)
                raise ValueError(_("Shein request returned an HTTP error.")) from exc

        return response

    @staticmethod
    def _is_retryable_request_error(*, exc: Exception) -> bool:
        cause = getattr(exc, "__cause__", None)
        return isinstance(
            cause,
            (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
        )

    def get_all_products(
        self,
        page_size: int = 200,
        page_num: int = 1,
        insert_time_start: Optional[str] = None,
        insert_time_end: Optional[str] = None,
        update_time_start: Optional[str] = None,
        update_time_end: Optional[str] = None,
        skip_failed_page: bool = False,
        max_failed_pages: Optional[int] = 3,
        stop_after_page: Optional[int] = None,
    ) -> Iterable[Dict[str, Any]]:
        """Yield product records from the Shein product query endpoint."""

        if not isinstance(page_size, int) or page_size <= 0:
            raise ValueError(_("Shein page size must be a positive integer."))
        if not isinstance(page_num, int) or page_num <= 0:
            raise ValueError(_("Shein page number must be a positive integer."))
        if stop_after_page is not None and (
            not isinstance(stop_after_page, int) or stop_after_page <= 0
        ):
            raise ValueError(_("Shein stop_after_page must be a positive integer."))

        if stop_after_page is not None and page_num > stop_after_page:
            return

        base_payload: Dict[str, Any] = {"pageSize": page_size}
        if insert_time_start:
            base_payload["insertTimeStart"] = insert_time_start
        if insert_time_end:
            base_payload["insertTimeEnd"] = insert_time_end
        if update_time_start:
            base_payload["updateTimeStart"] = update_time_start
        if update_time_end:
            base_payload["updateTimeEnd"] = update_time_end

        current_page = page_num
        consecutive_failures = 0

        while True:
            payload = dict(base_payload, pageNum=current_page)
            try:
                response = self.shein_post(path=self.product_query_path, payload=payload)
            except ValueError as exc:
                if skip_failed_page and self._is_retryable_request_error(exc=exc):
                    consecutive_failures += 1
                    logger.warning(
                        "Skipping Shein product page %s after request error (%s/%s).",
                        current_page,
                        consecutive_failures,
                        max_failed_pages or "unlimited",
                        exc_info=exc,
                    )
                    if max_failed_pages and consecutive_failures >= max_failed_pages:
                        logger.error(
                            "Stopping Shein product pagination after %s consecutive failures.",
                            consecutive_failures,
                        )
                        break
                    current_page += 1
                    continue
                raise
            consecutive_failures = 0

            try:
                body = response.json()
            except ValueError as exc:  # pragma: no cover - defensive guard
                logger.exception("Unable to decode Shein product list response")
                raise ValueError(_("Shein product query returned invalid JSON.")) from exc

            if body.get("code") != "0":
                message = body.get("msg") or "Unknown error"
                raise ValueError(
                    _("Failed to fetch Shein products: %(message)s")
                    % {"message": message}
                )

            info = body.get("info") or {}
            data = info.get("data") or []
            if not isinstance(data, list):  # pragma: no cover - defensive
                data = []

            if not data:
                break

            for record in data:
                if isinstance(record, dict):
                    yield record

            if len(data) < page_size:
                break

            if stop_after_page is not None and current_page >= stop_after_page:
                break

            current_page += 1

    def get_product(
        self,
        *,
        spu_name: str,
        language_list: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Return the product info payload for the provided SPU."""

        if not isinstance(spu_name, str) or not spu_name.strip():
            raise ValueError(_("Shein spuName is required."))

        languages = self._resolve_product_languages(language_list=language_list)
        payload = {
            "languageList": languages,
            "spuName": spu_name.strip(),
        }

        response = self.shein_post(
            path=self.product_info_path,
            payload=payload,
            add_language=False,
        )

        try:
            body = response.json()
        except ValueError as exc:  # pragma: no cover - defensive guard
            logger.exception("Unable to decode Shein product info response")
            raise ValueError(_("Shein product info returned invalid JSON.")) from exc

        code = body.get("code")
        if str(code) != "0":
            message = body.get("msg") or "Unknown error"
            raise SheinResponseException(
                _("Failed to fetch Shein product: %(message)s (code %(code)s)")
                % {"message": message, "code": code}
            )

        info = body.get("info") or {}
        return info if isinstance(info, dict) else {}

    def get_store_info(self) -> Dict[str, Any]:
        """Return the store info payload with quota metadata."""

        response = self.shein_post(
            path=self.store_info_path,
            payload={},
            add_language=False,
        )

        try:
            body = response.json()
        except ValueError as exc:  # pragma: no cover - defensive guard
            logger.exception("Unable to decode Shein store info response")
            raise ValueError(_("Shein store info returned invalid JSON.")) from exc

        if body.get("code") != "0":
            message = body.get("msg") or "Unknown error"
            raise ValueError(
                _("Failed to fetch Shein store info: %(message)s")
                % {"message": message}
            )

        info = body.get("info") or {}
        return info if isinstance(info, dict) else {}

    def get_certificate_rule_by_category_id(
        self,
        *,
        category_id,
        attribute_list: Optional[list[dict[str, Any]]] = None,
        certificate_pool_id_list: Optional[Iterable[int | str]] = None,
        site_arr_list: Optional[Iterable[str]] = None,
        system_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        category_numeric_id = self._safe_int_from_any(value=category_id)
        if category_numeric_id is None:
            raise ValueError(_("Shein categoryId is required and must be numeric."))

        payload: dict[str, Any] = {
            "categoryId": category_numeric_id,
            "systemId": (system_id or self.certificate_rule_default_system_id),
        }
        self._add_optional_certificate_rule_payload_fields(
            payload=payload,
            attribute_list=attribute_list,
            certificate_pool_id_list=certificate_pool_id_list,
            site_arr_list=site_arr_list,
        )

        response = self.shein_post(path=self.certificate_rule_path, payload=payload)
        return self._extract_certificate_rule_records_from_response(response=response)

    def get_certificate_rule_by_product_spu(
        self,
        *,
        spu_name: str,
        attribute_list: Optional[list[dict[str, Any]]] = None,
        certificate_pool_id_list: Optional[Iterable[int | str]] = None,
        site_arr_list: Optional[Iterable[str]] = None,
        system_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        normalized_spu_name = str(spu_name or "").strip()
        if not normalized_spu_name:
            raise ValueError(_("Shein spuName is required."))

        payload: dict[str, Any] = {
            "spuName": normalized_spu_name,
            "systemId": (system_id or self.certificate_rule_default_system_id),
        }
        self._add_optional_certificate_rule_payload_fields(
            payload=payload,
            attribute_list=attribute_list,
            certificate_pool_id_list=certificate_pool_id_list,
            site_arr_list=site_arr_list,
        )

        response = self.shein_post(path=self.certificate_rule_path, payload=payload)
        return self._extract_certificate_rule_records_from_response(response=response)

    def get_all_certificate_type_list_v2(self) -> list[dict[str, Any]]:
        response = self.shein_post(
            path=self.certificate_type_list_v2_path,
            payload={},
            add_language=True,
        )

        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - defensive guard
            logger.exception("Unable to decode Shein certificate type V2 response")
            raise ValueError(_("Shein certificate type V2 returned invalid JSON.")) from exc

        if not isinstance(payload, dict):
            return []

        code = payload.get("code")
        if code is not None and str(code) != "0":
            message = payload.get("msg") or "Unknown error"
            raise SheinResponseException(
                _("Failed to fetch Shein certificate types V2: %(message)s (code %(code)s)")
                % {"message": message, "code": code}
            )

        info = payload.get("info")
        if not isinstance(info, dict):
            return []

        data = info.get("data")
        if isinstance(data, list):
            return [record for record in data if isinstance(record, dict)]

        certificate_type_info_list = info.get("certificateTypeInfoList")
        if isinstance(certificate_type_info_list, list):
            return [record for record in certificate_type_info_list if isinstance(record, dict)]

        return []

    def _extract_certificate_rule_records_from_response(
        self,
        *,
        response: requests.Response,
    ) -> list[dict[str, Any]]:
        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - defensive guard
            logger.exception("Unable to decode Shein certificate rule response")
            raise ValueError(_("Shein certificate rule returned invalid JSON.")) from exc

        if not isinstance(payload, dict):
            return []

        code = payload.get("code")
        if code is not None and str(code) != "0":
            message = payload.get("msg") or "Unknown error"
            raise SheinResponseException(
                _("Failed to fetch Shein certificate rules: %(message)s (code %(code)s)")
                % {"message": message, "code": code}
            )

        info = payload.get("info")
        if not isinstance(info, dict):
            return []

        data = info.get("data")
        if isinstance(data, list):
            return [record for record in data if isinstance(record, dict)]

        if isinstance(data, dict):
            for key in ("records", "list", "data"):
                nested = data.get(key)
                if isinstance(nested, list):
                    return [record for record in nested if isinstance(record, dict)]

        return []

    def _add_optional_certificate_rule_payload_fields(
        self,
        *,
        payload: dict[str, Any],
        attribute_list: Optional[list[dict[str, Any]]],
        certificate_pool_id_list: Optional[Iterable[int | str]],
        site_arr_list: Optional[Iterable[str]],
    ) -> None:
        if isinstance(attribute_list, list):
            normalized_attribute_list = [
                item for item in attribute_list
                if isinstance(item, dict)
            ]
            if normalized_attribute_list:
                payload["attributeList"] = normalized_attribute_list

        if certificate_pool_id_list is not None:
            normalized_certificate_pool_ids: list[int] = []
            for value in certificate_pool_id_list:
                numeric_value = self._safe_int_from_any(value=value)
                if numeric_value is None:
                    continue
                normalized_certificate_pool_ids.append(numeric_value)
            if normalized_certificate_pool_ids:
                payload["certificatePoolId"] = normalized_certificate_pool_ids

        if site_arr_list is not None:
            normalized_site_arr_list = [
                str(site_value).strip()
                for site_value in site_arr_list
                if str(site_value).strip()
            ]
            if normalized_site_arr_list:
                payload["siteArrList"] = normalized_site_arr_list

    @staticmethod
    def _safe_int_from_any(*, value) -> Optional[int]:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError, AttributeError):
            return None

    def get_total_product_count(self) -> Optional[int]:
        """Return the total number of products for the Shein store."""

        info = self.get_store_info()
        quota = info.get("storeProductQuota") or {}
        if not isinstance(quota, dict):
            return None
        used_quota = quota.get("usedQuota")
        if used_quota is None:
            return None
        try:
            total = int(used_quota)
        except (TypeError, ValueError):
            return None

        return max(total, 0)

    def upload_certificate_file(
        self,
        *,
        filename: str,
        file_bytes: bytes,
        content_type: str | None = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        normalized_filename = str(filename or "").strip()
        if not normalized_filename:
            raise ValueError(_("Certificate filename is required for Shein upload."))

        if not isinstance(file_bytes, (bytes, bytearray)) or not file_bytes:
            raise ValueError(_("Certificate file content is empty."))

        headers, _, _ = self.build_shein_headers(
            path=self.upload_certificate_file_path,
            add_language=True,
            content_type="application/json",
        )
        headers.pop("Content-Type", None)

        url = self._build_shein_url(path=self.upload_certificate_file_path)
        request_timeout = timeout if timeout is not None else constants.DEFAULT_TIMEOUT
        file_content_type = str(content_type or "application/octet-stream").strip() or "application/octet-stream"
        files = {
            "file": (
                normalized_filename,
                io.BytesIO(bytes(file_bytes)),
                file_content_type,
            )
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=request_timeout,
                verify=self.sales_channel.verify_ssl,
            )
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network errors are mocked in tests
            logger.exception("Shein certificate upload request failed")
            raise ValueError(_("Shein certificate upload request failed.")) from exc

        return self._extract_successful_shein_json(response=response, context="certificate upload")

    def save_or_update_certificate_pool(
        self,
        *,
        certificate_type_id: int,
        certificate_url: str,
        certificate_url_name: str,
        certificate_pool_id: int | None = None,
        certificate_relation_info_list: Optional[list[dict[str, Any]]] = None,
        other_certificate_relation_info_list: Optional[list[dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "certificateTypeId": int(certificate_type_id),
            "certificateUrl": str(certificate_url or "").strip(),
            "certificateUrlName": str(certificate_url_name or "").strip(),
        }
        if certificate_pool_id is not None:
            payload["certificatePoolId"] = int(certificate_pool_id)
        if certificate_relation_info_list:
            payload["certificateRelationInfoList"] = certificate_relation_info_list
        if other_certificate_relation_info_list:
            payload["otherCertificateRelationInfoList"] = other_certificate_relation_info_list

        response = self.shein_post(
            path=self.save_or_update_certificate_pool_path,
            payload=payload,
            add_language=True,
        )
        return self._extract_successful_shein_json(response=response, context="certificate pool save")

    def save_certificate_pool_skc_bind(
        self,
        *,
        skc_certificate_pool_relation_list: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = {"skcCertificatePoolRelationList": skc_certificate_pool_relation_list}
        response = self.shein_post(
            path=self.save_certificate_pool_skc_bind_path,
            payload=payload,
            add_language=True,
        )
        return self._extract_successful_shein_json(response=response, context="certificate pool bind")

    def _extract_successful_shein_json(
        self,
        *,
        response: requests.Response,
        context: str,
    ) -> Dict[str, Any]:
        try:
            body = response.json()
        except ValueError as exc:  # pragma: no cover - defensive guard
            logger.exception("Unable to decode Shein %s response", context)
            raise ValueError(_("Shein %(context)s returned invalid JSON.") % {"context": context}) from exc

        if not isinstance(body, dict):
            raise ValueError(_("Shein %(context)s returned an invalid payload.") % {"context": context})

        code = body.get("code")
        if code is not None and str(code) != "0":
            message = str(body.get("msg") or "Unknown error").strip()
            raise SheinResponseException(
                _("Shein %(context)s failed: %(message)s (code %(code)s)")
                % {"context": context, "message": message, "code": code}
            )

        return body

    def _resolve_product_languages(
        self,
        *,
        language_list: Optional[Iterable[str]] = None,
    ) -> list[str]:
        languages: list[str] = []

        def add_language(*, language_code: Optional[str]) -> None:
            if not language_code or language_code in languages:
                return
            languages.append(language_code)

        if language_list:
            for candidate in language_list:
                normalized = self._normalize_shein_language_code(language_code=candidate)
                add_language(language_code=normalized)

        from sales_channels.integrations.shein.models import SheinRemoteLanguage

        remote_languages = (
            SheinRemoteLanguage.objects.filter(sales_channel=self.sales_channel)
            .order_by("pk")
        )

        for remote_language in remote_languages:
            normalized = self._normalize_shein_language_code(
                language_code=remote_language.local_instance,
            )
            if not normalized:
                normalized = self._normalize_shein_language_code(
                    language_code=remote_language.remote_code,
                )
            add_language(language_code=normalized)

            if len(languages) >= 5:
                break

        if not languages:
            languages = [constants.DEFAULT_LANGUAGE]

        return languages[:5]

    def _normalize_shein_language_code(
        self,
        *,
        language_code: Optional[str],
    ) -> Optional[str]:
        if not language_code:
            return None

        normalized = language_code.strip().lower()
        if not normalized:
            return None

        mapped = constants.SHEIN_LANGUAGE_HEADER_MAP.get(normalized)
        if mapped:
            return mapped

        if normalized in constants.SHEIN_LANGUAGE_HEADER_MAP.values():
            return normalized

        return None

    def _resolve_shein_language(self) -> str:
        company = getattr(self.sales_channel, "multi_tenant_company", None)
        language_code = getattr(company, "language", None) if company else None
        return constants.map_language_for_header(language_code)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_random_key(self) -> str:
        return ''.join(
            secrets.choice(self.signature_random_charset)
            for _ in range(self.signature_random_key_length)
        )

    def _build_shein_url(self, *, path: str) -> str:
        if not path or not path.startswith('/'):
            raise ValueError(_("Shein API path must be provided and start with '/'."))

        base_url = (
            constants.DEFAULT_TEST_API_BASE_URL
            if settings.DEBUG
            else constants.DEFAULT_PROD_API_BASE_URL
        )
        return f"{base_url.rstrip('/')}{path}"


class SheinSiteListMixin(SheinSignatureMixin):
    """Helper mixin to fetch and normalise Shein marketplace metadata."""

    site_list_path = "/open-api/goods/query-site-list"

    def fetch_site_records(self) -> list[Dict[str, Any]]:
        """Return the list of marketplaces returned by Shein."""

        raw_data = self._call_site_list_api()
        records: list[Dict[str, Any]] = []

        channel_domain = self.get_channel_domain()
        default_assigned = False

        for index, record in enumerate(raw_data):
            main_site = record.get("main_site")
            sub_sites = record.get("sub_site_list") or []
            is_default = False

            for sub_site in sub_sites:
                derived_domain = self.derive_domain_from_site_abbr(sub_site.get("site_abbr"))
                sub_site["derived_domain"] = derived_domain

                if channel_domain and derived_domain:
                    if channel_domain == derived_domain or channel_domain.endswith(f".{derived_domain}"):
                        is_default = True

            if is_default:
                if not default_assigned:
                    default_assigned = True
                else:
                    is_default = False

            records.append(
                {
                    "main_site": main_site,
                    "main_site_name": record.get("main_site_name"),
                    "is_default": is_default if default_assigned else False,
                    "sub_site_list": sub_sites,
                }
            )

        if records and not default_assigned:
            records[0]["is_default"] = True

        return records

    def iterate_sub_sites(self) -> Iterable[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Yield (marketplace_record, sub_site) pairs for each sub-site."""

        for marketplace in self.fetch_site_records():
            for sub_site in marketplace.get("sub_site_list", []):
                yield marketplace, sub_site

    def _call_site_list_api(self) -> list[Dict[str, Any]]:
        response = self.shein_post(path=self.site_list_path)

        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - defensive guard
            logger.exception("Unable to decode Shein site list response")
            raise ValueError(_("Shein site list returned invalid JSON.")) from exc

        if payload.get("code") != "0":
            message = payload.get("msg") or "Unknown error"
            raise ValueError(
                _("Failed to fetch Shein site list: %(message)s")
                % {"message": message}
            )

        info = payload.get("info") or {}
        data = info.get("data") or []
        if not isinstance(data, list):  # pragma: no cover - defensive
            return []

        return data

    @staticmethod
    def derive_domain_from_site_abbr(site_abbr: Optional[str]) -> Optional[str]:
        """Best effort derivation of the domain associated with a sub-site."""

        if not site_abbr:
            return None

        value = site_abbr.strip().lower()
        if not value:
            return None

        if value == "shein":
            return "shein.com"

        if value.startswith("shein-"):
            suffix = value.split("shein-", 1)[1]
            if suffix:
                return f"{suffix}.shein.com"

        return None

    @staticmethod
    def normalise_domain(value: Optional[str]) -> Optional[str]:
        """Normalise a domain or URL to just the lowercase hostname."""

        if not value:
            return None

        candidate = value.strip()
        if not candidate:
            return None

        if "//" not in candidate:
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)
        domain = parsed.netloc or parsed.path
        domain = domain.strip().lower()
        return domain or None

    @classmethod
    def build_view_url(cls, domain: Optional[str]) -> Optional[str]:
        """Return a HTTPS URL for the provided domain, when present."""

        if not domain:
            return None
        return f"https://{domain.strip('/')}"

    def get_channel_domain(self) -> Optional[str]:
        """Return the domain extracted from the connected sales channel hostname."""

        hostname = getattr(self.sales_channel, "hostname", None)
        return self.normalise_domain(hostname)
