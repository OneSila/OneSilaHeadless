"""Placeholder factories for Shein marketplace synchronisation."""

from __future__ import annotations

from typing import Any


class SheinMarketplacePullFactory:
    """Temporary stub until marketplace sync is implemented."""

    def __init__(self, *, sales_channel: Any) -> None:
        self.sales_channel = sales_channel

    def run(self, *_, **__) -> None:
        """No-op placeholder."""

        return None
