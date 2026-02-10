from strawberry.relay import from_base64, to_base64
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from model_bakery import baker
from core.models import MultiTenantCompany
from strawberry_django.test.client import TestClient
from django.urls import reverse_lazy
from django.conf import settings
from django.utils.translation import get_language_info

from .mutations import LOGOUT_MUTATION, ME_QUERY


class TransactionTestCaseMixin:
    def setUp(self):
        self.multi_tenant_company = baker.make(MultiTenantCompany)
        self.user = baker.make(get_user_model(), multi_tenant_company=self.multi_tenant_company)

    def to_global_id(self, instance):
        type_name = f"{instance.__class__.__name__}Type"
        return to_base64(type_name, instance.id)

    def from_global_id(self, global_id):
        return from_base64(global_id)

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

    def test_company_content_views(self):
        from sales_channels.integrations.amazon.models import AmazonSalesChannel
        from sales_channels.integrations.shopify.models import ShopifySalesChannel

        language_codes = [code for code, _ in settings.LANGUAGES[:2]]
        self.assertTrue(len(language_codes) >= 1)
        self.multi_tenant_company.language = language_codes[0]
        self.multi_tenant_company.languages = language_codes
        self.multi_tenant_company.save(update_fields=["language", "languages"])
        self.user.language = language_codes[0]
        self.user.save(update_fields=["language"])

        amazon_channel = AmazonSalesChannel.objects.create(
            hostname="My Amazon Store",
            multi_tenant_company=self.multi_tenant_company,
        )
        shopify_channel = ShopifySalesChannel.objects.create(
            hostname="https://www.shop.example.com",
            multi_tenant_company=self.multi_tenant_company,
        )

        query = """
            query companyContentViews {
              companyContentViews {
                key
                name
              }
            }
        """
        resp = self.strawberry_test_client(query=query)
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        result = {
            item["key"]: item["name"]
            for item in resp.data["companyContentViews"]
        }

        for code in language_codes:
            language_name = get_language_info(code)["name"]
            self.assertEqual(result[f"0.{code}"], f"Default - {language_name}")
            self.assertEqual(
                result[f"{amazon_channel.id}.{code}"],
                f"My Amazon Store - {language_name}",
            )
            self.assertEqual(
                result[f"{shopify_channel.id}.{code}"],
                f"shop.example.com - {language_name}",
            )


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
