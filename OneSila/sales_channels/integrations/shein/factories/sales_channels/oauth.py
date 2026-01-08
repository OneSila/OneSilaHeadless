"""Factories that orchestrate the Shein OAuth handshake."""

import base64
import hashlib
import hmac
import logging
import time
import secrets
import string
from typing import Optional
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.signals import refresh_website_pull_models
from sales_channels.integrations.shein import constants
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad

logger = logging.getLogger(__name__)


def _get_setting(name: str, default: Optional[str] = None) -> str:
    value = getattr(settings, name, default)
    if not value:
        raise ValueError(_("Missing Shein setting: %(name)s") % {"name": name})
    return value


class GetSheinRedirectUrlFactory:
    """Build the authorization URL that sends a merchant to Shein's OAuth flow."""

    def __init__(self, *, sales_channel: SheinSalesChannel):
        self.sales_channel = sales_channel
        self.redirect_url: Optional[str] = None

    @staticmethod
    def _authorization_host() -> str:
        return (
            constants.DEFAULT_TEST_AUTH_HOST
            if settings.DEBUG
            else constants.DEFAULT_PROD_AUTH_HOST
        )

    def _ensure_state(self) -> str:
        if not self.sales_channel.state:
            # The save method assigns a state when missing.
            self.sales_channel.save()
        return self.sales_channel.state

    def run(self) -> str:
        app_id = _get_setting("SHEIN_APP_ID")
        redirect_uri = _get_setting("SHEIN_REDIRECT_URI")
        state = self._ensure_state()

        encoded_redirect = base64.b64encode(redirect_uri.encode("utf-8")).decode("utf-8")

        params = {
            "appid": app_id,
            "redirectUrl": encoded_redirect,
            "state": state,
        }
        self.redirect_url = f"https://{self._authorization_host()}/#/empower?{urlencode(params)}"
        return self.redirect_url


