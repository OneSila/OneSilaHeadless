import json
import re
import logging
from copy import deepcopy
from typing import Any

from django.core.exceptions import ValidationError

from integrations.constants import (
    AMAZON_INTEGRATION,
    EBAY_INTEGRATION,
    MAGENTO_INTEGRATION,
    SHEIN_INTEGRATION,
    SHOPIFY_INTEGRATION,
    WOOCOMMERCE_INTEGRATION,
)
from llm.factories.bulk_content_prompt import build_bulk_content_system_prompt
from llm.factories.mixins import AskGPTMixin, CalculateCostMixin, CreateTransactionMixin

logger = logging.getLogger(__name__)


BASE_FIELD_FLAGS = {
    "name": True,
    "subtitle": False,
    "shortDescription": True,
    "description": True,
    "bulletPoints": False,
}

BASE_FIELD_LIMITS = {
    "name": {"min": 0, "max": 512},
    "subtitle": {"min": 0, "max": 0},
    "shortDescription": {"min": 0, "max": 500},
    "description": {"min": 0, "max": 6000},
    "bulletPoints": {"min": 0, "max": 255},
}

INTEGRATION_RULES = {
    MAGENTO_INTEGRATION: {
        "flags": {},
        "limits": {"name": {"max": 255}},
    },
    WOOCOMMERCE_INTEGRATION: {
        "flags": {},
        "limits": {},
    },
    SHOPIFY_INTEGRATION: {
        "flags": {"shortDescription": False},
        "limits": {"name": {"max": 70}, "description": {"max": 5000}},
    },
    AMAZON_INTEGRATION: {
        "flags": {"shortDescription": False, "bulletPoints": True},
        "limits": {"name": {"min": 150, "max": 200}, "description": {"min": 1000, "max": 2000}},
    },
    EBAY_INTEGRATION: {
        "flags": {"subtitle": True},
        "limits": {"name": {"max": 80}, "subtitle": {"max": 55}, "description": {"max": 4000}},
    },
    SHEIN_INTEGRATION: {
        "flags": {"subtitle": False, "shortDescription": False, "bulletPoints": False},
        "limits": {"name": {"max": 1000}, "description": {"max": 5000}},
    },
    "default": {"flags": {}, "limits": {}},
}

INTEGRATION_GUIDELINES = {
    AMAZON_INTEGRATION: [
        "No promotional claims or superlatives.",
        "Use factual, keyword-friendly phrasing.",
        "Bullet points must be feature-focused and concise.",
        "For titles, do not repeat the same word twice (case-insensitive).",
    ],
    SHOPIFY_INTEGRATION: [
        "Brand-forward tone is allowed.",
        "Use engaging, benefit-led copy.",
    ],
    MAGENTO_INTEGRATION: [
        "Neutral, specification-focused tone.",
        "Prioritize clarity and scannability.",
    ],
    EBAY_INTEGRATION: [
        "Clear, direct listing copy.",
        "Subtitle should be short and benefit-led.",
    ],
    SHEIN_INTEGRATION: [
        "Fashion-friendly tone without exaggeration.",
        "Keep copy concise and clean.",
    ],
    WOOCOMMERCE_INTEGRATION: [
        "Balanced, customer-friendly tone.",
        "Emphasize core features and benefits.",
    ],
}

REQUIRED_BULLET_POINTS = 5
LLM_FIELDS = ("name", "subtitle", "shortDescription", "description", "bulletPoints")


def build_field_rules(*, integration_type: str) -> dict[str, dict[str, Any]]:
    rules = {
        "flags": deepcopy(BASE_FIELD_FLAGS),
        "limits": deepcopy(BASE_FIELD_LIMITS),
    }

    overrides = INTEGRATION_RULES.get(integration_type, INTEGRATION_RULES["default"])
    for field_name, enabled in overrides.get("flags", {}).items():
        rules["flags"][field_name] = enabled

    for field_name, limit_overrides in overrides.get("limits", {}).items():
        base_limit = rules["limits"].setdefault(field_name, {"min": 0, "max": 0})
        base_limit.update(limit_overrides)

    return rules


