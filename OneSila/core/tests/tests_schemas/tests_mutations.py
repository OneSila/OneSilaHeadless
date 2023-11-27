from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from core.models.multi_tenant import MultiTenantUser
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin

from .mutations import REGISTER_USER_MUTATION, LOGIN_MUTATION, LOGOUT_MUTATION


class AccountsTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_register_flow(self):
        """
        New user registration flow works like so:
        1) Register user
        2) Create and assign multi tenant company
        3) Login
        """
        register_user_mutation = REGISTER_USER_MUTATION

        register_multi_tenant_company_mutation = """
            mutation registerMyMultiTenantCompany($name: String!, $country: String!, $phoneNumber: String!) {
                registerMyMultiTenantCompany(data: {name: $name, country: $country, phoneNumber: $phoneNumber}) {
                    id
                    name
                }
            }
        """

        me_query = ME_QUERY

        username = 'my@mail.com'
        password = "someNewPas@k22!"
        language = 'nl'

        company = 'company_name'
        country = 'BE'
        phone_number = '+939393939'

        resp = self.stawberry_test_client(
            query=register_user_mutation,
            asserts_errors=False,
            variables={"username": username, "password": password, 'language': language}
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        resp_username = resp.data['registerUser']['username']

        self.assertEqual(username, resp_username)

        resp = self.stawberry_test_client(
            query=register_multi_tenant_company_mutation,
            asserts_errors=False,
            variables={"name": company, "country": country, "phoneNumber": phone_number}
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)

        company_id = resp.data['registerMyMultiTenantCompany']['id']

        resp = self.stawberry_test_client(
            query=me_query,
            asserts_errors=False,
        )

        me_company_id = resp.data['me']['multiTenantCompany']['id']

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)
        self.assertEqual(company_id, me_company_id)

        my_multi_tenant_company_query = """
        query myMultiTenantCompany{
          myMultiTenantCompany{
            id
          }
        }
        """

        resp = self.stawberry_test_client(
            query=my_multi_tenant_company_query)

        me_company_id = resp.data['myMultiTenantCompany']['id']
        self.assertEqual(me_company_id, company_id)

    def test_non_email_username(self):
        register_user_mutation = REGISTER_USER_MUTATION

        username = 'my_bad_username'
        password = "someNewPas@k22!"
        langauge = 'nl'

        try:
            resp = self.stawberry_test_client(
                query=register_user_mutation,
                variables={"username": username, "password": password, "language": language}
            )
            self.fail("Should not be able to register with a non-email")
        except:
            pass

    def test_login_logout(self):
        password = '22kk22@ksk!aAD'
        user = MultiTenantUser(username='username@mail.com', language="nl")
        user.set_password(password)
        user.save()

        resp = self.stawberry_test_client(
            query=LOGIN_MUTATION,
            variables={"username": user.username, "password": password}
        )

        self.assertTrue(resp.errors is None)

        resp = self.stawberry_test_client(
            query=LOGOUT_MUTATION,
            variables={}
        )

        self.assertTrue(resp.data['logout'] is True)

    def test_me(self):
        me_query = ME_QUERY

        password = '22kk22@ksk!aAD'
        user = MultiTenantUser(username='usead3rname@mail.com', language="nl")
        user.set_password(password)
        user.save()

        resp = self.stawberry_test_client(
            query=LOGIN_MUTATION,
            variables={"username": user.username, "password": password}
        )

        resp = self.stawberry_test_client(
            query=me_query,
            variables={}
        )

        self.assertTrue(resp.data is not None)
        self.assertTrue(resp.errors is None)

    def test_enable_disable_user(self):
        pass
