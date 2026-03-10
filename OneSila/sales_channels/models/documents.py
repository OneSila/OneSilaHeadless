from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel

from core import models
from sales_channels.managers import RemoteDocumentTypeManager
from sales_channels.models.mixins import RemoteObjectMixin


class RemoteDocumentType(PolymorphicModel, RemoteObjectMixin, models.Model):
    """Polymorphic remote document type model."""
    CATEGORY_ID_KEYS = ("remote_id", "id", "value", "category_id")
    objects = RemoteDocumentTypeManager()

    local_instance = models.ForeignKey(
        "media.DocumentType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local document type mapped to this remote document type.",
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    translated_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    description = models.TextField(
        null=True,
        blank=True,
    )
    required_categories = models.JSONField(
        default=list,
        blank=True,
    )
    optional_categories = models.JSONField(
        default=list,
        blank=True,
    )

    class Meta:
        verbose_name = "Remote Document Type"
        verbose_name_plural = "Remote Document Types"
        search_terms = ["remote_id", "name", "translated_name", "description"]
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "local_instance"],
                condition=models.Q(local_instance__isnull=False),
                name="unique_remote_document_type_mapping_per_channel",
                violation_error_message=_(
                    "A local document type can only be mapped once per sales channel."
                ),
            ),
        ]

    @property
    def effective_name(self) -> str:
        translated_name = str(self.translated_name or "").strip()
        name = str(self.name or "").strip()
        remote_id = str(self.remote_id or "").strip()

        if translated_name:
            return translated_name

        if name:
            return name

        if remote_id:
            return remote_id
        return "Remote document type"

    def _extract_category_remote_id(self, *, value, field_name: str, index: int) -> str:
        remote_id = None

        if isinstance(value, dict):
            for key in self.CATEGORY_ID_KEYS:
                candidate = value.get(key)
                if candidate not in (None, ""):
                    remote_id = candidate
                    break
        else:
            remote_id = value

        remote_id = str(remote_id or "").strip()
        if not remote_id:
            raise ValidationError(
                {
                    field_name: _(
                        "Entry %(position)s must include a non-empty remote category ID."
                    )
                    % {"position": index + 1}
                }
            )

        return remote_id

    def _normalise_category_remote_ids(self, *, field_name: str) -> list[str]:
        value = getattr(self, field_name, None)
        if value in (None, ""):
            normalised = []
            setattr(self, field_name, normalised)
            return normalised

        if not isinstance(value, list):
            raise ValidationError({field_name: _("Must be a JSON list of category remote IDs.")})

        normalised = [
            self._extract_category_remote_id(
                value=entry,
                field_name=field_name,
                index=index,
            )
            for index, entry in enumerate(value)
        ]
        setattr(self, field_name, normalised)
        return normalised

    def _validate_required_optional_do_not_overlap(
        self,
        *,
        required_remote_ids: list[str],
        optional_remote_ids: list[str],
    ) -> None:
        overlapping_ids = sorted(set(required_remote_ids).intersection(optional_remote_ids))
        if not overlapping_ids:
            return

        message = _(
            "Categories cannot exist in both required and optional lists: %(ids)s"
        ) % {"ids": ", ".join(overlapping_ids)}
        raise ValidationError(
            {
                "required_categories": message,
                "optional_categories": message,
            }
        )

    @staticmethod
    def _normalise_category_remote_id_for_append(*, category_remote_id) -> str:
        return str(category_remote_id or "").strip()

    @staticmethod
    def _normalise_category_list_for_append(*, value) -> list[str]:
        if not isinstance(value, list):
            return []

        seen: set[str] = set()
        normalised: list[str] = []
        for entry in value:
            candidate = str(entry or "").strip()
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            normalised.append(candidate)
        return normalised

    def add_category(self, *, category_remote_id, required: bool, save: bool = True) -> bool:
        normalized_category_remote_id = self._normalise_category_remote_id_for_append(
            category_remote_id=category_remote_id
        )
        if not normalized_category_remote_id:
            return False

        required_categories = self._normalise_category_list_for_append(
            value=getattr(self, "required_categories", []),
        )
        optional_categories = self._normalise_category_list_for_append(
            value=getattr(self, "optional_categories", []),
        )

        target_categories = required_categories if required else optional_categories
        other_categories = optional_categories if required else required_categories

        changed = False
        if normalized_category_remote_id in other_categories:
            other_categories.remove(normalized_category_remote_id)
            changed = True

        if normalized_category_remote_id not in target_categories:
            target_categories.append(normalized_category_remote_id)
            changed = True

        if not changed:
            return False

        self.required_categories = required_categories
        self.optional_categories = optional_categories

        if save:
            self.save()

        return True

    def add_required_category(self, *, category_remote_id, save: bool = True) -> bool:
        return self.add_category(
            category_remote_id=category_remote_id,
            required=True,
            save=save,
        )

    def add_optional_category(self, *, category_remote_id, save: bool = True) -> bool:
        return self.add_category(
            category_remote_id=category_remote_id,
            required=False,
            save=save,
        )

    def _validate_local_instance_is_mappable(self) -> None:
        if not self.local_instance_id:
            return

        from media.models import DocumentType

        local_code = getattr(self.local_instance, "code", None)
        if local_code is None:
            local_code = (
                DocumentType.objects.filter(id=self.local_instance_id)
                .values_list("code", flat=True)
                .first()
            )

        if local_code == DocumentType.INTERNAL_CODE:
            raise ValidationError(
                {
                    "local_instance": _(
                        "The INTERNAL document type cannot be mapped to remote document types."
                    )
                }
            )

    def clean(self):
        super().clean()

        self._validate_local_instance_is_mappable()
        required_remote_ids = self._normalise_category_remote_ids(field_name="required_categories")
        optional_remote_ids = self._normalise_category_remote_ids(field_name="optional_categories")
        self._validate_required_optional_do_not_overlap(
            required_remote_ids=required_remote_ids,
            optional_remote_ids=optional_remote_ids,
        )

    def __str__(self):
        label = self.name or self.translated_name or self.remote_id or "Remote document type"
        return f"{label} @ {self.sales_channel}"


