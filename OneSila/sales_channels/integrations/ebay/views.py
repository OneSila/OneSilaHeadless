import hashlib
import json
import logging
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannel

logger = logging.getLogger(__name__)


def _get_verification_token() -> str:
    token = getattr(settings, "EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN", "")
    if not token:
        raise ImproperlyConfigured("Missing EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN setting")
    if not 32 <= len(token) <= 80:
        raise ImproperlyConfigured(
            "EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN must be between 32 and 80 characters"
        )
    return token


def _get_registered_endpoint(request) -> str:
    """
    The 'endpoint' used in the challenge hash must be EXACTLY the URL you registered,
    with no query string or fragment. Prefer a settings override; otherwise strip query/fragment.
    """
    endpoint = getattr(settings, "EBAY_ACCOUNT_DELETION_ENDPOINT", None)
    if endpoint:
        return endpoint

    full_url = request.build_absolute_uri()  # may include ?challenge_code=...&app_key=...
    parts = urlsplit(full_url)
    # Remove query + fragment to avoid mismatches; keep scheme + host + path exactly as served
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _compute_challenge_response(*, challenge_code: str, verification_token: str, endpoint: str) -> str:
    """
    Spec: SHA-256 of the concatenation: challengeCode + verificationToken + endpoint
    """
    data = (challenge_code + verification_token + endpoint).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


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


def _handle_challenge(*, request, verification_token: str) -> HttpResponse:
    # eBay sends a random challenge code as 'challenge_code' (or sometimes 'challengeCode')
    challenge_code = request.GET.get("challenge_code") or request.GET.get("challengeCode")
    if not challenge_code:
        logger.warning("eBay account deletion challenge missing challenge code")
        return HttpResponse(status=400)

    # IMPORTANT: Do NOT include query params in the endpoint used for hashing.
    endpoint = _get_registered_endpoint(request)

    challenge_response = _compute_challenge_response(
        challenge_code=challenge_code,
        verification_token=verification_token,
        endpoint=endpoint,
    )

    return JsonResponse({"challengeResponse": challenge_response})


def _handle_notification(*, request, verification_token: str) -> HttpResponse:
    """
    For marketplace account deletion POST notifications, eBay can include data identifying the account.
    We accept the payload, try to find an identifier, and mark the channel for delete.
    """

    try:
        raw_body = request.body.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("eBay account deletion payload is not valid UTF-8")
        return HttpResponse(status=400)

    body = (raw_body or "").strip()
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
