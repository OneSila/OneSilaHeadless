from core.tests import TestCase
from eancodes.factories.generate_eancodes import GenerateEancodesFactory
from eancodes.models import EanCode


class GenerateEancodesFactoryTestCase(TestCase):

    def test_generate_eancodes_with_12_digit_prefix(self):
        """
        Test EAN code generation with a 12-digit prefix.
        """
        prefix = "123456789012"
        factory = GenerateEancodesFactory(prefix=prefix, multi_tenant_company=self.multi_tenant_company)
        factory.run()

        # Retrieve all generated EAN codes from the database
        ean_codes = EanCode.objects.filter(multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(len(ean_codes), 1, "Should generate exactly one EAN code.")
        ean_code = ean_codes.first().ean_code

        # Verify the EAN code length
        self.assertEqual(len(ean_code), 13, "The generated EAN code should have 13 digits.")

        # Verify the prefix and checksum
        self.assertTrue(ean_code.startswith(prefix), "The EAN code should start with the given prefix.")
        self.assertEqual(ean_code, "1234567890128", "The EAN code generated should be 1234567890128 - check digit is 8")

    def test_generate_eancodes_with_11_digit_prefix(self):
        """
        Test EAN code generation with an 11-digit prefix.
        """
        prefix = "12345678901"
        factory = GenerateEancodesFactory(prefix=prefix, multi_tenant_company=self.multi_tenant_company)
        factory.run()

        ean_codes = EanCode.objects.filter(multi_tenant_company=self.multi_tenant_company)

        self.assertEqual(len(ean_codes), 10, "Should generate exactly ten EAN codes.")

        # Verify each EAN code length and prefix
        for ean_code_instance in ean_codes:
            ean_code = ean_code_instance.ean_code
            self.assertEqual(len(ean_code), 13, "The generated EAN code should have 13 digits.")
            self.assertTrue(ean_code.startswith(prefix), "The EAN code should start with the given prefix.")
            self.assertEqual(ean_code[-1], str(factory.calculate_checksum(ean_code[:-1])), "The EAN code should have a correct checksum.")
