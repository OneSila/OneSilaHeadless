import logging
from woocommerce import API
from django.conf import settings
from .exceptions import FailedToGetAttributesError, FailedToGetError, \
    FailedToGetAttributeError, FailedToGetAttributeTermsError, FailedToGetProductsError, \
    FailedToCreateAttributeError, FailedToPostError, FailedToDeleteError, \
    FailedToDeleteAttributeError, DuplicateError, FailedToUpdateAttributeError, \
    FailedToPutError, FailedToCreateAttributeTermError, FailedToUpdateAttributeTermError, \
    FailedToDeleteAttributeTermError, FailedToGetAttributeTermError, FailedToGetAttributeTermError, \
    FailedToCreateAttributeTermError, FailedToDeleteAttributeTermError, FailedToUpdateAttributeTermError, \
    FailedToGetStoreCurrencyError, FailedToGetProductError, FailedToGetProductBySkuError, FailedToCreateProductError, \
    FailedToUpdateProductError, FailedToDeleteProductError, FailedToGetStoreConfigError, \
    FailedToGetStoreLanguageError
from .constants import API_ATTRIBUTE_PREFIX
import urllib3
import requests
from copy import deepcopy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class WoocommerceApiWrapper:
    attribute_prefix = API_ATTRIBUTE_PREFIX

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

    def discover_next_page(self, resp):
        """discover the next page url from the response headers and
        return (True, url) or (False, None)"""
        link_headers = resp.headers.get('Link').split(', ')
        for lh in link_headers:
            url, rel = lh.split(';')
            if 'next' in rel:
                # url looks like this: "<https://example.com/wp-json/wc/v3/products?page=2>"
                # clean it up and only keep the endpoint.
                url = url.strip('>').strip('<')
                url = url.split(self.api_version)[1].lstrip('/')
                return True, url
        return False, None

    def get_paged_get(self, endpoint, params={}):
        """get a paged response from woocommerce"""
        data = []
        resp = self.get(endpoint, params=params, return_json=False)
        data.extend(resp.json())

        has_next, next_url = self.discover_next_page(resp)
        while has_next:
            resp = self.get(next_url, params=params, return_json=False)
            has_next, next_url = self.discover_next_page(resp)
            data.extend(resp.json())

        return data

    def get(self, endpoint, params=None, return_json=True):
        resp = self.woocom.get(endpoint, params=params)
        try:
            resp.raise_for_status()
            if return_json:
                return resp.json()
            else:
                return resp
        except Exception as e:
            raise FailedToGetError(e, response=resp) from e

    def post(self, endpoint, data=None):
        logger.debug(f"POSTing to {endpoint} with data: {data}")
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

    def delete(self, endpoint):
        # Why force?  https://docs.woocommerce.com/rest-api-reference/products/delete-a-product/
        # We want to bypass trash and permanently delete the instance.
        params = {'force': True}

        resp = self.woocom.delete(endpoint, params=params)
        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise FailedToDeleteError(e, response=resp) from e

    def get_attributes(self):
        try:
            return [self.remove_attribute_slug_prefix(attribute) for attribute in self.get_paged_get('products/attributes')]
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
            return self.get_paged_get(f'products/attributes/{attribute_id}/terms')
        except FailedToGetError as e:
            raise FailedToGetAttributeTermsError(e, response=e.response) from e

    def create_attribute(self, slug, name, has_archives=True, type='select'):
        payload = {
            'slug': self.attribute_prefix + slug,
            'name': name,
            'type': type,
            'has_archives': has_archives
        }
        try:
            resp = self.remove_attribute_slug_prefix(self.post('products/attributes', data=payload))
            logger.debug(f"Created woocommerce attribute: {resp}")
            return resp
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

    def get_attribute_term(self, attribute_id, value_id):
        try:
            return self.get(f'products/attributes/{attribute_id}/terms/{value_id}')
        except FailedToGetError as e:
            raise FailedToGetAttributeTermError(e, response=e.response) from e

    def get_attribute_term_by_name(self, attribute_id, name):
        for value in self.get_attribute_terms(attribute_id):
            if value['name'] == name:
                return value
        raise FailedToGetAttributeTermError(f"Attribute value with name {name} not found")

    def create_attribute_term(self, attribute_id, name, slug=None):
        payload = {
            'name': name,
        }

        if slug:
            payload['slug'] = slug

        try:
            return self.post(f'products/attributes/{attribute_id}/terms', data=payload)
        except FailedToPostError as e:
            # It's likely that the value already exists.  We should go and get it.
            # before raising and error
            try:
                return self.get_attribute_term_by_name(attribute_id, name)
            except FailedToGetAttributeTermError:
                # Return from original error since that's what actually matters.
                raise FailedToCreateAttributeTermError(e, response=e.response) from e

    def update_attribute_value(self, attribute_id, value_id, name, slug=None):
        payload = {
            'name': name,
        }

        if slug:
            payload['slug'] = slug

        try:
            return self.put(f'products/attributes/{attribute_id}/terms/{value_id}', data=payload)
        except FailedToPutError as e:
            raise FailedToUpdateAttributeTermError(e, response=e.response) from e

    def delete_attribute_term(self, attribute_id, value_id):
        try:
            return self.delete(f'products/attributes/{attribute_id}/terms/{value_id}')
        except FailedToDeleteError as e:
            raise FailedToDeleteAttributeTermError(e, response=e.response) from e

    def get_products(self):
        try:
            return self.get_paged_get('products')
        except FailedToGetError as e:
            raise FailedToGetProductsError(e, response=e.response) from e

    def get_product(self, product_id):
        try:
            return self.get(f'products/{product_id}')
        except FailedToGetError as e:
            raise FailedToGetProductError(e, response=e.response) from e

    def get_product_by_sku(self, sku):
        try:
            return self.get(f'products?sku={sku}')[0]
        except IndexError as e:
            raise FailedToGetProductBySkuError(e) from e

    def _convert_price_to_string(self, price):
        if price is None:
            return None
        return str(price)

    def create_product(self, name, type, sku, status, catalog_visibility, regular_price, sale_price=None, description='', short_description='', categories=[], images=[], attributes=[]):
        """
        Create a product in WooCommerce.
        """
        payload = {
            'name': name,
            'type': type,
            'sku': sku,
            'status': status,
            'catalog_visibility': catalog_visibility,
            'regular_price': self._convert_price_to_string(regular_price),
            'sale_price': self._convert_price_to_string(sale_price),
            'description': description,
            'short_description': short_description,
            'categories': categories,
            'images': images,
            'attributes': attributes,
        }
        for k, v in deepcopy(payload).items():
            if v is None or v == []:
                del payload[k]

        logger.debug(f"Create Product Payload: {payload}")

        try:
            return self.post('products', data=payload)
        except FailedToPostError as e:
            # It seems duplicates are raised as 400 errors.
            try:
                self.get_product_by_sku(sku)
                raise DuplicateError(e, response=e.response) from e
            except FailedToGetProductBySkuError:
                pass

            raise FailedToCreateProductError(e, response=e.response) from e

    def create_product_variation(self, product_id, **payload):
        """
        Create a product variation in WooCommerce.
        """
        fields_to_convert_to_string = ['regular_price', 'sale_price']
        for key in payload.keys():
            if key in fields_to_convert_to_string:
                payload[key] = self._convert_price_to_string(payload[key])

        logger.debug(f"Create Product Variation Payload: {payload}")
        return self.post(f'products/{product_id}/variations', data=payload)

    def update_product_variation(self, product_id, variation_id, **payload):
        """
        Update a product variation in WooCommerce.
        """
        fields_to_convert_to_string = ['regular_price', 'sale_price']
        for key in payload.keys():
            if key in fields_to_convert_to_string:
                payload[key] = self._convert_price_to_string(payload[key])
        return self.put(f'products/{product_id}/variations/{variation_id}', data=payload)

    def delete_product_variation(self, product_id, variation_id):
        """
        Delete a product variation in WooCommerce.
        """
        return self.delete(f'products/{product_id}/variations/{variation_id}')

    def update_product(self, product_id, **payload):
        fields_to_update = ['name', 'type', 'sku', 'status', 'catalog_visibility', 'regular_price',
            'sale_price', 'description', 'short_description', 'categories', 'images', 'attributes']
        for key in payload.keys():
            if key not in fields_to_update:
                raise ValueError(f"Field {key} is not updateable")

        for k, v in payload.items():
            if k in ['regular_price', 'sale_price']:
                payload[k] = self._convert_price_to_string(v)

        logger.debug(f"Update Payload: {payload}")
        try:
            return self.put(f'products/{product_id}', data=payload)
        except FailedToPutError as e:
            raise FailedToUpdateProductError(e, response=e.response) from e

    def delete_product(self, product_id):
        try:
            return self.delete(f'products/{product_id}')
        except FailedToDeleteError as e:
            raise FailedToDeleteProductError(e, response=e.response) from e

    def get_from_settings(self, key):
        """
        Get a setting from the WooCommerce settings.
        """
        for i in self.get('settings/general'):
            if i['id'] == key:
                return i['default']
        raise ValueError(f"Setting with key {key} not found")

    def get_store_currency(self):
        """
        Get the configured currency for the store.
        """
        key = 'woocommerce_currency'
        try:
            return self.get_from_settings(key)
        except ValueError:
            raise FailedToGetStoreCurrencyError(f"Currency not found for key {key}")

    def get_store_config(self):
        """
        Get the name of the store.
        """
        resp = requests.get(f"{self.hostname}/wp-json")
        if resp.ok:
            resp_data = resp.json()
            return {
                'name': resp_data['name'],
                'url': resp_data['url'],
            }
        else:
            raise FailedToGetStoreConfigError(f"Failed to get store config: {resp.status_code}")

    def get_store_language(self):
        """
        Get the language configured for the store.
        """
        # FIXME: This is a poor way to detect language.
        # Instead, we should gain access to the wordpress application password
        # and use the wordpress api instead of the woocom api.
        # GET https://example.com/wp-json/wp/v2/settings
        # and look for a language

        key = 'woocommerce_default_country'
        try:
            value = self.get_from_settings(key)
            country = value.split(':')[0]

            if country in ['GB', 'US', 'CA', 'AU', 'NZ']:
                return f'en_{country}'
            elif country in ['DE', 'AT', 'CH']:
                return 'de_DE'
            elif country in ['FR', 'LU', 'CH']:
                return 'fr_FR'
            elif country in ['ES']:
                return 'es_ES'
            elif country in ['IT']:
                return 'it_IT'
            elif country in ['NL', 'BE']:
                return 'nl_NL'
            elif country in ['PL']:
                return 'pl_PL'
            elif country in ['PT']:
                return 'pt_PT'
            elif country in ['RO']:
                return 'ro_RO'
            else:
                raise FailedToGetStoreLanguageError(f"Language not found for key {key}")
        except ValueError:
            raise FailedToGetStoreLanguageError(f"Language not found for key {key}")