def normalize_bullet_points(*, value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        cleaned = []
        for line in lines:
            cleaned.append(line.lstrip("-•").strip())
        return [item for item in cleaned if item]
    return [str(value).strip()] if str(value).strip() else []


def is_empty_value(*, value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned == "" or cleaned == "<p><br></p>"
    if isinstance(value, list):
        return len([item for item in value if str(item).strip()]) == 0
    return False


def normalize_text(*, value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_optional_text(*, value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _limit_value(*, value: int | None) -> int | None:
    if value is None or value <= 0:
        return None
    return value


class BulkContentLLM(AskGPTMixin, CalculateCostMixin, CreateTransactionMixin):
    model = "gpt-5-mini"
    temperature = 0.4
    max_tokens = 8000

    def __init__(
        self,
        *,
        product,
        channels: list[dict[str, Any]],
        additional_informations: str | None = None,
        debug: bool = True,
    ):
        super().__init__()
        self.product = product
        self.channels = channels
        self.product_sku = str(product.sku or product.id)
        self.debug = debug
        self.multi_tenant_company = product.multi_tenant_company
        self.additional_informations = normalize_optional_text(value=additional_informations)
        self.channel_configs: dict[str, dict[str, Any]] = {}
        self.integration_id_aliases: dict[str, str] = {}
        for channel in channels:
            integration_id = str(channel.get("integration_id"))
            self.channel_configs[integration_id] = {
                "languages": list(channel.get("languages", [])),
                "field_rules": channel.get("field_rules", {}),
            }
            fallback_id = channel.get("integration_fallback_id")
            if fallback_id and str(fallback_id) != integration_id:
                self.integration_id_aliases[str(fallback_id)] = integration_id
        self.retry_errors: list[str] | None = None
        self.previous_output: str | None = None
        self.used_points = 0

    @property
    def system_prompt(self) -> str:
        return build_bulk_content_system_prompt(
            required_bullet_points=REQUIRED_BULLET_POINTS,
        )

    def _prompt_rules(self, *, field_rules: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        rules = deepcopy(field_rules)
        rules["flags"] = {
            field: enabled for field, enabled in rules["flags"].items() if field in LLM_FIELDS
        }
        rules["limits"] = {
            field: limits for field, limits in rules["limits"].items() if field in LLM_FIELDS
        }
        return rules

    def _prompt_channels(self) -> list[dict[str, Any]]:
        cleaned_channels = []
        for channel in self.channels:
            cleaned = {
                key: value
                for key, value in channel.items()
                if key not in {"integration_fallback_id", "existing_content"}
            }
            cleaned["field_rules"] = self._prompt_rules(field_rules=channel.get("field_rules", {}))
            cleaned_channels.append(cleaned)
        return cleaned_channels

    @property
    def prompt(self) -> str:
        payload = {
            "product_id": str(self.product.id),
            "product_sku": self.product_sku,
            "channels": self._prompt_channels(),
            "writing_brief": [
                "Customer-facing storefront copy. Write about the product, not the listing.",
                "Do not mention ordering, returns, customer service, inspections, or internal codes.",
                "Do not use em dashes or hyphens; use commas or plain sentences.",
                "Avoid meta phrases like \"this description\" or \"this listing\".",
                "Do not dump property labels; integrate facts naturally.",
                "If facts are limited, keep it short and factual. Do not pad to fill length.",
            ],
        }
        if self.additional_informations:
            payload["additional_informations"] = self.additional_informations

        return json.dumps(payload, ensure_ascii=True, indent=2)

    def _strip_code_fences(self, *, text: str) -> str:
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("```", 1)[1].strip()
            if clean.startswith("json"):
                clean = clean[len("json"):].strip()
            if "```" in clean:
                clean = clean.split("```")[0].strip()
        return clean

    def _extract_json_block(self, *, text: str) -> str | None:
        start_idx = None
        stack = []
        in_string = False
        escape = False

        for idx, char in enumerate(text):
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == "\"":
                    in_string = False
                continue

            if char == "\"":
                in_string = True
                continue

            if char in ("{", "["):
                if start_idx is None:
                    start_idx = idx
                stack.append(char)
                continue

            if char in ("}", "]") and stack:
                opening = stack.pop()
                if (opening == "{" and char != "}") or (opening == "[" and char != "]"):
                    return None
                if not stack and start_idx is not None:
                    return text[start_idx:idx + 1]

        return None

    def _escape_control_chars(self, *, text: str) -> str:
        escaped = []
        in_string = False
        escape = False

        for char in text:
            if in_string:
                if escape:
                    escape = False
                    escaped.append(char)
                    continue
                if char == "\\":
                    escape = True
                    escaped.append(char)
                    continue
                if char == "\"":
                    in_string = False
                    escaped.append(char)
                    continue
                if char == "\n":
                    escaped.append("\\n")
                    continue
                if char == "\r":
                    escaped.append("\\r")
                    continue
                if char == "\t":
                    escaped.append("\\t")
                    continue
                escaped.append(char)
                continue

            if char == "\"":
                in_string = True
            escaped.append(char)

        return "".join(escaped)

    def _remove_trailing_commas(self, *, text: str) -> str:
        return re.sub(r",\s*([}\]])", r"\1", text)

    def _clean_json_response(self, *, text: str) -> dict[str, Any]:
        clean = self._strip_code_fences(text=text)
        candidate = self._extract_json_block(text=clean) or clean
        candidate = self._escape_control_chars(text=candidate)
        candidate = self._remove_trailing_commas(text=candidate)
        return json.loads(candidate)

    def _normalize_language_payload(self, *, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}

        normalized: dict[str, Any] = {}
        for field in LLM_FIELDS:
            if field not in payload:
                continue
            value = payload.get(field)
            if field == "bulletPoints":
                normalized[field] = normalize_bullet_points(value=value)
            else:
                normalized[field] = normalize_text(value=value)
        return normalized

    def _parse_response(self, *, text: str) -> dict[str, dict[str, dict[str, Any]]]:
        data = self._clean_json_response(text=text)
        if not isinstance(data, dict):
            raise ValidationError("Invalid JSON response: expected an object.")

        expected_ids = set(self.channel_configs.keys())
        recognized: dict[str, Any] = {}
        for key, integration_payload in data.items():
            if key in expected_ids:
                recognized[key] = integration_payload
                continue
            if key in self.integration_id_aliases:
                recognized[self.integration_id_aliases[key]] = integration_payload
                continue
            if len(expected_ids) == 1 and len(data) == 1:
                recognized[next(iter(expected_ids))] = integration_payload

        missing = expected_ids - set(recognized.keys())
        if missing:
            raise ValidationError("Invalid JSON response: missing integration key.")

        normalized: dict[str, dict[str, dict[str, Any]]] = {}
        for integration_id, integration_payload in recognized.items():
            if not isinstance(integration_payload, dict):
                raise ValidationError("Invalid JSON response: integration payload must be an object.")

            if self.product_sku in integration_payload:
                product_payload = integration_payload[self.product_sku]
            elif len(integration_payload) == 1:
                product_payload = next(iter(integration_payload.values()))
            else:
                raise ValidationError("Invalid JSON response: missing product sku key.")

            if not isinstance(product_payload, dict):
                raise ValidationError("Invalid JSON response: product payload must be an object.")

            languages = self.channel_configs[integration_id]["languages"]
            normalized[integration_id] = {}
            for language in languages:
                lang_payload = product_payload.get(language)
                normalized[integration_id][language] = self._normalize_language_payload(payload=lang_payload)

        return normalized

    def _validate_language_payload(
        self,
        *,
        integration_id: str,
        language: str,
        payload: dict[str, Any],
        field_rules: dict[str, Any],
    ) -> list[str]:
        errors = []
        flags = field_rules.get("flags", {})
        limits = field_rules.get("limits", {})

        for field, enabled in flags.items():
            if not enabled:
                continue

            if field == "bulletPoints":
                points = payload.get(field, [])
                if not points:
                    errors.append(f"{integration_id}.{language}.{field} is missing")
                    continue
                if len(points) != REQUIRED_BULLET_POINTS:
                    errors.append(f"{integration_id}.{language}.{field} must have {REQUIRED_BULLET_POINTS} items")
                max_len = _limit_value(value=limits.get(field, {}).get("max"))
                for index, point in enumerate(points):
                    if is_empty_value(value=point):
                        errors.append(f"{integration_id}.{language}.{field}[{index}] is empty")
                        continue
                    if max_len and len(point) > max_len:
                        errors.append(f"{integration_id}.{language}.{field}[{index}] exceeds max length {max_len}")
                continue

            value = payload.get(field, "")
            if is_empty_value(value=value):
                errors.append(f"{integration_id}.{language}.{field} is missing")
                continue
            min_len = _limit_value(value=limits.get(field, {}).get("min"))
            max_len = _limit_value(value=limits.get(field, {}).get("max"))
            value_len = len(value)
            if min_len and value_len < min_len:
                errors.append(f"{integration_id}.{language}.{field} below min length {min_len}")
            if max_len and value_len > max_len:
                errors.append(f"{integration_id}.{language}.{field} exceeds max length {max_len}")

        return errors

    def _validate_response(self, *, payload: dict[str, dict[str, dict[str, Any]]]) -> list[str]:
        errors = []
        for integration_id, channel_payload in payload.items():
            channel_config = self.channel_configs.get(integration_id, {})
            languages = channel_config.get("languages", [])
            field_rules = channel_config.get("field_rules", {})
            for language in languages:
                lang_payload = channel_payload.get(language)
                if not isinstance(lang_payload, dict) or not lang_payload:
                    errors.append(f"{integration_id}.{language} payload is missing or invalid")
                    continue
                errors.extend(
                    self._validate_language_payload(
                        integration_id=integration_id,
                        language=language,
                        payload=lang_payload,
                        field_rules=field_rules,
                    )
                )
        return errors

    def generate_content(self) -> dict[str, dict[str, dict[str, Any]]]:

        if self.debug:
            logger.info("BulkContentLLM prompt:\n%s", self.prompt)
            print(f"BulkContentLLM prompt:\n{self.prompt}")
        self.response = self.ask_gpt()
        self.calculate_cost(self.response)
        self.text_response = self.get_text_response(self.response)
        print('----------------------------------------------------- RESPONMSE ???')
        print(self.text_response)
        if self.debug:
            logger.info("BulkContentLLM response:\n%s", self.text_response)
            print(f"BulkContentLLM response:\n{self.text_response}")
        self._create_transaction()
        self._create_ai_generate_process()
        self.used_points += self.ai_process.transaction.points

        parsed = self._parse_response(text=self.text_response)
        errors = self._validate_response(payload=parsed)
        if errors:
            raise ValidationError("; ".join(errors))
        return parsed
