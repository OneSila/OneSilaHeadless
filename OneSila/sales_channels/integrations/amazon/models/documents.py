from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from sales_channels.models.documents import RemoteDocumentType


class AmazonDocumentType(RemoteDocumentType):
    # NOTE for next iteration (Amazon document/certificate coverage):
    # 1) image_locator_**pf
    # 2) image_locator_ps** (currently PS01-PS06)
    # 3) safety_data_sheet_url
    # 4) compliance_media[*].content_type
    #
    # compliance_media content_type values discovered so far:
    # - application_guide
    # - certificate_of_analysis
    # - certificate_of_compliance
    # - compatibility_guide
    # - emergency_use_authorization
    # - emergency_use_authorization_amendment
    # - installation_manual
    # - instructions_for_use
    # - patient_fact_sheet
    # - provider_fact_sheet
    # - safety_data_sheet
    # - safety_information
    # - specification_sheet
    # - troubleshooting_guide
    # - user_guide
    # - user_manual
    # - warranty
    def _get_sales_channel_marketplace_ids(self) -> list[str]:
        if not self.sales_channel_id:
            return []

        from sales_channels.integrations.amazon.models.sales_channels import AmazonSalesChannelView

        marketplace_ids = (
            AmazonSalesChannelView.objects.filter(sales_channel_id=self.sales_channel_id)
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
            .values_list("remote_id", flat=True)
            .distinct()
        )
        return [str(marketplace_id).strip() for marketplace_id in marketplace_ids if str(marketplace_id).strip()]

    def _validate_category_remote_ids_exist(self, *, field_name: str, remote_ids: list[str]) -> None:
        if not remote_ids:
            return

        from sales_channels.integrations.amazon.models.recommended_browse_nodes import AmazonBrowseNode

        category_qs = AmazonBrowseNode.objects.filter(remote_id__in=remote_ids)
        marketplace_ids = self._get_sales_channel_marketplace_ids()
        if marketplace_ids:
            category_qs = category_qs.filter(marketplace_id__in=marketplace_ids)

        existing_remote_ids = set(category_qs.values_list("remote_id", flat=True).distinct())
        missing_remote_ids = sorted(set(remote_ids) - existing_remote_ids)
        if not missing_remote_ids:
            return

        if marketplace_ids:
            raise ValidationError(
                {
                    field_name: _(
                        "Unknown Amazon browse node remote IDs for this sales channel marketplaces: %(ids)s"
                    )
                    % {"ids": ", ".join(missing_remote_ids)}
                }
            )

        raise ValidationError(
            {
                field_name: _(
                    "Unknown Amazon browse node remote IDs: %(ids)s"
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
