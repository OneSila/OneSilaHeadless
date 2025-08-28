import json
import time
import traceback
from typing import Any, Dict, Optional

import requests
from django.apps import apps
from django.db import transaction
from django.forms.models import model_to_dict
from django.utils import timezone

from webhooks.models import WebhookDelivery, WebhookDeliveryAttempt
from webhooks.utils import signing
from webhooks.utils.envelope import build_envelope


class SendWebhookDeliveryFactory:
    def __init__(
        self,
        *,
        outbox_id: int,
        delivery_id: int,
        dirty_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.outbox_id = outbox_id
        self.delivery_id = delivery_id
        self.dirty_fields = dirty_fields or {}

    def run(self) -> None:
        with transaction.atomic():
            self._get_delivery()
            self._build_payload()
            self._build_body_and_headers()
            self._send_request()
            self._record_attempt()
            self._update_delivery()

    # Internal helpers
    def _get_delivery(self) -> None:
        self.delivery = WebhookDelivery.objects.select_related(
            "outbox", "webhook_integration"
        ).get(id=self.delivery_id)
        self.outbox = self.delivery.outbox
        self.integration = self.delivery.webhook_integration

    def _build_payload(self) -> None:
        if self.outbox.payload:
            self.payload = self.outbox.payload
            return
        try:
            model = apps.get_model(self.outbox.subject_type)
            instance = model.objects.filter(pk=self.outbox.subject_id).first()
            if instance is not None:
                self.payload = model_to_dict(instance)
            else:
                self.payload = {}
        except Exception:  # noqa: BLE001
            self.payload = {}
        self.outbox.payload = self.payload
        self.outbox.save(update_fields=["payload"])

    def _build_body_and_headers(self) -> None:
        envelope = build_envelope(
            self.integration,
            self.outbox,
            self.outbox.action,
            self.payload,
            self.dirty_fields,
        )
        self.body = json.dumps(envelope)
        self.raw_body = self.body.encode()
        timestamp = int(time.time())
        self.headers = signing.build_headers(
            self.integration.user_agent,
            self.outbox.topic,
            self.outbox.action,
            self.integration.version,
            str(self.delivery.webhook_id),
            self.integration.secret,
            timestamp,
            self.raw_body,
        )
        self.headers.update(self.integration.extra_headers or {})

    def _send_request(self) -> None:
        timeout = self.integration.timeout_ms / 1000
        self.sent_at = timezone.now()
        start = time.perf_counter()
        self.response_code: int | None = None
        self.response_body: str | None = None
        self.error_text: str | None = None
        self.error_tb: str | None = None
        try:
            resp = requests.post(
                self.integration.url,
                data=self.raw_body,
                headers=self.headers,
                timeout=timeout,
                verify=self.integration.verify_ssl,
            )
            self.response_code = resp.status_code
            self.response_body = resp.text
        except Exception as exc:  # noqa: BLE001
            self.error_text = str(exc)
            self.error_tb = traceback.format_exc()
        self.response_ms = int((time.perf_counter() - start) * 1000)

    def _record_attempt(self) -> None:
        self.attempt_number = self.delivery.attempt + 1
        WebhookDeliveryAttempt.objects.create(
            delivery=self.delivery,
            number=self.attempt_number,
            sent_at=self.sent_at,
            response_code=self.response_code,
            response_ms=self.response_ms,
            response_body_snippet=self.response_body,
            error_text=self.error_text,
            error_traceback=self.error_tb,
        )

    def _update_delivery(self) -> None:
        success = self.response_code is not None and 200 <= self.response_code < 300
        self.delivery.attempt = self.attempt_number
        self.delivery.sent_at = self.sent_at
        self.delivery.response_code = self.response_code
        self.delivery.response_ms = self.response_ms
        self.delivery.response_body_snippet = self.response_body
        self.delivery.error_message = self.error_text
        self.delivery.error_traceback = self.error_tb
        self.delivery.status = (
            WebhookDelivery.DELIVERED
            if success
            else (
                WebhookDelivery.PENDING
                if self.attempt_number < self.integration.max_retries
                else WebhookDelivery.FAILED
            )
        )
        self.delivery.save()
        if not success:
            raise Exception(self.error_text or f"HTTP {self.response_code}")
