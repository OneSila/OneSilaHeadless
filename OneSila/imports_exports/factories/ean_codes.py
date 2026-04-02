from eancodes.models import EanCode
from imports_exports.factories.mixins import AbstractImportInstance
from products.models import Product


class ImportEanCodeInstance(AbstractImportInstance):
    def __init__(self, data: dict, import_process=None, product=None, instance=None):
        super().__init__(data, import_process, instance)
        self.product = product

        self.set_field_if_exists("ean_code")
        self.set_field_if_exists("product_sku")
        self.set_field_if_exists("product_data")
        self.set_field_if_exists("internal")
        self.set_field_if_exists("already_used")

        if self.product is None and hasattr(self, "product_data") and isinstance(self.product_data, dict):
            self.product_sku = self.product_data.get("sku") or getattr(self, "product_sku", None)

        self.validate()

    @property
    def local_class(self):
        return EanCode

    @property
    def updatable_fields(self):
        return ["ean_code", "internal", "already_used"]

    def validate(self):
        if not hasattr(self, "ean_code") or not self.ean_code:
            raise ValueError("The 'ean_code' field is required.")

        if not self.product and not getattr(self, "product_sku", None):
            raise ValueError("Either 'product' or 'product_sku'/'product_data.sku' must be provided.")

    def pre_process_logic(self):
        if self.product is None and getattr(self, "product_sku", None):
            self.product = Product.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                sku=self.product_sku,
            ).first()

    def process_logic(self):
        if self.product is None:
            self.instance = None
            return

        existing_for_product = EanCode.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
        ).first()

        if existing_for_product:
            self.instance = existing_for_product
        else:
            existing_for_code = EanCode.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                ean_code=self.ean_code,
            ).first()
            if existing_for_code:
                self.instance = existing_for_code
                self.instance.product = self.product
            else:
                self.instance = EanCode(
                    multi_tenant_company=self.multi_tenant_company,
                    product=self.product,
                )

        self.instance.ean_code = self.ean_code
        self.instance.internal = getattr(self, "internal", False)
        self.instance.already_used = getattr(self, "already_used", True)
        self.instance.save()
