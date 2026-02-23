from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel

from core import models
from sales_channels.models.mixins import RemoteObjectMixin


class RemoteDocumentType(PolymorphicModel, RemoteObjectMixin, models.Model):
    """Polymorphic remote document type model."""
    CATEGORY_ID_KEYS = ("remote_id", "id", "value", "category_id")

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
