"""Reusable helpers for interacting with the Shein Open API."""

import base64
import hashlib
import hmac
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

logger = logging.getLogger(__name__)


class SheinSignatureMixin:
    """Provide signature generation utilities for Shein API calls."""

    signature_random_key_length = 5
    signature_random_charset = string.ascii_letters + string.digits

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
            response = requests.post(
                url,
                json=payload or {},
                headers=headers,
                timeout=request_timeout,
                verify=self.sales_channel.verify_ssl,
            )
        except requests.RequestException as exc:  # pragma: no cover - network errors are mocked in tests
            logger.exception("Shein POST request failed for path %s", path)
            raise ValueError(_("Shein request failed: unable to reach remote service.")) from exc

        if raise_for_status:
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:  # pragma: no cover - raised via mocks
                logger.exception("Shein POST request returned HTTP error for path %s", path)
                raise ValueError(_("Shein request returned an HTTP error.")) from exc

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
            response = requests.get(
                url,
                params=payload or {},
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
