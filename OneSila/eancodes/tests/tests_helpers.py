from core.tests import TestCase
from eancodes.helpers import EANCodeValidator
from eancodes.exceptions import ValidationError


class TestEANCodeValidator(TestCase):
    def test_empty_full_run(self):
        validator = EANCodeValidator("", fail_on_error=False)
        resp, errors = validator.run()
        self.assertFalse(resp)
        self.assertTrue(len(errors) > 0)

    def test_none_full_run(self):
        validator = EANCodeValidator(None, fail_on_error=False)
        resp, errors = validator.run()
        self.assertFalse(resp)
        self.assertTrue(len(errors) > 0)

    def test_has_value(self):
        validator = EANCodeValidator("", fail_on_error=False)
        self.assertEqual(validator.has_value()[0], False)

    def test_is_valid_length(self):
        validator = EANCodeValidator("1234567890123", fail_on_error=False)
        self.assertEqual(validator.is_valid_length()[0], True)

    def test_validate_country_code(self):
        # Using range 205 from the internal restricted range.
        validator = EANCodeValidator("2054567890123", fail_on_error=False)
        self.assertEqual(validator.validate_country_code()[0], False)

    def test_validate_checksum(self):
        validator = EANCodeValidator("1234567890123", fail_on_error=False)
        self.assertEqual(validator.validate_checksum()[0], False)

    def test_run_fail_on_error_false(self):
        validator = EANCodeValidator("2044567890123", fail_on_error=False)
        self.assertTrue(len(validator.run()[1]) > 0)

    def test_run_fail_on_error(self):
        validator = EANCodeValidator("1234567890123", fail_on_error=True)
        with self.assertRaises(ValidationError):
            validator.run()

    def test_valid_ean(self):
        validator = EANCodeValidator("5055988625672", fail_on_error=False)
        resp, errors = validator.run()
        self.assertTrue(resp)
        self.assertEqual(errors, [])

    def test_valid_ean_fail_on_error(self):
        validator = EANCodeValidator("5055988625672", fail_on_error=True)
        resp, errors = validator.run()
        self.assertTrue(resp)
        self.assertEqual(errors, [])

    def test_messed_up_format(self):
        validator = EANCodeValidator("5051090-002226", fail_on_error=False)
        resp, errors = validator.run()
        self.assertFalse(resp)
        self.assertTrue(len(errors) > 0)

    def test_messed_up_format_fail_on_error(self):
        validator = EANCodeValidator("5051090-002226", fail_on_error=True)
        with self.assertRaises(ValidationError):
            validator.run()
