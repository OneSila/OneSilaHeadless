"""Tests for eBay pagination helpers."""

from __future__ import annotations

import os

from collections.abc import Iterator
from typing import Any, Callable

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OneSila.settings")
django.setup()

from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin


class _DummyEbayMixin(GetEbayAPIMixin):
    """Lightweight subclass to access pagination helpers."""


def _iterator_fetcher(records: list[dict[str, int]]) -> tuple[Callable[..., Iterator[dict[str, Any]]], list[dict[str, Any]]]:
    """Return a fetcher mimicking ``ebay_rest`` iterator behaviour."""

    calls: list[dict[str, Any]] = []

    def fetcher(**kwargs):
        calls.append(dict(kwargs))
        limit = kwargs.get("limit")

        def iterator() -> Iterator[dict[str, Any]]:
            yielded = 0
            for record in records:
                if limit is not None and limit > 0 and yielded >= limit:
                    break
                yielded += 1
                yield {"record": record}
            yield {
                "total": {
                    "records_available": len(records),
                    "records_yielded": yielded,
                }
            }

        return iterator()

    return fetcher, calls


def test_paginate_api_results_re_requests_without_limit_for_iterators():
    mixin = _DummyEbayMixin()
    records = [{"id": index} for index in range(5)]
    fetcher, calls = _iterator_fetcher(records)

    results = list(
        mixin._paginate_api_results(
            fetcher,
            limit=2,
            record_key="record",
        )
    )

    assert results == records
    assert len(calls) == 2
    assert calls[0]["limit"] == 2
    assert "limit" not in calls[1]


def test_paginate_api_results_iterator_with_default_limit_single_call():
    mixin = _DummyEbayMixin()
    records = [{"id": index} for index in range(3)]
    fetcher, calls = _iterator_fetcher(records)

    results = list(
        mixin._paginate_api_results(
            fetcher,
            limit=None,
            record_key="record",
        )
    )

    assert results == records
    assert len(calls) == 1
    assert "limit" not in calls[0]

