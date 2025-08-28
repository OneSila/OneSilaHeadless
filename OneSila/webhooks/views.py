import hashlib
import hmac
import logging
import time

from django.conf import settings
from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


def _get_param(request, name, default=None):
    if name in request.GET:
        return request.GET.get(name)
    return request.headers.get(name, default)


def _get_bool(value, default=False):
    if value is None:
        return default
    return str(value).lower() in {"1", "true", "yes"}


def test_receiver(request):
    if getattr(settings, "DEBUGG", False):
        return HttpResponse(status=200)

    token = request.headers.get("X-Test-Token")
    if token != getattr(settings, "TEST_WEBHOOK_SECRET", ""):
        return HttpResponse(status=401)

    raw_body = request.body
    logger.info("webhook test receiver", extra={"headers": dict(request.headers), "body": raw_body})

    mode = _get_param(request, "mode", "success")
    delay_ms = _get_param(request, "delay_ms")
    delay_ms = int(delay_ms) if delay_ms else 0
    retry_after = _get_param(request, "retry_after")
    retry_after = int(retry_after) if retry_after else 0
    validate_signature = _get_bool(_get_param(request, "validate_signature", "true"), True)
    secret = _get_param(request, "secret_override", getattr(settings, "TEST_WEBHOOK_SECRET", ""))
    echo_headers = _get_bool(_get_param(request, "echo_headers"))
    echo_body = _get_bool(_get_param(request, "echo_body"))

    if mode == "fail_signature":
        return HttpResponse(status=401)

    if mode != "timeout" and delay_ms:
        time.sleep(delay_ms / 1000)

    if validate_signature:
        signature_header = request.headers.get("X-OneSila-Signature", "")
        parts = dict(part.split("=") for part in signature_header.split(",") if "=" in part)
        timestamp = parts.get("t")
        signature = parts.get("v1")
        valid = False
        try:
            timestamp_int = int(timestamp)
            payload = f"{timestamp}.".encode() + raw_body
            expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
            skew = abs(time.time() - timestamp_int) <= 300
            valid = hmac.compare_digest(expected, signature or "") and skew
        except Exception:
            valid = False
        if not valid:
            return HttpResponse(status=401)

    data = {"mode": mode}

    if echo_headers:
        safe_headers = {k: v for k, v in request.headers.items() if k.lower() not in {"authorization", "x-test-token"}}
        data["headers"] = safe_headers
    if echo_body:
        data["body"] = raw_body[:2048].decode("utf-8", errors="replace")

    if mode == "client_error":
        return JsonResponse(data, status=400)
    if mode == "server_error":
        return JsonResponse(data, status=500)
    if mode == "rate_limit":
        response = JsonResponse(data, status=429)
        response["Retry-After"] = str(retry_after or 1)
        return response
    if mode == "timeout":
        time.sleep((delay_ms or 10000) / 1000)
        return JsonResponse(data, status=200)
    if mode == "slow_ok":
        return JsonResponse(data, status=200)
    if mode == "redirect":
        response = JsonResponse(data, status=302)
        response["Location"] = "/"
        return response

    return JsonResponse(data, status=200)
