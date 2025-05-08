from woocommerce import API
from django.conf import settings
from .exceptions import FailedToGetAttributesError, FailedToGetError, \
    FailedToGetAttributeError, FailedToGetAttributeTermsError, FailedToGetProductsError, \
    FailedToCreateAttributeError, FailedToPostError, FailedToDeleteError, \
    FailedToDeleteAttributeError, DuplicateError, FailedToUpdateAttributeError, \
    FailedToPutError

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WoocommerceApiWrapper:
    attribute_prefix = 'pa_'

    def __init__(self, *, api_key, api_secret, hostname, api_version, verify_ssl, timeout):
        self.api_key = api_key
        self.api_secret = api_secret
        self.hostname = hostname
        self.api_version = api_version
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.user_agent = settings.ONESILA_DEFAULT_USER_AGENT

        self.initialise_woocom()

    def initialise_woocom(self):
        """direct api call to woocommerce"""
        self.woocom = API(
            url=self.hostname,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            version=self.api_version,
            verify_ssl=self.verify_ssl,
            timeout=self.timeout,
            user_agent=self.user_agent
        )

    def remove_attribute_slug_prefix(self, attribute):
        """remove the attribute prefix from the attribute slug and return the attribute"""
        new_slug = attribute['slug'].replace(self.attribute_prefix, '')
        attribute['slug'] = new_slug
        return attribute

    def get_paged_get(self, endpoint, params=None):
        """get a paged response from woocommerce"""
        # FIXME: implement paged get
        pass

    def get(self, endpoint, params=None):
        resp = self.woocom.get(endpoint, params=params)
        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise FailedToGetError(e, response=resp) from e

    def post(self, endpoint, data=None):
        resp = self.woocom.post(endpoint, data=data)
        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if "already in use" in resp.text:
                raise DuplicateError(e, response=resp) from e
            raise FailedToPostError(e, response=resp) from e

    def put(self, endpoint, data=None):
        resp = self.woocom.put(endpoint, data=data)
        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise FailedToPutError(e, response=resp) from e

    def delete(self, endpoint, force=True):
        params = {}
        if force:
            params['force'] = True

        resp = self.woocom.delete(endpoint, params=params)
        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise FailedToDeleteError(e, response=resp) from e

    def get_attributes(self):
        try:
            return [self.remove_attribute_slug_prefix(attribute) for attribute in self.get('products/attributes')]
        except FailedToGetError as e:
            raise FailedToGetAttributesError(e, response=e.response) from e

    def get_attribute(self, attribute_id):
        try:
            return self.remove_attribute_slug_prefix(self.get(f'products/attributes/{attribute_id}'))
        except FailedToGetError as e:
            raise FailedToGetAttributeError(e, response=e.response) from e

    def get_attribute_by_code(self, attribute_code):
        for attribute in self.get_attributes():
            # We don't clean the slug here as the get_attribute function does this.
            slug = attribute['slug']
            if slug == attribute_code:
                return attribute
        raise FailedToGetAttributeError(f"Attribute with code {attribute_code} not found")

    def get_attribute_terms(self, attribute_id):
        try:
            return self.get(f'products/attributes/{attribute_id}/terms')
        except FailedToGetError as e:
            raise FailedToGetAttributeTermsError(e, response=e.response) from e

    def get_products(self):
        try:
            return self.get('products')
        except FailedToGetError as e:
            raise FailedToGetProductsError(e, response=e.response) from e

    def create_attribute(self, slug, name, has_archives=True, type='select'):
        payload = {
            'slug': self.attribute_prefix + slug,
            'name': name,
            'type': type,
            'has_archives': has_archives
        }
        try:
            return self.remove_attribute_slug_prefix(self.post('products/attributes', data=payload))
        except FailedToGetError as e:
            raise FailedToCreateAttributeError(e, response=e.response) from e

    def update_attribute(self, attribute_id, payload):
        try:
            return self.put(f'products/attributes/{attribute_id}', data=payload)
        except FailedToPutError as e:
            raise FailedToUpdateAttributeError(e, response=e.response) from e

    def delete_attribute(self, attribute_id):
        try:
            return self.delete(f'products/attributes/{attribute_id}')
        except FailedToGetError as e:
            raise FailedToDeleteAttributeError(e, response=e.response) from e
