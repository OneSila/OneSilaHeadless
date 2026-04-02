from eancodes.models import EanCode

from .helpers import filter_queryset_by_ids, to_bool
from .mixins import AbstractExportFactory


class EanCodesExportFactory(AbstractExportFactory):
    kind = "ean_codes"
    supported_columns = (
        "ean_code",
        "product_sku",
    )
    default_columns = (
        "ean_code",
        "product_sku",
    )

    def get_queryset(self):
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))
        product_ids = self.normalize_ids(value=self.get_parameter(key="product"))

        queryset = EanCode.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).select_related("product")
        queryset = filter_queryset_by_ids(queryset=queryset, ids=ids)
        if product_ids:
            queryset = queryset.filter(product_id__in=product_ids)

        return queryset.order_by("id")

    def get_payload(self):
        include_product_sku = self.include_column(key="product_sku") or to_bool(
            value=self.get_parameter(key="add_product_sku"),
            default=True,
        )
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)

        payload = []
        for index, ean_code in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            row = {
                "ean_code": ean_code.ean_code,
            }
            if include_product_sku and ean_code.product_id:
                row["product_sku"] = ean_code.product.sku
            payload.append(row)
            self.update_progress(processed=index, total_records=total_records)
        return payload
