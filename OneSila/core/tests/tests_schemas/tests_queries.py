from strawberry.relay import from_base64, to_base64
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from model_bakery import baker
from core.models import MultiTenantCompany
from strawberry_django.test.client import TestClient
from django.urls import reverse_lazy

from .mutations import LOGOUT_MUTATION, ME_QUERY


class TransactionTestCaseMixin:
    def setUp(self):
        self.multi_tenant_company = baker.make(MultiTenantCompany)
        self.user = baker.make(get_user_model(), multi_tenant_company=self.multi_tenant_company)

    def to_global_id(self, *, instance):
        type_name = f"{instance.__class__.__name__}Type"
        return to_base64(type_name, instance.id)

    def strawberry_raw_client(self):
        return TestClient('/graphql/')

    def strawberry_test_client(self, asserts_errors=False, **kwargs):
        test_client = TestClient('/graphql/')
        with test_client.login(self.user):
            return test_client.query(asserts_errors=asserts_errors, **kwargs)

    def strawberry_anonymous_test_client(self, **kwargs):
        test_client = TestClient('/graphql/')
        return test_client.query(asserts_errors=False, **kwargs)


class TestCountryQuery(TransactionTestCaseMixin, TransactionTestCase):
    def test_countries(self):
        query = """
            query countries{
              countries{
                code
                name
              }
            }
        """
        resp = self.strawberry_anonymous_test_client(
            query=query)

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)


class TestLanguageQuery(TransactionTestCaseMixin, TransactionTestCase):
    def test_languages(self):
        query = """
            query languages{
              languages{
                code
                name
                nameLocal
                nameTranslated
              }
            }
        """

        # Make sure you are logged out first.  The test-client is
        # logged in by default.
        # resp = self.strawberry_anonymous_test_client(query=ME_QUERY)
        # self.assertTrue(resp.errors is not None)

        resp = self.strawberry_anonymous_test_client(
            query=query)

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

    def test_default_language(self):
        query = """
            query defaultLanguage{
              defaultLanguage{
                code
                name
                bidi
              }
            }
        """

        resp = self.strawberry_anonymous_test_client(
            query=query)

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

    def test_current_lang(self):
        query = """
            query currentUserLanguage{
                currentUserLanguage{
                    code
                    name
                    bidi
                }
            }
        """
        resp = self.strawberry_test_client(
            query=query)

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)


class TestTimeZoneQuery(TransactionTestCaseMixin, TransactionTestCase):
    def test_languages(self):
        query = """
            query timezones{
              timezones{
                key
              }
            }
        """

        # Make sure you are logged out first.  The test-client is
        # logged in by default.
        # resp = self.strawberry_anonymous_test_client(query=ME_QUERY)
        # self.assertTrue(resp.errors is not None)

        resp = self.strawberry_anonymous_test_client(
            query=query)

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

    def test_default_timezone(self):
        query = """
            query defaultTimezone{
              defaultTimezone{
                key
              }
            }
        """

        resp = self.strawberry_anonymous_test_client(
            query=query)

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

    def test_current_user_timezone(self):
        query = """
            query currentUserTimezone{
                currentUserTimezone{
                    key
                }
            }
        """
        resp = self.strawberry_test_client(
            query=query)

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)
