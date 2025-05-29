from .country_list import EAN_COUNTRY_LIST
from .decorators import validation_method
from .exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)


class EANCodeValidator:
    """
    Validate the EAN-code.
    Original inspiration from: https://stackoverflow.com/a/51836010/5731101
    """

    def __init__(self, ean, fail_on_error=True):
        self.ean = ean
        self.errors = []
        self.fail_on_error = fail_on_error

    @validation_method
    def has_value(self):
        if self.ean is None or self.ean == "":
            msg = "EAN is empty"
            return False, msg

        return True, None

    @validation_method
    def is_valid_length(self):
        if len(self.ean) < 13:
            msg = "EAN is too short"
            return False, msg

        if len(self.ean) > 13:
            msg = "EAN is too long"
            return False, msg

        return True, None

    @validation_method
    def validate_country_code(self):
        start_digits = self.ean[:3]
        if start_digits not in EAN_COUNTRY_LIST:
            msg = "Invalid country code"
            return False, msg

        return True, None

    @validation_method
    def validate_checksum(self):
        start_digits = self.ean[:3]
        err = 0
        even = 0
        odd = 0
        # get check bit(last bit)
        check_bit = self.ean[len(self.ean) - 1]
        # Get all vals except check bit
        check_val = self.ean[:-1]

        # Gather Odd and Even Bits
        for index, num in enumerate(check_val):
            if index % 2 == 0:
                even += int(num)
            else:
                odd += int(num)

        # Check if the algorithm 3 * odd parity + even parity + check bit matches
        bits_match = ((3 * odd) + even + int(check_bit)) % 10 == 0

        if not bits_match:
            msg = "Invalid checksum"
            return False, msg

        return True, None

    def run(self):
        self.has_value()
        self.is_valid_length()
        self.validate_country_code()
        self.validate_checksum()
        return self.errors


def gtin_is_valid(ean):
    # Verify the correctness of an ean13 / gtin code
    # https://stackoverflow.com/a/51836010/5731101

    logger.debug(f"Rejecting gtin. Bits match is {bits_match} and Valid Start digits are {valid_start_digits}.")
    return False
