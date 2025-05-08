class WoocommerceError(Exception):
    """
    Base exception class for all WooCommerce related errors.
    Handles JSON error responses from the WooCommerce API.
    """

    def __init__(self, message=None, response=None):
        self.response = response
        self.code = None
        self.message = message
        self.response_message = None
        self.response_status_code = None

        if self.response:
            json = self.response.json()
            self.code = json.get('code')
            self.response_message = json.get('message', message)
            self.response_status_code = self.response.status_code

        super().__init__(self.response_message if self.response_message else message)


class FailedToGetAttributesError(WoocommerceError):
    """
    Exception raised when the attributes are not retrieved from the WooCommerce API.
    """
    pass


class FailedToGetError(WoocommerceError):
    """
    Exception raised when the WooCommerce API returns a non-200 status code.
    """
    pass


class FailedToGetAttributeError(FailedToGetError):
    """
    Exception raised when the attribute is not retrieved from the WooCommerce API.
    """
    pass


class FailedToGetAttributeTermsError(FailedToGetError):
    """
    Exception raised when the attribute terms are not retrieved from the WooCommerce API.
    """
    pass


class FailedToGetProductsError(FailedToGetError):
    """
    Exception raised when the products are not retrieved from the WooCommerce API.
    """
    pass


class FailedToCreateAttributeError(FailedToGetError):
    """
    Exception raised when the attribute creation fails on the WooCommerce API.
    """
    pass


class FailedToPostError(WoocommerceError):
    """
    Exception raised when the WooCommerce API post request fails.
    """
    pass


class FailedToDeleteError(WoocommerceError):
    """
    Exception raised when the WooCommerce API delete request fails.
    """
    pass


class FailedToDeleteAttributeError(FailedToDeleteError):
    """
    Exception raised when the attribute deletion fails on the WooCommerce API.
    """
    pass


class FailedToPutError(WoocommerceError):
    """
    Exception raised when the WooCommerce API put request fails.
    """
    pass


class FailedToUpdateAttributeError(FailedToPutError):
    """
    Exception raised when the attribute update fails on the WooCommerce API.
    """
    pass


class DuplicateError(WoocommerceError):
    """
    Exception raised when trying to create an item that already exists.
    """
    pass