class RemoteDocument(PolymorphicModel, RemoteObjectMixin, models.Model):
    """Polymorphic remote mirror of a local document media."""

    local_instance = models.ForeignKey(
        "media.Media",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local media instance associated with this remote document.",
    )
    remote_document_type = models.ForeignKey(
        "sales_channels.RemoteDocumentType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Mapped remote document type used to create this remote document.",
    )
    class Meta:
        unique_together = ("local_instance", "sales_channel", "remote_document_type")
        verbose_name = "Remote Document"
        verbose_name_plural = "Remote Documents"

    @property
    def frontend_name(self):
        if self.remote_document_type:
            return f"{self.remote_document_type} ({self.remote_id or 'pending'})"
        return f"Document {self.remote_id or 'pending'}"

    def clean(self):
        super().clean()

        if self.remote_document_type_id and self.sales_channel_id:
            remote_document_type_channel_id = (
                RemoteDocumentType.objects.filter(id=self.remote_document_type_id)
                .values_list("sales_channel_id", flat=True)
                .first()
            )
            if (
                remote_document_type_channel_id is not None
                and remote_document_type_channel_id != self.sales_channel_id
            ):
                raise ValidationError(
                    {"remote_document_type": _("Remote document type must belong to the same sales channel.")}
                )

        if self.local_instance_id:
            from media.models import Media

            media_type = (
                Media.objects.filter(id=self.local_instance_id)
                .values_list("type", flat=True)
                .first()
            )
            if media_type and media_type != Media.FILE:
                raise ValidationError({"local_instance": _("Only FILE media can be mirrored as remote documents.")})

    def __str__(self):
        remote_id = self.remote_id or "pending"
        return f"{self.remote_document_type or 'Document'} -> {remote_id}"


class RemoteDocumentProductAssociation(PolymorphicModel, RemoteObjectMixin, models.Model):
    """Polymorphic association of a remote document to a remote product."""

    local_instance = models.ForeignKey(
        "media.MediaProductThrough",
        on_delete=models.CASCADE,
        help_text="Local MediaProductThrough instance linked to this remote document association.",
    )
    remote_product = models.ForeignKey(
        "sales_channels.RemoteProduct",
        on_delete=models.CASCADE,
        help_text="Remote product linked to this document association.",
    )
    remote_document = models.ForeignKey(
        "sales_channels.RemoteDocument",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Remote document assigned to the remote product.",
    )
    remote_url = models.URLField(
        max_length=2048,
        null=True,
        blank=True,
        help_text="Public source URL used for this remote document association sync.",
    )
    require_document = models.BooleanField(
        default=True,
        help_text="When enabled, a linked remote_document is required for this assignment.",
    )

    class Meta:
        verbose_name = "Remote Document Product Association"
        verbose_name_plural = "Remote Document Product Associations"
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(require_document=True) & models.Q(remote_document__isnull=False))
                    | (models.Q(require_document=False) & models.Q(remote_document__isnull=True))
                ),
                name="remote_document_product_assoc_require_document_consistency",
                violation_error_message=_(
                    "remote_document is required only when require_document is enabled."
                ),
            ),
            models.UniqueConstraint(
                fields=["local_instance", "sales_channel", "remote_product", "remote_document"],
                condition=models.Q(require_document=True),
                name="remote_document_product_assoc_unique_with_remote_document",
            ),
            models.UniqueConstraint(
                fields=["local_instance", "sales_channel", "remote_product"],
                condition=models.Q(require_document=False),
                name="remote_document_product_assoc_unique_without_remote_document",
            ),
        ]

    @property
    def frontend_name(self):
        return f"{self.remote_document or 'Document mapping'} for {self.remote_product}"

    def __str__(self):
        return f"{self.remote_document or 'Document mapping'} associated with {self.remote_product}"
