from eancodes.models import EanCode


class GenerateEancodesFactory:
    def __init__(self, *, prefix, multi_tenant_company):
        self.ean_code_instances = None
        self.prefix = prefix
        self.multi_tenant_company = multi_tenant_company

    def set_ean_codes(self):
        """Generate all possible EAN codes based on the given prefix."""
        self.ean_codes = []
        base_length = len(self.prefix)
        num_fill = 13 - base_length

        if num_fill == 0:
            self.ean_codes.append(self.prefix)
            return

        for i in range(10**num_fill):
            suffix = str(i).zfill(num_fill)
            full_ean_code = f"{self.prefix}{suffix}"
            self.ean_codes.append(full_ean_code)

    def generate_eancodes(self):
        ean_code_instances = [EanCode(ean_code=ean_code, multi_tenant_company=self.multi_tenant_company) for ean_code in self.ean_codes]
        self.ean_code_instances = EanCode.objects.bulk_create(ean_code_instances)

    def run(self):
        self.set_ean_codes()
        self.generate_eancodes()