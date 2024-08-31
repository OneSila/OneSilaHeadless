from eancodes.models import EanCode
from functools import reduce


class GenerateEancodesFactory:
    def __init__(self, *, prefix, multi_tenant_company):
        self.ean_code_instances = None
        self.prefix = prefix
        self.multi_tenant_company = multi_tenant_company

    def calculate_checksum(self, ean):
        """
        Calculates the checksum for an EAN13.
        @param str ean: String of 12 numbesrs
        :returns: The checksum for `ean`.
        :rtype: Integer
        """
        ean_list = [int(digit) for digit in ean]
        assert len(ean_list) == 12, "EAN must be a list of 12 numbers"
        def sum_(x, y): return int(x) + int(y)
        evensum = reduce(sum_, ean_list[::2])
        oddsum = reduce(sum_, ean_list[1::2])
        return (10 - ((evensum + oddsum * 3) % 10)) % 10

    def set_ean_codes(self):
        """Generate all possible EAN codes based on the given prefix."""
        self.ean_codes = []
        base_length = len(self.prefix)
        num_fill = 12 - base_length

        if num_fill < 0:
            raise ValueError("Prefix length is too long. It must allow for at least one fill digit.")

        if num_fill == 0:
            check_digit = self.calculate_checksum(self.prefix)
            full_ean_code = f"{self.prefix}{check_digit}"
            self.ean_codes.append(full_ean_code)
            return

        for i in range(10**num_fill):
            suffix = str(i).zfill(num_fill)
            partial_ean_code = f"{self.prefix}{suffix}"
            check_digit = self.calculate_checksum(partial_ean_code)
            full_ean_code = f"{partial_ean_code}{check_digit}"
            self.ean_codes.append(full_ean_code)

    def generate_eancodes(self):
        ean_code_instances = [EanCode(ean_code=ean_code, multi_tenant_company=self.multi_tenant_company) for ean_code in self.ean_codes]
        self.ean_code_instances = EanCode.objects.bulk_create(ean_code_instances)

    def run(self):
        self.set_ean_codes()
        self.generate_eancodes()
