import json
import os

from properties.models import ProductProperty
from sales_channels.exceptions import PreFlightCheckError
from sales_channels.factories.products.documents import (
    RemoteDocumentProductThroughCreateFactory,
    RemoteDocumentProductThroughDeleteFactory,
    RemoteDocumentProductThroughUpdateFactory,
)
from sales_channels.helpers import describe_document
from sales_channels.integrations.amazon.exceptions import AmazonUnsupportedPropertyForProductType
from sales_channels.integrations.amazon.factories.properties.mixins import (
    AmazonProductPropertyBaseMixin,
    TOKEN_RE,
)
from sales_channels.integrations.amazon.models import (
    AmazonDocumentThroughProduct,
    AmazonDocumentType,
    AmazonProperty,
    AmazonRemoteLanguage,
)
from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition


class AmazonDocumentThroughProductBase(AmazonProductPropertyBaseMixin):
    remote_model_class = AmazonDocumentThroughProduct
    remote_document_assign_model_class = AmazonDocumentThroughProduct
    has_remote_document_instance = False

    def __init__(self, *args, view, get_value_only=False, remote_rule=None, **kwargs):
        self.view = view
        self.get_value_only = get_value_only
        self.remote_rule = remote_rule
        super().__init__(*args, **kwargs)

        self.remote_document_type = None
        self.document_property_code = None
        self.public_definition = None

    def _document_label(self):
        media = self._get_media()
        media_through = self._get_media_through()
        return describe_document(
            media=media,
            media_through=media_through,
            remote_document_type=self.remote_document_type,
        )

    def _get_media_through(self):
        if getattr(self, "local_instance", None) is not None:
            return self.local_instance
        if getattr(self, "remote_instance", None) is not None:
            return getattr(self.remote_instance, "local_instance", None)
        return None

    def _get_media(self):
        media_through = self._get_media_through()
        if media_through is None:
            return None
        return getattr(media_through, "media", None)

    def _get_or_resolve_remote_rule(self):
        if self.remote_rule is not None:
            return self.remote_rule
        if self.remote_product is None:
            raise PreFlightCheckError("Missing remote product for Amazon document sync.")
        self.remote_rule = self.remote_product.get_remote_rule()
        return self.remote_rule

    def _resolve_remote_document_type(self):
        media = self._get_media()
        if media is None or not getattr(media, "document_type_id", None):
            return None

        mapped_queryset = AmazonDocumentType.objects.filter(
            sales_channel=self.sales_channel,
            local_instance_id=media.document_type_id,
        ).exclude(remote_id__in=(None, ""))
        mapped_ids = list(mapped_queryset.values_list("id", flat=True))
        if not mapped_ids:
            return None

        if len(mapped_ids) > 1:
            raise PreFlightCheckError(
                f"{self._document_label()} has multiple Amazon document type mappings. Keep exactly one mapping."
            )

        return mapped_queryset.first()

    def _resolve_ps_document_property_code(self):
        media_through = self._get_media_through()
        position = None
        if media_through is not None and getattr(self, "remote_product", None) is not None:
            from media.models import MediaProductThrough

            mapped_local_document_type_ids = list(
                AmazonDocumentType.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_id="image_locator_ps",
                )
                .exclude(local_instance_id__isnull=True)
                .values_list("local_instance_id", flat=True)
            )
            if mapped_local_document_type_ids:
                ordered_ps_document_ids = list(
                    MediaProductThrough.objects.get_public_product_documents(
                        product=self.remote_product.local_instance,
                        sales_channel=self.sales_channel,
                    )
                    .filter(media__document_type_id__in=mapped_local_document_type_ids)
                    .order_by("sort_order", "id")
                    .values_list("id", flat=True)
                )
                for index, media_through_id in enumerate(ordered_ps_document_ids, start=1):
                    if media_through_id == media_through.id:
                        position = index
                        break

        if position is None:
            sort_order = getattr(media_through, "sort_order", 0) if media_through else 0
            try:
                position = int(sort_order) + 1
            except (TypeError, ValueError):
                position = 1

        position = max(1, min(position, 6))
        code = f"image_locator_ps{position:02d}"

        remote_rule = self._get_or_resolve_remote_rule()
        exists = AmazonPublicDefinition.objects.filter(
            api_region_code=self.view.api_region_code,
            product_type_code=remote_rule.product_type_code,
            code=code,
        ).exists()
        if not exists:
            return None

        return code

    def _resolve_pf_document_property_code(self):
        remote_rule = self._get_or_resolve_remote_rule()
        codes = list(
            AmazonPublicDefinition.objects.filter(
                api_region_code=self.view.api_region_code,
                product_type_code=remote_rule.product_type_code,
                code__regex=r"^image_locator_.*pf$",
            )
            .values_list("code", flat=True)
            .distinct()
        )

        if not codes:
            return None
        if len(codes) > 1:
            raise PreFlightCheckError(
                f"{self._document_label()} matched multiple PF fields ({', '.join(sorted(codes))}). Resolve marketplace PF mapping first."
            )

        return codes[0]

    def _resolve_ee_document_property_code(self):
        remote_rule = self._get_or_resolve_remote_rule()
        codes = list(
            AmazonPublicDefinition.objects.filter(
                api_region_code=self.view.api_region_code,
                product_type_code=remote_rule.product_type_code,
                code__regex=r"^image_locator_.*ee$",
            )
            .values_list("code", flat=True)
            .distinct()
        )

        if not codes:
            return None
        if len(codes) > 1:
            raise PreFlightCheckError(
                f"{self._document_label()} matched multiple EE fields ({', '.join(sorted(codes))}). Resolve marketplace EE mapping first."
            )

        return codes[0]

    def _resolve_document_property_code(self):
        remote_id = str(getattr(self.remote_document_type, "remote_id", "") or "").strip()
        if not remote_id:
            raise PreFlightCheckError(f"{self._document_label()} mapped Amazon document type has no remote id.")

        if remote_id.startswith("compliance_media__"):
            return "compliance_media"
        if remote_id == "safety_data_sheet_url":
            return "safety_data_sheet_url"
        if remote_id == "image_locator_ps":
            return self._resolve_ps_document_property_code()
        if remote_id == "image_locator_pf":
            return self._resolve_pf_document_property_code()
        if remote_id == "image_locator_ee":
            return self._resolve_ee_document_property_code()

        raise PreFlightCheckError(
            f"{self._document_label()} is mapped to unsupported Amazon document type '{remote_id}'."
        )

    def _validate_media_for_document_type(self):
        media = self._get_media()
        if media is None:
            raise PreFlightCheckError("Document media is missing for Amazon document sync.")

        remote_id = str(getattr(self.remote_document_type, "remote_id", "") or "").strip()
        is_image_locator = remote_id.startswith("image_locator_")

        if is_image_locator:
            if not media.is_document_image or not media.image:
                raise PreFlightCheckError(
                    f"{self._document_label()} must be uploaded as an image document for Amazon image locator fields."
                )
            return

        if media.is_document_image:
            if not media.image:
                raise PreFlightCheckError(f"{self._document_label()} is marked as image document but image is missing.")
            return

        file_obj = getattr(media, "file", None)
        file_name = getattr(file_obj, "name", "") if file_obj else ""
        extension = os.path.splitext(file_name)[1].lower()
        if extension != ".pdf":
            raise PreFlightCheckError(
                f"{self._document_label()} must be a PDF (or image document) for Amazon document fields."
            )

    def _get_document_url(self):
        existing_remote_url = str(getattr(getattr(self, "remote_instance", None), "remote_url", "") or "").strip()
        if existing_remote_url:
            return existing_remote_url

        media = self._get_media()
        if media is None:
            raise PreFlightCheckError("Document media is missing for Amazon document sync.")

        document_url = media.get_real_document_file()
        if not document_url:
            raise PreFlightCheckError(
                f"{self._document_label()} does not have a public URL. Upload the file/image before syncing."
            )
        return document_url

    def _get_document_language(self):
        media = self._get_media()
        local_language = (
            str(
                getattr(media, "document_language", None)
                or getattr(self.view, "language_tag_local", None)
                or getattr(self.sales_channel.multi_tenant_company, "language", None)
                or ""
            )
            .strip()
        )
        if not local_language:
            return self.view.language_tag

        language_qs = AmazonRemoteLanguage.objects.filter(
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
        )
        remote_code = language_qs.filter(local_instance=local_language).values_list("remote_code", flat=True).first()
        if remote_code:
            return remote_code

        language_root = local_language.replace("-", "_").split("_")[0]
        remote_code = language_qs.filter(local_instance=language_root).values_list("remote_code", flat=True).first()
        if remote_code:
            return remote_code

        return self.view.language_tag

    def _get_compliance_content_type(self):
        remote_id = str(getattr(self.remote_document_type, "remote_id", "") or "").strip()
        if not remote_id.startswith("compliance_media__"):
            return None

        content_type = remote_id.split("__", 1)[1].strip()
        allowed_types = set(self.public_definition.document_allowed_types or [])
        if allowed_types and content_type not in allowed_types:
            raise PreFlightCheckError(
                f"{self._document_label()} maps to compliance type '{content_type}' which is not allowed for this product type."
            )
        return content_type

    def _replace_tokens(self, data, product):
        def _resolve(value):
            if value == "%document_url%":
                return self._get_document_url()
            if value == "%document_language%":
                return self._get_document_language()
            if value == "%document_type%":
                return self._get_compliance_content_type()

            match = TOKEN_RE.fullmatch(value)
            if not match:
                return value

            kind, code = match.groups()
            if kind == "auto":
                if code == "marketplace_id":
                    return self.view.remote_id
                if code == "language":
                    return self.view.language_tag
                return None

            if kind == "unit":
                return self._get_unit(code)

            if kind == "value":
                remote_property = AmazonProperty.objects.get(
                    sales_channel=self.sales_channel,
                    code=code,
                )
                local_property = remote_property.local_instance
                try:
                    product_property = ProductProperty.objects.get(
                        product=product,
                        property=local_property,
                    )
                except ProductProperty.DoesNotExist:
                    return None
                return self.get_remote_value_for_property(
                    prop_instance=product_property,
                    remote_property=remote_property,
                    language_code=self.view.language_tag_local,
                )

            return value

        def _walk(node):
            if isinstance(node, dict):
                return {key: _walk(node=value) for key, value in node.items()}
            if isinstance(node, list):
                return [_walk(node=value) for value in node]
            if isinstance(node, str):
                return _resolve(node)
            return node

        def _clean(node):
            if isinstance(node, dict):
                cleaned = {key: _clean(node=value) for key, value in node.items()}
                cleaned = {key: value for key, value in cleaned.items() if value not in (None, "", [], {})}
                if "unit" in cleaned and not any("value" in key for key in cleaned.keys()):
                    cleaned.pop("unit")
                if not cleaned:
                    return None
                if all(key in ("language_tag", "marketplace_id") for key in cleaned):
                    return None
                return cleaned
            if isinstance(node, list):
                cleaned_list = []
                for item in node:
                    cleaned_item = _clean(node=item)
                    if cleaned_item is not None:
                        cleaned_list.append(cleaned_item)
                return cleaned_list or None
            if isinstance(node, str):
                lower = node.lower()
                if lower == "true":
                    return True
                if lower == "false":
                    return False
                try:
                    return int(node) if node.isdigit() else float(node)
                except ValueError:
                    return node
            return node

        return _clean(node=_walk(node=data)) or {}

    def _prepare_document_context(self):
        self.remote_document_type = self._resolve_remote_document_type()
        if self.remote_document_type is None:
            return False

        self.document_property_code = self._resolve_document_property_code()
        if not self.document_property_code:
            return False
        try:
            self.public_definition = self._get_public_definition(
                self._get_or_resolve_remote_rule(),
                self.document_property_code,
            )
        except AmazonUnsupportedPropertyForProductType:
            return False

        if not self.public_definition.usage_definition:
            return False

        self._validate_media_for_document_type()
        self._get_compliance_content_type()
        return True

    def _build_document_attributes_payload(self):
        if not self.public_definition:
            return {}

        usage = json.loads(self.public_definition.usage_definition)
        payload = self._replace_tokens(usage, self.remote_product.local_instance)

        if not getattr(self.remote_product, "product_owner", False):
            allowed_properties = self.remote_rule.listing_offer_required_properties.get(self.view.api_region_code, [])
            if self.document_property_code not in allowed_properties:
                return {}

        return payload

    def _patch_remote_product(self, *, attributes):
        if self.get_value_only:
            return attributes

        return self.update_product(
            self.remote_product.remote_sku,
            self.view.remote_id,
            self.remote_rule,
            attributes,
        )

    def build_payload(self):
        self.payload = {}
        return self.payload

    def serialize_response(self, response):
        if hasattr(response, "payload"):
            return json.dumps(response.payload)
        return True

    def customize_remote_instance_data(self):
        self.remote_instance_data["remote_product"] = self.remote_product
        self.remote_instance_data["require_document"] = False
        self.remote_instance_data["remote_document"] = None
        return self.remote_instance_data

    def set_remote_id(self, response_data):
        # Remote ID here tracks the Amazon property code used for the assignment.
        pass

    def _sync_remote_instance_document_code(self):
        if not self.remote_instance or not self.document_property_code:
            return
        if self.remote_instance.remote_id == self.document_property_code:
            return
        self.remote_instance.remote_id = self.document_property_code
        self.remote_instance.save(update_fields=["remote_id"])


