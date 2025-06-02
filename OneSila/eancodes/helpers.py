from .country_list import EAN_COUNTRY_LIST
from .decorators import validation_method
from .exceptions import ValidationError
import logging
from django.utils.translation import gettext_lazy as _
logger = logging.getLogger(__name__)


class ValidatorErrorMesssages:
    EAN_IS_EMPTY = _(u"EAN is empty")
    EAN_IS_TOO_SHORT = _(u"EAN is too short")
    EAN_IS_TOO_LONG = _(u"EAN is too long")
    INVALID_COUNTRY_CODE = _(u"Invalid country code")
    INVALID_CHECKSUM = _(u"Invalid checksum. Non existing code")
    EAN_CONTAINS_NON_NUMERIC_CHARACTERS = _(u"EAN contains non-numeric characters")


class EANCodeValidator:
    """
    Validate the EAN-code.
    Original inspiration from: https://stackoverflow.com/a/51836010/5731101
    """

    def __init__(self, ean, fail_on_error=True):
        self.ean = ean
        self.errors = set()
        self.fail_on_error = fail_on_error

    @property
    def error_list(self):
        return list(self.errors)

    @validation_method
    def has_value(self):
        if self.ean is None or self.ean == "":
            msg = ValidatorErrorMesssages.EAN_IS_EMPTY
            return False, msg

        return True, None

    @validation_method
    def is_valid_length(self):
        try:
            if len(self.ean) < 13:
                msg = ValidatorErrorMesssages.EAN_IS_TOO_SHORT
                return False, msg

            if len(self.ean) > 13:
                msg = ValidatorErrorMesssages.EAN_IS_TOO_LONG
                return False, msg

            return True, None
        except TypeError:
            msg = ValidatorErrorMesssages.EAN_IS_EMPTY
            return False, msg

    @validation_method
    def validate_country_code(self):
        try:
            start_digits = self.ean[:3]
            if start_digits not in EAN_COUNTRY_LIST:
                msg = ValidatorErrorMesssages.INVALID_COUNTRY_CODE
                return False, msg
        except TypeError:
            msg = ValidatorErrorMesssages.EAN_IS_EMPTY
            return False, msg

        return True, None

    @validation_method
    def validate_checksum(self):
        try:
            start_digits = self.ean[:3]
            err = 0
            even = 0
            odd = 0
            # get check bit(last bit)
            check_bit = self.ean[len(self.ean) - 1]
            # Get all vals except check bit
            check_val = self.ean[:-1]

            # Gather Odd and Even Bits
            try:
                for index, num in enumerate(check_val):
                    if index % 2 == 0:
                        even += int(num)
                    else:
                        odd += int(num)
            except ValueError:
                msg = ValidatorErrorMesssages.EAN_CONTAINS_NON_NUMERIC_CHARACTERS
                return False, msg

            # Check if the algorithm 3 * odd parity + even parity + check bit matches
            bits_match = ((3 * odd) + even + int(check_bit)) % 10 == 0

            if not bits_match:
                msg = ValidatorErrorMesssages.INVALID_CHECKSUM
                return False, msg
        except IndexError:
            msg = ValidatorErrorMesssages.EAN_IS_TOO_SHORT
            return False, msg
        except TypeError:
            msg = ValidatorErrorMesssages.EAN_IS_EMPTY
            return False, msg

        return True, None

    def run(self):
        self.has_value()
        self.is_valid_length()
        self.validate_country_code()
        self.validate_checksum()

        return not self.errors, self.error_list
