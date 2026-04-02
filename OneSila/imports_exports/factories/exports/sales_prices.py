from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem

from .helpers import build_product_stub, filter_queryset_by_ids, to_bool
from .mixins import AbstractExportFactory


def build_sales_pricelist_stub(*, sales_pricelist):
    return {
        "name": sales_pricelist.name,
        "currency": sales_pricelist.currency.iso_code,
        "start_date": sales_pricelist.start_date,
        "end_date": sales_pricelist.end_date,
    }


class SalesPricesExportFactory(AbstractExportFactory):
    kind = "sales_prices"
    supported_columns = (
        "rrp",
        "price",
        "currency",
        "product_data",
        "product_sku",
    )
    default_columns = (
        "rrp",
        "price",
        "currency",
        "product_data",
    )

    def get_queryset(self):
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))
        product_ids = self.normalize_ids(value=self.get_parameter(key="product"))

        queryset = SalesPrice.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).select_related(
            "product",
            "currency",
        )
        queryset = filter_queryset_by_ids(queryset=queryset, ids=ids)
        if product_ids:
            queryset = queryset.filter(product_id__in=product_ids)

        return queryset.order_by("product_id", "currency__iso_code")

    def get_payload(self):
        include_product_sku = self.include_column(key="product_sku") or to_bool(
            value=self.get_parameter(key="add_product_sku"),
        )
        include_product_data = self.include_column(key="product_data")
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)

        payload = []
        for index, sales_price in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            row = {
                "currency": sales_price.currency.iso_code,
            }
            if self.include_column(key="rrp"):
                row["rrp"] = sales_price.rrp
            if self.include_column(key="price"):
                row["price"] = sales_price.price
            if include_product_data:
                row["product_data"] = build_product_stub(product=sales_price.product)
            if include_product_sku:
                row["product_sku"] = sales_price.product.sku
            payload.append(row)
            self.update_progress(processed=index, total_records=total_records)
        return payload


class PriceListsExportFactory(AbstractExportFactory):
    kind = "price_lists"
    supported_columns = (
        "name",
        "start_date",
        "end_date",
        "currency",
        "vat_included",
        "auto_update_prices",
        "auto_add_products",
        "price_change_pcnt",
        "discount_pcnt",
        "notes",
        "sales_pricelist_items",
    )
    default_columns = (
        "name",
        "start_date",
        "end_date",
        "currency",
        "vat_included",
        "auto_update_prices",
        "auto_add_products",
        "price_change_pcnt",
        "discount_pcnt",
        "notes",
    )

    def get_queryset(self):
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))
        queryset = SalesPriceList.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).select_related(
            "currency",
        ).prefetch_related(
            "salespricelistitem_set__product",
        )
        return filter_queryset_by_ids(queryset=queryset, ids=ids).order_by("id")

    def serialize_item(self, *, item):
        return {
            "product_data": build_product_stub(product=item.product),
            "price_auto": item.price_auto,
            "discount_auto": item.discount_auto,
            "price_override": item.price_override,
            "discount_override": item.discount_override,
        }

    def get_payload(self):
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)
        payload = []
        for index, sales_pricelist in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            row = {
                "name": sales_pricelist.name,
                "currency": sales_pricelist.currency.iso_code,
            }
            if self.include_column(key="start_date"):
                row["start_date"] = sales_pricelist.start_date
            if self.include_column(key="end_date"):
                row["end_date"] = sales_pricelist.end_date
            if self.include_column(key="vat_included"):
                row["vat_included"] = sales_pricelist.vat_included
            if self.include_column(key="auto_update_prices"):
                row["auto_update_prices"] = sales_pricelist.auto_update_prices
            if self.include_column(key="auto_add_products"):
                row["auto_add_products"] = sales_pricelist.auto_add_products
            if self.include_column(key="price_change_pcnt"):
                row["price_change_pcnt"] = sales_pricelist.price_change_pcnt
            if self.include_column(key="discount_pcnt"):
                row["discount_pcnt"] = sales_pricelist.discount_pcnt
            if self.include_column(key="notes"):
                row["notes"] = sales_pricelist.notes
            if self.include_column(key="sales_pricelist_items"):
                row["sales_pricelist_items"] = [
                    self.serialize_item(item=item)
                    for item in sales_pricelist.salespricelistitem_set.all()
                ]
            payload.append(row)
            self.update_progress(processed=index, total_records=total_records)
        return payload


class PriceListPricesExportFactory(AbstractExportFactory):
    kind = "price_list_prices"
    supported_columns = (
        "price_auto",
        "discount_auto",
        "price_override",
        "discount_override",
        "product_data",
        "product_sku",
        "salespricelist_data",
        "salespricelist_name",
    )
    default_columns = (
        "price_auto",
        "discount_auto",
        "price_override",
        "discount_override",
        "product_data",
        "salespricelist_data",
    )

    def get_queryset(self):
        ids = self.normalize_ids(value=self.get_parameter(key="ids"))
        product_ids = self.normalize_ids(value=self.get_parameter(key="product"))
        sales_pricelist_ids = self.normalize_ids(value=self.get_parameter(key="salespricelist"))

        queryset = SalesPriceListItem.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
        ).select_related(
            "product",
            "salespricelist",
            "salespricelist__currency",
        )
        queryset = filter_queryset_by_ids(queryset=queryset, ids=ids)
        if product_ids:
            queryset = queryset.filter(product_id__in=product_ids)
        if sales_pricelist_ids:
            queryset = queryset.filter(salespricelist_id__in=sales_pricelist_ids)
        return queryset.order_by("salespricelist_id", "product_id")

    def get_payload(self):
        include_product_sku = self.include_column(key="product_sku") or to_bool(
            value=self.get_parameter(key="add_product_sku"),
        )
        include_sales_pricelist_name = self.include_column(key="salespricelist_name")
        queryset = self.get_queryset()
        total_records = self.track_queryset(queryset=queryset)

        payload = []
        for index, item in enumerate(self.iterate_queryset(queryset=queryset), start=1):
            row = {}
            if self.include_column(key="price_auto"):
                row["price_auto"] = item.price_auto
            if self.include_column(key="discount_auto"):
                row["discount_auto"] = item.discount_auto
            if self.include_column(key="price_override"):
                row["price_override"] = item.price_override
            if self.include_column(key="discount_override"):
                row["discount_override"] = item.discount_override
            if self.include_column(key="product_data"):
                row["product_data"] = build_product_stub(product=item.product)
            if include_product_sku:
                row["product_sku"] = item.product.sku
            if self.include_column(key="salespricelist_data"):
                row["salespricelist_data"] = build_sales_pricelist_stub(
                    sales_pricelist=item.salespricelist,
                )
            if include_sales_pricelist_name:
                row["salespricelist_name"] = item.salespricelist.name
            payload.append(row)
            self.update_progress(processed=index, total_records=total_records)
        return payload

