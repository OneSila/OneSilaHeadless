"""Utility mixins for eBay API access."""

from __future__ import annotations

from ast import literal_eval
from collections.abc import Iterable, Iterator, Mapping
from typing import Any

import requests
from django.conf import settings

import json

from ebay_rest import API
from ebay_rest.api import commerce_identity
from ebay_rest.reference import Reference
from ebay_rest.api.sell_marketing.api_client import ApiClient
from ebay_rest.api.sell_marketing.configuration import Configuration

from ebay_rest.api.commerce_identity.api.user_api import UserApi

from sales_channels.integrations.ebay.models import EbaySalesChannel, EbaySalesChannelView


class GetEbayAPIMixin:

    def get_api(self) -> API:
        """Returns a fully authenticated API instance."""
        credentials = {
            "app_id": settings.EBAY_CLIENT_ID,
            "cert_id": settings.EBAY_CLIENT_SECRET,
            "dev_id": settings.EBAY_DEV_ID,
            "redirect_uri": settings.EBAY_RU_NAME,
        }

        user_info = {
            "refresh_token": self.sales_channel.refresh_token,
            "refresh_token_expiry": self.sales_channel.refresh_token_expiration.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "email_or_username": "OneSila",
            "password": "???"  # For some reason username and password are validating even if we provide the
            # refresh_token and we can add anything here
        }

        header = {
            "marketplace_id": "EBAY_US",
            "accept_language": "en-US",
            "content_language": "en-US",
        }

        view = getattr(self, "view", None)

        if isinstance(view, EbaySalesChannelView):
            selected_view = view
        else:
            selected_view = None
            if view is not None:
                real_instance_getter = getattr(view, "get_real_instance", None)
                if callable(real_instance_getter):
                    candidate = real_instance_getter()
                    if isinstance(candidate, EbaySalesChannelView):
                        selected_view = candidate
                if selected_view is None:
                    selected_view = EbaySalesChannelView.objects.filter(pk=getattr(view, "pk", None)).first()
            if selected_view is None:
                selected_view = EbaySalesChannelView.objects.filter(
                    sales_channel=self.sales_channel,
                    is_default=True,
                ).first()

        if selected_view is not None:
            if selected_view.remote_id:
                header["marketplace_id"] = selected_view.remote_id

            remote_language = selected_view.remote_languages.first()
            if remote_language and remote_language.remote_code:
                language_code = remote_language.remote_code.replace("_", "-")
                header["accept_language"] = language_code
                header["content_language"] = language_code

        # Construct API with dicts (no need for .json file)
        return API(
            application=credentials,
            user=user_info,
            header=header
        )

    def get_api_client(self) -> ApiClient:
        config = Configuration()
        access_token = self.api._user_token.get()

        config.access_token = access_token
        if getattr(self.sales_channel, "environment", None) == getattr(self.sales_channel.__class__, "SANDBOX", "sandbox"):
            config.host = "https://api.sandbox.ebay.com"
        else:
            config.host = "https://api.ebay.com"

        return ApiClient(configuration=config)

    def get_marketplace_currencies(self, marketplace_id: str) -> str | None:
        resp = self.api.sell_metadata_get_currencies(marketplace_id=marketplace_id)
        return resp

    def marketplace_reference(self) -> dict:
        """Return eBay marketplace reference information."""
        return Reference.get_marketplace_id_values()

    def get_marketplace_ids(self) -> list[str]:
        """Return all available marketplace IDs."""
        reference = self.marketplace_reference()
        return list(reference.keys())

    def get_default_marketplace_id(self) -> str | None:
        resp = self.api.commerce_identity_get_user()
        return resp.get("registration_marketplace_id", None)

    def _get_account_api_base_url(self) -> str:
        if  self.sales_channel.environment == EbaySalesChannel.SANDBOX:
            return "https://api.sandbox.ebay.com/sell/account/v1"

        return "https://api.ebay.com/sell/account/v1"

    def _get_account_headers(self) -> dict[str, str]:
        api = getattr(self, "api", None)
        if api is None:
            api = self.get_api()
            self.api = api
        access_token = api._user_token.get()
        if not access_token:
            raise ValueError("Unable to retrieve eBay access token.")
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    def _request_account_policy(self, endpoint: str, view_remote_id: str) -> dict:
        url = f"{self._get_account_api_base_url()}/{endpoint}"
        headers = self._get_account_headers()

        response = requests.get(url, headers=headers, params={"marketplace_id": view_remote_id})
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {}

    def get_fulfillment_policies(self) -> dict:
        return self._request_account_policy("fulfillment_policy", self.view.remote_id)

    def get_payment_policies(self) -> dict:
        return self._request_account_policy("payment_policy", self.view.remote_id)

    def get_return_policies(self) -> dict:
        return self._request_account_policy("return_policy", self.view.remote_id)

    def get_subscription_marketplace_ids(self) -> list[str] | None:
        url = f"{self._get_account_api_base_url()}/subscription"
        headers = self._get_account_headers()

        try:
            response = requests.get(url, headers=headers)
            if not response.ok:
                return None
            data = response.json()
        except Exception:
            return None

        marketplace_used_ids = set()

        for sub in data.get("subscriptions", []):
            marketplace_id = sub.get("marketplaceId")
            if marketplace_id:
                marketplace_used_ids.add(marketplace_id)

        return list(marketplace_used_ids)

    def _extract_paginated_records(
        self,
        response: Any,
        *,
        record_key: str,
        records_key: str | None = None,
    ) -> tuple[list[Any], int | None, int | None]:
        """Normalize paginated eBay responses into records and pagination info."""

        def _as_int(value: Any) -> int | None:
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    return None
            return None

        records: list[Any] = []
        total_available: int | None = None
        records_yielded: int | None = None

        if response is None:
            return records, total_available, records_yielded

        if isinstance(response, Iterable) and not isinstance(response, (dict, str, bytes)):
            for item in response:
                if not isinstance(item, dict):
                    continue
                if record_key in item:
                    value = item[record_key]
                    if isinstance(value, list):
                        records.extend(value)
                    elif value is not None:
                        records.append(value)
                total_data = item.get("total")
                if isinstance(total_data, dict):
                    available = _as_int(total_data.get("records_available"))
                    if available is not None:
                        total_available = available
                    yielded = _as_int(total_data.get("records_yielded"))
                    if yielded is not None:
                        records_yielded = yielded
            if records_yielded is None:
                records_yielded = len(records)
            return records, total_available, records_yielded

        if isinstance(response, dict):
            container: Any = None
            if records_key and records_key in response:
                container = response.get(records_key)
            elif record_key in response:
                container = response.get(record_key)
            else:
                for key in (
                    records_key,
                    record_key,
                    "records",
                    "inventory_items",
                    "inventoryItems",
                    "offers",
                    "items",
                    "data",
                ):
                    if key and key in response:
                        container = response.get(key)
                        break

            if isinstance(container, list):
                records.extend(container)
            elif container is not None:
                records.append(container)

            total_section = response.get("total") or response.get("pagination") or response.get("page")
            if isinstance(total_section, dict):
                available = (
                    _as_int(total_section.get("records_available"))
                    or _as_int(total_section.get("total_entries"))
                    or _as_int(total_section.get("total"))
                    or _as_int(total_section.get("total_count"))
                    or _as_int(total_section.get("matched_records"))
                )
                if available is not None:
                    total_available = available
                yielded = (
                    _as_int(total_section.get("records_yielded"))
                    or _as_int(total_section.get("returned_entries"))
                    or _as_int(total_section.get("returned"))
                    or _as_int(total_section.get("size"))
                    or _as_int(total_section.get("returned_count"))
                )
                if yielded is not None:
                    records_yielded = yielded

            if records_yielded is None:
                records_yielded = len(records)

            return records, total_available, records_yielded

        return records, total_available, records_yielded

    def _paginate_api_results(
        self,
        fetcher,
        *,
        limit: int | None,
        record_key: str,
        records_key: str | None = None,
        **kwargs,
    ) -> Iterator[Any]:
        """Yield records from paginated eBay endpoints."""

        offset = kwargs.pop("offset", 0) or 0

        while True:
            request_kwargs = dict(kwargs)
            if limit is not None and limit > 0:
                request_kwargs["limit"] = limit
            if offset:
                request_kwargs["offset"] = offset

            response = fetcher(**request_kwargs)

            is_iterator_response = isinstance(response, Iterator)
            response_items = response if is_iterator_response else (response,)

            if is_iterator_response:
                # ebay-rest methods that return iterators perform pagination
                # internally and treat the ``limit`` parameter as the maximum
                # number of records to yield overall. Re-fetch without the
                # explicit limit so that we always process the complete result
                # set and rely on the iterator to manage pagination.
                if limit is not None and limit > 0 and "limit" in request_kwargs:
                    response = fetcher(**dict(kwargs))
                    response_items = response
                else:
                    response_items = response

            yielded_any = False

            for item in response_items:
                records, total_available, records_yielded = self._extract_paginated_records(
                    item,
                    record_key=record_key,
                    records_key=records_key,
                )

                if not records:
                    continue

                yielded_any = True

                for record in records:
                    yield record

                increment = records_yielded if records_yielded is not None else len(records)
                if increment <= 0:
                    if not is_iterator_response:
                        return
                    continue

                if not is_iterator_response:
                    offset += increment
                    if total_available is not None and offset >= total_available:
                        return

            if is_iterator_response:
                break

            if not yielded_any:
                break

    def get_all_products(self, limit: int | None = None) -> Iterator[dict[str, Any]]:
        """Yield all inventory items for the configured sales channel."""

        yield from self._paginate_api_results(
            self.api.sell_inventory_get_inventory_items,
            limit=limit,
            record_key="record",
            records_key="inventory_items",
        )

    def get_category_aspects_map(
        self,
        *,
        products_limit: int | None = None,
        offers_limit: int | None = None,
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Return category and aspect information grouped by marketplace."""

        category_map: dict[str, dict[str, dict[str, Any]]] = {}

        for product in self.get_all_products(limit=products_limit):
            if not isinstance(product, dict):
                continue

            sku = product.get("sku") or product.get("inventory_item_sku")
            if not sku:
                continue

            product_aspects = self._extract_product_aspects(product=product)

            for offer in self._paginate_api_results(
                self.api.sell_inventory_get_offers,
                limit=offers_limit,
                record_key="record",
                records_key="offers",
                sku=sku,
            ):
                if not isinstance(offer, dict):
                    continue

                marketplace_id = offer.get("marketplace_id")
                if not marketplace_id:
                    continue

                category_id = offer.get("category_id")
                if not category_id:
                    continue

                marketplace_key = str(marketplace_id)
                marketplace_categories = category_map.setdefault(marketplace_key, {})

                category_key = str(category_id)
                category_details = marketplace_categories.setdefault(
                    category_key,
                    {"category_id": category_key, "aspects": {}},
                )

                aspects_map = category_details.setdefault("aspects", {})

                if not product_aspects:
                    continue

                for aspect_name, aspect_values in product_aspects.items():
                    value_set = aspects_map.setdefault(aspect_name, set())
                    value_set.update(aspect_values)

        return category_map

    def _extract_product_aspects(
        self,
        *,
        product: dict[str, Any],
    ) -> dict[str, set[str]]:
        """Return normalized aspect data from a product payload."""

        product_data = product.get("product")
        if isinstance(product_data, dict):
            aspects_raw = product_data.get("aspects")
        else:
            aspects_raw = None

        if isinstance(aspects_raw, Mapping):
            aspects_source = aspects_raw
        elif isinstance(aspects_raw, str):
            try:
                parsed = literal_eval(aspects_raw)
            except (SyntaxError, ValueError):
                return {}
            if not isinstance(parsed, Mapping):
                return {}
            aspects_source = parsed
        else:
            return {}

        normalized: dict[str, set[str]] = {}
        for aspect_name, values in aspects_source.items():
            if not aspect_name:
                continue

            if isinstance(values, str):
                source_values: Iterable[Any] = [values]
            elif isinstance(values, Iterable) and not isinstance(values, (str, bytes, bytearray)):
                source_values = values
            else:
                continue

            normalized_values = {str(value) for value in source_values if value is not None}
            if not normalized_values:
                continue

            key = str(aspect_name)
            if key in normalized:
                normalized[key].update(normalized_values)
            else:
                normalized[key] = normalized_values

        return normalized


