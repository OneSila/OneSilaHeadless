from __future__ import annotations

from typing import Optional

from sales_channels.models.products import RemoteProduct


def shein_document_state_to_status(*, document_state: int | None) -> Optional[str]:
    """Map Shein document state integers to OneSila RemoteProduct status codes.

    Shein states:
    -1: Acceptance failed
     1: Pending review
     2: Approval successful
     3: Approval failed
     4: Withdrawn
     5: Under appeal
    """

    if document_state is None:
        return None

    try:
        state = int(document_state)
    except (TypeError, ValueError):
        return None

    if state in (-1, 3):
        return RemoteProduct.STATUS_APPROVAL_REJECTED
    if state in (1, 5):
        return RemoteProduct.STATUS_PENDING_APPROVAL
    if state == 2:
        return RemoteProduct.STATUS_COMPLETED

    return None


def shein_aggregate_document_states_to_status(*, document_states: list[int | None]) -> Optional[str]:
    """Aggregate multiple SKC document states into a single RemoteProduct status."""

    mapped = [shein_document_state_to_status(document_state=value) for value in document_states]

    if RemoteProduct.STATUS_APPROVAL_REJECTED in mapped:
        return RemoteProduct.STATUS_APPROVAL_REJECTED
    if RemoteProduct.STATUS_PENDING_APPROVAL in mapped:
        return RemoteProduct.STATUS_PENDING_APPROVAL
    if mapped and all(status == RemoteProduct.STATUS_COMPLETED for status in mapped if status is not None):
        return RemoteProduct.STATUS_COMPLETED

    return None