class ValidateSheinAuthFactory:
    """Exchange a temp token for permanent Shein credentials."""

    def __init__(
        self,
        *,
        sales_channel: SheinSalesChannel,
        app_id: str,
        temp_token: str,
        state: Optional[str] = None,
    ):
        self.sales_channel = sales_channel
        self.app_id = app_id
        self.temp_token = temp_token
        self.state = state
        self.payload: Optional[dict] = None
        self.decrypted_secret: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> SheinSalesChannel:
        self._validate_inputs()
        response_payload = self._call_token_endpoint()
        self._ensure_unique_open_key(open_key_id=response_payload.get("openKeyId"))
        self.decrypted_secret = self._decrypt_secret(response_payload["secretKey"])
        self._persist(response_payload)
        self._dispatch_refresh()
        return self.sales_channel

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _validate_inputs(self) -> None:
        expected_app_id = _get_setting("SHEIN_APP_ID")
        if self.app_id != expected_app_id:
            raise ValueError(_("AppID mismatch during Shein authorization."))

        if self.state and self.sales_channel.state and self.state != self.sales_channel.state:
            raise ValueError(_("State mismatch during Shein authorization."))

    def _api_base_url(self) -> str:
        return (
            constants.DEFAULT_TEST_API_BASE_URL
            if settings.DEBUG
            else constants.DEFAULT_PROD_API_BASE_URL
        )

    def _call_token_endpoint(self) -> dict:
        url = f"{self._api_base_url().rstrip('/')}/open-api/auth/get-by-token"
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp)
        language = constants.map_language_for_header(self._get_company_language())

        headers = {
            "language": language,
            "x-lt-appid": self.app_id,
            "x-lt-signature": signature,
            "x-lt-timestamp": timestamp,
            "Content-Type": "application/json",
        }

        timeout = constants.DEFAULT_TIMEOUT
        try:
            response = requests.post(
                url,
                json={"tempToken": self.temp_token},
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Shein token exchange request failed")
            raise ValueError(_("Failed to contact Shein token endpoint.")) from exc
        data = response.json()
        if data.get("code") != "0":
            msg = data.get("msg") or "Unknown error"
            raise ValueError(_("Failed to validate Shein authorization: %(message)s") % {"message": msg})

        info = data.get("info") or {}
        if not info:
            raise ValueError(_("Shein authorization response missing info payload."))

        if self.state and info.get("state") and info.get("state") != self.state:
            raise ValueError(_("State mismatch in Shein response."))

        return info

    def _generate_signature(self, timestamp: str) -> str:
        """Generate the HMAC signature mandated by Shein for the token exchange."""

        path = "/open-api/auth/get-by-token"
        open_key = self.app_id
        secret = _get_setting("SHEIN_APP_SECRET")

        random_key = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(5)
        )
        value = f"{open_key}&{timestamp}&{path}"
        key = f"{secret}{random_key}"

        digest = hmac.new(key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
        hex_signature = digest.hex()
        base64_signature = base64.b64encode(hex_signature.encode("utf-8")).decode("utf-8")
        return f"{random_key}{base64_signature}"

    def _decrypt_secret(self, encrypted_secret: str) -> str:
        if not encrypted_secret:
            raise ValueError(_("Shein secretKey is empty."))

        app_secret = _get_setting("SHEIN_APP_SECRET")
        key_bytes = app_secret.encode("utf-8")[:16]
        iv_seed = constants.DEFAULT_AES_IV
        if len(iv_seed.encode("utf-8")) < 16:
            raise ValueError(_("Shein IV seed must be at least 16 bytes."))

        iv_bytes = bytearray(16)
        iv_bytes[:] = iv_seed.encode("utf-8")[:16]

        cipher = AES.new(key_bytes, AES.MODE_CBC, bytes(iv_bytes))
        padded_secret = encrypted_secret + "=" * (-len(encrypted_secret) % 4)
        decoded = base64.b64decode(padded_secret)
        decrypted = cipher.decrypt(decoded)
        return unpad(decrypted, AES.block_size).decode("utf-8")

    def _get_company_language(self) -> Optional[str]:
        company = getattr(self.sales_channel, "multi_tenant_company", None)
        return getattr(company, "language", None) if company else None

    def _ensure_unique_open_key(self, *, open_key_id: Optional[str]) -> None:
        if not open_key_id:
            return
        company = getattr(self.sales_channel, "multi_tenant_company", None)
        if not company:
            return
        existing = (
            SheinSalesChannel.objects.filter(
                multi_tenant_company=company,
                open_key_id=open_key_id,
            )
            .exclude(pk=self.sales_channel.pk)
            .only("hostname")
            .first()
        )
        if existing:
            raise ValidationError(
                {
                    "__all__": _(
                        "The Shein app is already connected to %(hostname)s."
                    )
                    % {"hostname": existing.hostname}
                }
            )

    def _persist(self, payload: dict) -> None:
        update_fields = [
            "state",
            "open_key_id",
            "secret_key_encrypted",
            "secret_key",
            "supplier_id",
            "supplier_source",
            "supplier_business_mode",
            "last_authorized_at",
        ]

        self.sales_channel.state = payload.get("state") or self.sales_channel.state
        self.sales_channel.open_key_id = payload.get("openKeyId")
        self.sales_channel.secret_key_encrypted = payload.get("secretKey")
        self.sales_channel.secret_key = self.decrypted_secret
        supplier_id = payload.get("supplierId")
        if supplier_id is not None:
            try:
                self.sales_channel.supplier_id = int(supplier_id)
            except (TypeError, ValueError):
                self.sales_channel.supplier_id = None
        supplier_source = payload.get("supplierSource")
        if supplier_source is not None:
            try:
                self.sales_channel.supplier_source = int(supplier_source)
            except (TypeError, ValueError):
                self.sales_channel.supplier_source = None
        self.sales_channel.supplier_business_mode = payload.get("supplierBusinessMode") or self.sales_channel.supplier_business_mode
        self.sales_channel.last_authorized_at = timezone.now()
        self.sales_channel.save(update_fields=update_fields)

    def _dispatch_refresh(self) -> None:
        refresh_website_pull_models.send(
            sender=self.sales_channel.__class__,
            instance=self.sales_channel,
        )
