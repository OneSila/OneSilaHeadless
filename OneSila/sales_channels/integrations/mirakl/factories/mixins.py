from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import requests


logger = logging.getLogger(__name__)


class GetMiraklAPIMixin:
    """Reusable Mirakl API helper methods."""

    default_timeout = 30
    default_page_size = 100

    def get_api(self):
        return self

    def get_mirakl_session(self) -> requests.Session:
        session = getattr(self, "_mirakl_session", None)
        if session is None:
            session = requests.Session()
            self._mirakl_session = session
        return session

    def get_mirakl_base_url(self) -> str:
        base_url = getattr(self.sales_channel, "normalized_base_url", "")
        if not base_url:
            raise ValueError("Mirakl hostname is missing.")
        return base_url

    def get_mirakl_headers(self, *, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        api_key = str(getattr(self.sales_channel, "api_key", "") or "").strip()
        if not api_key:
            raise ValueError("Mirakl API key is missing.")

        headers = {
            "Authorization": api_key,
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def get_mirakl_default_params(self, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        merged = dict(params or {})
        if getattr(self.sales_channel, "shop_id", None) is not None and "shop_id" not in merged:
            merged["shop_id"] = self.sales_channel.shop_id
        return merged

    def _build_mirakl_url(self, *, path: str) -> str:
        cleaned_path = str(path or "").strip()
        if not cleaned_path.startswith("/"):
            cleaned_path = f"/{cleaned_path}"
        return urljoin(f"{self.get_mirakl_base_url()}/", cleaned_path.lstrip("/"))

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: int | None = None,
        extra_headers: dict[str, str] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> requests.Response:
        url = self._build_mirakl_url(path=path)
        request_timeout = timeout if timeout is not None else self.default_timeout
        request_params = self.get_mirakl_default_params(params=params)
        max_attempts = max(1, int(getattr(self.sales_channel, "max_retries", 3) or 3))
        headers = self.get_mirakl_headers(extra_headers=extra_headers)

        if files:
            headers.pop("Content-Type", None)
        else:
            headers.setdefault("Content-Type", "application/json")

        for attempt in range(1, max_attempts + 1):
            response = self.get_mirakl_session().request(
                method=method,
                url=url,
                params=request_params,
                json=None if files else payload,
                data=None if not files else payload,
                files=files,
                headers=headers,
                timeout=request_timeout,
                verify=self.sales_channel.verify_ssl,
            )

            if response.status_code == 429 and attempt < max_attempts:
                retry_after = response.headers.get("Retry-After", "1")
                try:
                    sleep_for = max(0, int(float(retry_after)))
                except (TypeError, ValueError):
                    sleep_for = 1
                logger.warning("Mirakl rate limit hit for %s %s. Retrying in %s seconds.", method, path, sleep_for)
                time.sleep(sleep_for)
                continue

            break

        allowed_statuses = expected_statuses or {200, 201, 202, 204}
        if response.status_code not in allowed_statuses:
            detail = ""
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise ValueError(f"Mirakl request failed with status {response.status_code}: {detail}")

        return response

    def _json(self, *, response: requests.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError as exc:
            raise ValueError("Mirakl response was not valid JSON.") from exc

    def mirakl_get(
        self,
        *,
        path: str,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        response = self._request(method="GET", path=path, params=params, timeout=timeout, expected_statuses={200})
        return self._json(response=response)

    def mirakl_post(
        self,
        *,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        response = self._request(
            method="POST",
            path=path,
            params=params,
            payload=payload,
            timeout=timeout,
            expected_statuses=expected_statuses or {200, 201, 202},
        )
        if response.status_code == 204:
            return {}
        return self._json(response=response)

    def mirakl_put(
        self,
        *,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        response = self._request(
            method="PUT",
            path=path,
            params=params,
            payload=payload,
            timeout=timeout,
            expected_statuses=expected_statuses or {200, 201, 202, 204},
        )
        if response.status_code == 204:
            return {}
        return self._json(response=response)

    def mirakl_post_multipart(
        self,
        *,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: int | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        response = self._request(
            method="POST",
            path=path,
            params=params,
            payload=payload,
            files=files,
            timeout=timeout,
            expected_statuses=expected_statuses or {200, 201, 202},
        )
        return self._json(response=response)

    def mirakl_download(
        self,
        *,
        path: str,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
        expected_statuses: set[int] | None = None,
    ) -> tuple[bytes, requests.Response]:
        response = self._request(
            method="GET",
            path=path,
            params=params,
            timeout=timeout,
            expected_statuses=expected_statuses or {200},
        )
        return response.content, response

    def mirakl_paginated_get(
        self,
        *,
        path: str,
        results_key: str,
        params: dict[str, Any] | None = None,
        page_size: int | None = None,
    ) -> list[dict[str, Any]]:
        effective_page_size = min(100, page_size or self.default_page_size)
        offset = 0
        collected: list[dict[str, Any]] = []

        while True:
            page_params = dict(params or {})
            page_params.update({"max": effective_page_size, "offset": offset})
            payload = self.mirakl_get(path=path, params=page_params)
            records = payload.get(results_key) or []
            if not isinstance(records, list):
                records = []

            collected.extend(record for record in records if isinstance(record, dict))

            total_count = payload.get("total_count")
            if not records:
                break
            if isinstance(total_count, int) and len(collected) >= total_count:
                break
            if len(records) < effective_page_size:
                break
            offset += effective_page_size

        return collected

    def get_account_info(self) -> dict[str, Any]:
        cached = getattr(self, "_mirakl_account_info", None)
        if cached is None:
            cached = self.mirakl_get(path="/api/account")
            self._mirakl_account_info = cached
        return cached

    def get_platform_configuration(self) -> dict[str, Any]:
        cached = getattr(self, "_mirakl_platform_configuration", None)
        if cached is None:
            cached = self.mirakl_get(path="/api/platform/configuration")
            self._mirakl_platform_configuration = cached
        return cached

    def validate_credentials(self) -> dict[str, Any]:
        return self.get_account_info()
