import base64
import hashlib
import hmac
import json
import logging

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from django.conf import settings
from django.http import HttpResponse, JsonResponse, QueryDict
from django.http.multipartparser import MultiPartParser, MultiPartParserError
from django.views.decorators.csrf import csrf_exempt

from sales_channels.integrations.shein.models import SheinSalesChannel, SheinProduct
from sales_channels.integrations.shein.models import SheinProductIssue
from sales_channels.integrations.shein import constants
from integrations.models import IntegrationLog


logger = logging.getLogger(__name__)


def _normalize_header(request, name: str) -> str | None:
    value = request.headers.get(name)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _verify_shein_webhook_signature(*, sales_channel: SheinSalesChannel, request) -> bool:
    signature = _normalize_header(request, "x-lt-signature")
    timestamp = _normalize_header(request, "x-lt-timestamp")
    open_key_id = _normalize_header(request, "x-lt-openKeyId")
    app_id = _normalize_header(request, "x-lt-appid")
    if not signature or not timestamp or not open_key_id or not app_id:
        return False

    if open_key_id != (sales_channel.open_key_id or ""):
        return False

    expected_app_id = settings.SHEIN_APP_ID
    if not expected_app_id or app_id != expected_app_id:
        return False

    try:
        timestamp_int = int(timestamp)
    except (TypeError, ValueError):
        return False

    if len(signature) < 5:
        return False

    random_key = signature[:5]
    if not random_key:
        return False

    secret_key = settings.SHEIN_APP_SECRET
    if not secret_key:
        return False

    value = f"{app_id}&{timestamp_int}&{request.path}"
    key = f"{secret_key}{random_key}"

    digest = hmac.new(key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
    hex_signature = digest.hex()
    base64_signature = base64.b64encode(hex_signature.encode("utf-8")).decode("utf-8")
    expected_signature = f"{random_key}{base64_signature}"
    return expected_signature == signature


def _get_sales_channel_from_request(request) -> SheinSalesChannel | None:
    open_key_id = _normalize_header(request, "x-lt-openKeyId")
    if not open_key_id:
        return None
    return SheinSalesChannel.objects.filter(open_key_id=open_key_id).first()


def _normalize_event_data(*, event_data: str | None) -> str | None:
    if not event_data:
        return None
    normalized = str(event_data).strip()
    if not normalized:
        return None
    normalized = normalized.replace(" ", "+")
    normalized = "".join(normalized.split())
    return normalized or None


def _build_aes_bytes(*, value: str, length: int = 16) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) >= length:
        return raw[:length]
    return raw.ljust(length, b"\0")


def _decrypt_event_data(*, event_data: str, secret_key: str):
    normalized = _normalize_event_data(event_data=event_data)
    if not normalized:
        return None

    iv_seed = constants.DEFAULT_AES_IV
    if len(iv_seed.encode("utf-8")) < 16:
        return None

    iv_bytes = _build_aes_bytes(value=iv_seed)
    padded = normalized + "=" * (-len(normalized) % 4)

    key_bytes = _build_aes_bytes(value=secret_key)
    try:
        decoded = base64.b64decode(padded)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        decrypted = cipher.decrypt(decoded)
        plaintext = unpad(decrypted, AES.block_size).decode("utf-8")
        payload = json.loads(plaintext)

        if isinstance(payload, str):
            payload = json.loads(payload)

    except Exception as e:  # noqa: BLE001 - surface a clean failure to the caller
        return None

    if isinstance(payload, dict):
        return payload

    return None


def _extract_webhook_payload(*, request) -> dict | None:
    event_data = request.POST.get("eventData") if hasattr(request, "POST") else None
    event_data = _normalize_event_data(event_data=event_data)

    if not event_data:
        content_type = request.META.get("CONTENT_TYPE", "") or ""
        if request.body and "application/json" in content_type:
            try:
                body = json.loads(request.body)
            except ValueError:
                body = None
            if isinstance(body, dict):
                event_data = _normalize_event_data(event_data=body.get("eventData"))
                if not event_data:
                    return body
        elif request.body and "application/x-www-form-urlencoded" in content_type:
            body = QueryDict(request.body.decode("utf-8"), encoding="utf-8")
            event_data = _normalize_event_data(event_data=body.get("eventData"))
        elif request.body and "multipart/form-data" in content_type:
            try:
                parser = MultiPartParser(request.META, request, request.upload_handlers)
                data, _files = parser.parse()
            except (MultiPartParserError, ValueError):
                data = None
            if data:
                event_data = _normalize_event_data(event_data=data.get("eventData"))

    if event_data:
        secret_key = settings.SHEIN_APP_SECRET
        if not secret_key:
            return None

        return _decrypt_event_data(event_data=event_data, secret_key=secret_key)

    return None


@csrf_exempt
def shein_product_document_audit_status_notice(request):
    sales_channel = _get_sales_channel_from_request(request)
    if not sales_channel:
        return HttpResponse(status=401)

    if not _verify_shein_webhook_signature(sales_channel=sales_channel, request=request):
        return HttpResponse(status=401)

    payload = _extract_webhook_payload(request=request)
    if not isinstance(payload, dict):
        return HttpResponse(status=400)

    spu_name = payload.get("spu_name")
    audit_state = payload.get("audit_state")
    failed_reason = payload.get("failed_reason")

    if not spu_name:
        return HttpResponse(status=202)

    from sales_channels.models.products import RemoteProduct
    from django.db.utils import OperationalError, ProgrammingError

    remote_product = SheinProduct.objects.filter(
        sales_channel=sales_channel,
        spu_name=str(spu_name),
    ).first()
    if not remote_product:
        logger.warning(
            "Shein audit webhook could not resolve remote product (channel=%s spu_name=%s)",
            getattr(sales_channel, "pk", None),
            spu_name,
        )
        return HttpResponse(status=202)

    updates: list[str] = []
    if spu_name and remote_product.remote_id != spu_name:
        remote_product.remote_id = str(spu_name)
        updates.append("remote_id")

    if updates:
        RemoteProduct.objects.filter(pk=remote_product.pk).update(
            remote_id=remote_product.remote_id,
        )

    try:
        SheinProductIssue.upsert_from_webhook(
            remote_product=remote_product,
            payload=payload,
        )
    except (OperationalError, ProgrammingError):
        # Table not yet migrated; allow webhook to succeed so remote_id still updates.
        logger.info("SheinProductIssue table not available yet; skipping issue upsert.")

    remote_product.add_log(
        action=IntegrationLog.ACTION_UPDATE,
        response={"webhook": "product_document_audit_status_notice", "payload": payload},
        payload={"spu_name": spu_name, "audit_state": audit_state},
        identifier="SheinProductAuditWebhook",
        remote_product=remote_product,
    )

    if failed_reason:
        if isinstance(failed_reason, list):
            failed_reason_message = "; ".join(
                str(reason).strip() for reason in failed_reason if str(reason).strip()
            )
        else:
            failed_reason_message = str(failed_reason or "").strip()
        if not failed_reason_message:
            failed_reason_message = "Shein product review failed."

        remote_product.add_log(
            action=IntegrationLog.ACTION_UPDATE,
            response="",
            payload={
                "spu_name": spu_name,
                "failed_reason": failed_reason,
                "audit_state": audit_state,
            },
            identifier="SheinProductAuditFailed",
            remote_product=remote_product,
            error_message=failed_reason_message,
        )
        remote_product.refresh_status(
            override_status=remote_product.STATUS_APPROVAL_REJECTED,
        )

    return JsonResponse({"ok": True})
