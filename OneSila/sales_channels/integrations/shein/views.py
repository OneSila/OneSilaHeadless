import json
import base64
import hashlib
import hmac
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from integrations.models import IntegrationLog
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.models import SheinProductIssue


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
    if not signature or not timestamp or not open_key_id:
        return False

    if open_key_id != (sales_channel.open_key_id or ""):
        return False

    try:
        timestamp_int = int(timestamp)
    except (TypeError, ValueError):
        return False

    random_key = signature[:5]
    if not random_key:
        return False

    secret_key = sales_channel.secret_key
    if not secret_key:
        return False

    value = f"{open_key_id}&{timestamp_int}&{request.path}"
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


def _resolve_remote_product_id(*, sales_channel: SheinSalesChannel, version: str | None, document_sn: str | None) -> int | None:
    qs = IntegrationLog.objects.filter(
        integration=sales_channel,
        identifier="SheinProductSubmission",
        status=IntegrationLog.STATUS_SUCCESS,
    )
    if version:
        qs = qs.filter(payload__version=version)
    elif document_sn:
        qs = qs.filter(payload__document_sn=document_sn)
    else:
        return None

    log = qs.order_by("-created_at").first()
    if not log:
        return None
    return log.object_id


@csrf_exempt
def shein_product_document_audit_status_notice(request):
    sales_channel = _get_sales_channel_from_request(request)
    if not sales_channel:
        return HttpResponse(status=401)

    if not _verify_shein_webhook_signature(sales_channel=sales_channel, request=request):
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body or b"{}")
    except ValueError:
        return HttpResponse(status=400)

    if not isinstance(payload, dict):
        return HttpResponse(status=400)

    spu_name = payload.get("spu_name")
    version = payload.get("version")
    document_sn = payload.get("document_sn")
    audit_state = payload.get("audit_state")
    failed_reason = payload.get("failed_reason")

    remote_product_id = _resolve_remote_product_id(
        sales_channel=sales_channel,
        version=version,
        document_sn=document_sn,
    )
    if not remote_product_id:
        logger.warning(
            "Shein audit webhook could not resolve remote product (channel=%s version=%s document_sn=%s)",
            getattr(sales_channel, "pk", None),
            version,
            document_sn,
        )
        return HttpResponse(status=202)

    from sales_channels.models.products import RemoteProduct
    from django.db.utils import OperationalError, ProgrammingError

    remote_product = RemoteProduct.objects.filter(pk=remote_product_id, sales_channel=sales_channel).first()
    if not remote_product:
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
        payload={"version": version, "document_sn": document_sn, "audit_state": audit_state},
        identifier="SheinProductAuditWebhook",
        remote_product=remote_product,
    )

    if failed_reason:
        remote_product.add_user_error(
            action=IntegrationLog.ACTION_UPDATE,
            response={"failed_reason": failed_reason, "audit_state": audit_state},
            payload={"version": version, "document_sn": document_sn},
            error_traceback="",
            identifier="SheinProductAuditFailed",
            remote_product=remote_product,
        )

    return JsonResponse({"ok": True})
