class WoocommerceError(Exception):
    """
    Base exception class for all WooCommerce related errors.
    Handles JSON error responses from the WooCommerce API.
    """

    def __init__(self, message=None, response=None, extra_msg=None):
        self.response = response
        self.code = None
        self.message = message
        self.response_message = None
        self.response_status_code = None
        self.extra_msg = extra_msg

        try:
            json = response.json()
            self.code = json.get('code')
            self.response_message = json.get('message', message)
            self.response_status_code = self.response.status_code
        except AttributeError:
            self.response_message = message

        if self.extra_msg:
            self.response_message += f" {self.extra_msg}"

        super().__init__(self.response_message)


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


class FailedToCreateAttributeTermError(FailedToPostError):
    """
    Exception raised when the attribute value creation fails on the WooCommerce API.
    """
    pass


class FailedToUpdateAttributeTermError(FailedToPutError):
    """
    Exception raised when the attribute value update fails on the WooCommerce API.
    """
    pass


class FailedToDeleteAttributeTermError(FailedToDeleteError):
    """
    Exception raised when the attribute value deletion fails on the WooCommerce API.
    """
    pass


class FailedToGetAttributeTermError(FailedToGetError):
    """
    Exception raised when the attribute value is not retrieved from the WooCommerce API.
    """
    pass


class FailedToGetProductBySkuError(FailedToGetError):
    """
    Exception raised when the product by SKU is not retrieved from the WooCommerce API.
    """
    pass


class FailedToCreateProductError(FailedToPostError):
    """
    Exception raised when the product creation fails on the WooCommerce API.
    """
    pass


class FailedToUpdateProductError(FailedToPutError):
    """
    Exception raised when the product update fails on the WooCommerce API.
    """
    pass


class FailedToDeleteProductError(FailedToDeleteError):
    """
    Exception raised when the product deletion fails on the WooCommerce API.
    """
    pass


class FailedToGetStoreCurrencyError(FailedToGetError):
    """
    Exception raised when the store currency is not retrieved from the WooCommerce API.
    """
    pass


class FailedToGetProductError(FailedToGetError):
    """
    Exception raised when the product is not retrieved from the WooCommerce API.
    """
    pass


class FailedToGetStoreConfigError(FailedToGetError):
    """
    Exception raised when the store name is not retrieved from the WooCommerce API.
    """
    pass


class FailedToGetStoreLanguageError(FailedToGetError):
    """
    Exception raised when the store languages are not retrieved from the WooCommerce API.
    """
    pass


class ProductNotFoundError(FailedToUpdateProductError):
    """
    Exception raised when the product is not found on the WooCommerce API.
    """
    pass


class InternalWoocomPostError(Exception):
    """Used if woocom failed to post throught the actual package."""
    pass


class NoneValueNotAllowedError(Exception):
    """
    Exception raised when a None value is not allowed.
    """
    pass
