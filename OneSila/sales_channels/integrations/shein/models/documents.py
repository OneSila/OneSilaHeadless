from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from sales_channels.models.documents import RemoteDocumentType


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
