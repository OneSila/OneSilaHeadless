from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from sales_channels.models.documents import RemoteDocumentType


class EbayDocumentType(RemoteDocumentType):
    CATEGORY_ID_KEYS = ("remote_id", "id", "value", "category_id")

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

    def _get_sales_channel_tree_ids(self) -> list[str]:
        if not self.sales_channel_id:
            return []

        from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannelView

        tree_ids = (
            EbaySalesChannelView.objects.filter(sales_channel_id=self.sales_channel_id)
            .exclude(default_category_tree_id__isnull=True)
            .exclude(default_category_tree_id="")
            .values_list("default_category_tree_id", flat=True)
            .distinct()
        )
        return [str(tree_id).strip() for tree_id in tree_ids if str(tree_id).strip()]

    def _validate_category_remote_ids_exist(self, *, field_name: str, remote_ids: list[str]) -> None:
        if not remote_ids:
            return

        from sales_channels.integrations.ebay.models.categories import EbayCategory

        category_qs = EbayCategory.objects.filter(remote_id__in=remote_ids)
        tree_ids = self._get_sales_channel_tree_ids()
        if tree_ids:
            category_qs = category_qs.filter(marketplace_default_tree_id__in=tree_ids)

        existing_remote_ids = set(category_qs.values_list("remote_id", flat=True).distinct())
        missing_remote_ids = sorted(set(remote_ids) - existing_remote_ids)
        if not missing_remote_ids:
            return

        if tree_ids:
            raise ValidationError(
                {
                    field_name: _(
                        "Unknown eBay category remote IDs for this sales channel tree: %(ids)s"
                    )
                    % {"ids": ", ".join(missing_remote_ids)}
                }
            )

        raise ValidationError(
            {
                field_name: _(
                    "Unknown eBay category remote IDs: %(ids)s"
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
