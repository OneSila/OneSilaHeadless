import hashlib
import hmac
import json
import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannel

logger = logging.getLogger(__name__)


def _get_verification_token() -> str:
    token = getattr(settings, "EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN", "")
    if not token:
        raise ImproperlyConfigured("Missing EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN setting")
    if not 32 <= len(token) <= 80:
        raise ImproperlyConfigured("EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN must be between 32 and 80 characters")
    return token


def _compute_challenge_response(*, challenge_code: str, verification_token: str, endpoint: str) -> str:
    message = f"{challenge_code}{endpoint}".encode("utf-8")
    key = verification_token.encode("utf-8")
    return hmac.new(key=key, msg=message, digestmod=hashlib.sha256).hexdigest()


def _extract_account_identifier(*, payload: Any) -> str | None:
    candidate_keys = {
        "sellerid",
        "userid",
        "username",
        "remoteid",
        "remote_id",
        "accountid",
        "account_id",
        "ebayaccountid",
        "ebayuserid",
    }
    stack: list[Any] = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if isinstance(value, (dict, list)):
                    stack.append(value)
                elif isinstance(value, str) and key.lower() in candidate_keys:
                    return value
        elif isinstance(current, list):
            stack.extend(item for item in current if isinstance(item, (dict, list)))
    return None


def _extract_request_token(*, request) -> str | None:
    header_value = request.headers.get("X-EBAY-VERIFICATION-TOKEN")
    if header_value:
        return header_value

    return (
        request.GET.get("verification_token")
        or request.GET.get("verificationToken")
    )


def _handle_challenge(*, request, verification_token: str) -> HttpResponse:
    challenge_code = request.GET.get("challenge_code") or request.GET.get("challengeCode")
    if not challenge_code:
        logger.warning("eBay account deletion challenge missing challenge code")
        return HttpResponse(status=400)

    endpoint = request.GET.get("endpoint") or request.build_absolute_uri()
    provided_token = _extract_request_token(request=request)
    if provided_token and not constant_time_compare(provided_token, verification_token):
        logger.warning("eBay account deletion challenge token mismatch")
        return HttpResponse(status=403)

    response = _compute_challenge_response(
        challenge_code=challenge_code,
        verification_token=verification_token,
        endpoint=endpoint,
    )
    return JsonResponse({"challengeResponse": response})


def _handle_notification(*, request, verification_token: str) -> HttpResponse:
    provided_token = _extract_request_token(request=request)
    if not provided_token:
        logger.warning("eBay account deletion notification missing verification token")
        return HttpResponse(status=403)
    if not constant_time_compare(provided_token, verification_token):
        logger.warning("eBay account deletion notification token mismatch")
        return HttpResponse(status=403)

    try:
        raw_body = request.body.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("eBay account deletion payload is not valid UTF-8")
        return HttpResponse(status=400)

    body = raw_body.strip()
    if not body:
        payload: dict[str, Any] = {}
    else:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.warning("eBay account deletion payload is not valid JSON")
            return HttpResponse(status=400)

    identifier = _extract_account_identifier(payload=payload)
    if not identifier:
        logger.warning("eBay account deletion payload missing account identifier")
        return HttpResponse(status=200)

    channel = EbaySalesChannel.objects.filter(remote_id=identifier).first()
    if not channel:
        logger.warning("No eBay SalesChannel found for remote_id=%s", identifier)
        return HttpResponse(status=200)

    if not channel.mark_for_delete:
        channel.mark_for_delete = True
        channel.save(update_fields=["mark_for_delete"])
        logger.info("Marked eBay SalesChannel %s for deletion", channel.pk)

    return HttpResponse(status=200)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def ebay_marketplace_account_deletion(request):
    try:
        verification_token = _get_verification_token()
    except ImproperlyConfigured as exc:
        logger.error("eBay account deletion endpoint misconfigured: %s", exc)
        return HttpResponse(status=500)

    if request.method == "GET":
        return _handle_challenge(request=request, verification_token=verification_token)

    return _handle_notification(request=request, verification_token=verification_token)
