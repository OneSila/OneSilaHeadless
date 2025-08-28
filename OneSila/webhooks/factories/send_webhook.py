import json
import time
import traceback

import requests
from django.db import transaction
from django.utils import timezone

from webhooks.models import (
    WebhookDelivery,
    WebhookDeliveryAttempt,
    WebhookOutbox,
    WebhookIntegration,
)
from webhooks.utils import signing
from webhooks.utils.envelope import build_envelope


class SendWebhookDeliveryFactory:
    def __init__(self, outbox_id: int, delivery_id: int) -> None:
        self.outbox_id = outbox_id
        self.delivery_id = delivery_id

    def run(self) -> None:
        with transaction.atomic():
            delivery = WebhookDelivery.objects.select_related(
                "outbox", "webhook_integration"
            ).get(id=self.delivery_id)
            outbox: WebhookOutbox = delivery.outbox
            integration: WebhookIntegration = delivery.webhook_integration

            envelope = build_envelope(
                integration, outbox, outbox.action, outbox.payload
            )
            body = json.dumps(envelope)
            raw_body = body.encode()
            timestamp = int(time.time())
            headers = signing.build_headers(
                integration.user_agent,
                outbox.topic,
                outbox.action,
                integration.version,
                str(delivery.webhook_id),
                integration.secret,
                timestamp,
                raw_body,
            )
            headers.update(integration.extra_headers or {})

            timeout = integration.timeout_ms / 1000
            sent_at = timezone.now()
            start = time.perf_counter()
            response_code: int | None = None
            response_body: str | None = None
            error_text: str | None = None
            error_tb: str | None = None

            try:
                resp = requests.post(
                    integration.url,
                    data=raw_body,
                    headers=headers,
                    timeout=timeout,
                    verify=integration.verify_ssl,
                )
                response_code = resp.status_code
                response_body = resp.text
            except Exception as exc:  # noqa: BLE001
                error_text = str(exc)
                error_tb = traceback.format_exc()
            response_ms = int((time.perf_counter() - start) * 1000)

            attempt_number = delivery.attempt + 1
            WebhookDeliveryAttempt.objects.create(
                delivery=delivery,
                number=attempt_number,
                sent_at=sent_at,
                response_code=response_code,
                response_ms=response_ms,
                response_body_snippet=response_body,
                error_text=error_text,
                error_traceback=error_tb,
            )

            success = response_code is not None and 200 <= response_code < 300
            delivery.attempt = attempt_number
            delivery.sent_at = sent_at
            delivery.response_code = response_code
            delivery.response_ms = response_ms
            delivery.response_body_snippet = response_body
            delivery.error_message = error_text
            delivery.error_traceback = error_tb
            delivery.status = (
                WebhookDelivery.DELIVERED
                if success
                else (
                    WebhookDelivery.PENDING
                    if attempt_number < integration.max_retries
                    else WebhookDelivery.FAILED
                )
            )
            delivery.save()

            if not success:
                raise Exception(error_text or f"HTTP {response_code}")