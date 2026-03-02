from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core import models
from sales_channels.models.documents import (
    RemoteDocument,
    RemoteDocumentProductAssociation,
    RemoteDocumentType,
)


class SheinDocumentType(RemoteDocumentType):
    def _validate_category_remote_ids_exist(self, *, field_name: str, remote_ids: list[str]) -> None:
        if not remote_ids:
            return

        from sales_channels.integrations.shein.models.categories import SheinCategory

        category_qs = SheinCategory.objects.filter(remote_id__in=remote_ids)
        if self.sales_channel_id:
            category_qs = category_qs.filter(sales_channel_id=self.sales_channel_id)

        existing_remote_ids = set(category_qs.values_list("remote_id", flat=True).distinct())
        missing_remote_ids = sorted(set(remote_ids) - existing_remote_ids)
        if not missing_remote_ids:
            return

        if self.sales_channel_id:
            cross_channel_remote_ids = set(
                SheinCategory.objects.filter(remote_id__in=missing_remote_ids)
                .exclude(sales_channel_id=self.sales_channel_id)
                .values_list("remote_id", flat=True)
                .distinct()
            )
            if cross_channel_remote_ids:
                raise ValidationError(
                    {
                        field_name: _(
                            "Shein category remote IDs do not belong to this sales channel: %(ids)s"
                        )
                        % {"ids": ", ".join(sorted(cross_channel_remote_ids))}
                    }
                )

        raise ValidationError(
            {
                field_name: _(
                    "Unknown Shein category remote IDs: %(ids)s"
                )
                % {"ids": ", ".join(missing_remote_ids)}
            }
        )

    def clean(self):
        super().clean()

        required_remote_ids = self._normalise_category_remote_ids(field_name="required_categories")
        optional_remote_ids = self._normalise_category_remote_ids(field_name="optional_categories")

        self._validate_category_remote_ids_exist(
            field_name="required_categories",
            remote_ids=required_remote_ids,
        )
        self._validate_category_remote_ids_exist(
            field_name="optional_categories",
            remote_ids=optional_remote_ids,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class SheinDocument(RemoteDocument):
    remote_url = models.URLField(
        max_length=2048,
        null=True,
        blank=True,
        help_text="Public URL of the certificate file mirrored on Shein.",
    )
    remote_filename = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Filename stored or returned by Shein for this document.",
    )

    class Meta:
        verbose_name = "Shein Remote Document"
        verbose_name_plural = "Shein Remote Documents"
        search_terms = ["remote_id", "remote_url", "remote_filename"]

    def clean(self):
        super().clean()

        if not self.remote_document_type_id:
            return

        remote_document_type_id = (
            SheinDocumentType.objects.filter(id=self.remote_document_type_id)
            .values_list("id", flat=True)
            .first()
        )
        if remote_document_type_id is None:
            raise ValidationError(
                {"remote_document_type": _("Shein remote documents must use a Shein document type mapping.")}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class SheinDocumentThroughProduct(RemoteDocumentProductAssociation):
    expire_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Certificate expiration timestamp returned by Shein, when available.",
    )
    missing_status = models.BooleanField(
        default=False,
        help_text="Whether this certificate is currently marked as missing by Shein.",
    )

    class Meta:
        verbose_name = "Shein Document Through Product"
        verbose_name_plural = "Shein Documents Through Products"