class AmazonDocumentThroughProductCreateFactory(
    AmazonDocumentThroughProductBase,
    RemoteDocumentProductThroughCreateFactory,
):
    def preflight_check(self):
        if not super().preflight_check():
            return False
        return self._prepare_document_context()

    def create_remote(self):
        attributes = self._build_document_attributes_payload()
        if not attributes:
            return None
        return self._patch_remote_product(attributes=attributes)

    def post_create_process(self):
        self._sync_remote_instance_document_code()


class AmazonDocumentThroughProductUpdateFactory(
    AmazonDocumentThroughProductBase,
    RemoteDocumentProductThroughUpdateFactory,
):
    create_factory_class = AmazonDocumentThroughProductCreateFactory

    def preflight_check(self):
        allowed = super().preflight_check() and self._prepare_document_context()
        if not allowed:
            self.remote_instance = None
        return allowed

    def update_remote(self):
        attributes = self._build_document_attributes_payload()
        if not attributes:
            return None
        return self._patch_remote_product(attributes=attributes)

    def needs_update(self):
        return True

    def post_update_process(self):
        self._sync_remote_instance_document_code()


class AmazonDocumentThroughProductDeleteFactory(
    AmazonDocumentThroughProductBase,
    RemoteDocumentProductThroughDeleteFactory,
):
    def _resolve_delete_property_code(self):
        if self.remote_instance and getattr(self.remote_instance, "remote_id", None):
            return str(self.remote_instance.remote_id).strip()

        try:
            if self._prepare_document_context():
                return self.document_property_code
        except PreFlightCheckError:
            return None

        return None

    def delete_remote(self):
        property_code = self._resolve_delete_property_code()
        if not property_code:
            return True

        attributes = {property_code: None}
        if self.get_value_only:
            return attributes

        response = self.update_product(
            self.remote_instance.remote_product.remote_sku,
            self.view.remote_id,
            self.remote_instance.remote_product.get_remote_rule(),
            attributes,
        )
        return response

    def serialize_response(self, response):
        return True
