from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class AccountsTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_register_flow(self):
        """
        New user registration flow works like so:
        1) Register user
        2) Create and assign multi tenant company
        3) Login
        """
        register_user_mutation = """
            mutation registerUser($username: String!, $password: String!) {
              registerUser(data: {username: $username, password: $password}) {
                username
                password
                invitationAccepted
                isMultiTenantCompanyOwner
              }
            }
        """

        register_multi_tenant_company_mutation = """
            mutation registerMyMultiTenantCompany($name: String!, $country: String!, $phoneNumber: String!) {
                registerMyMultiTenantCompany(data: {name: $name, country: $country, phoneNumber: $phoneNumber}) {
                    id
                    name
                }
            }
        """

        query = """
            query me {
              me {
                multiTenantCompany{
                    id
                }
              }
            }
        """

        username = 'my@mail.com'
        password = "someNewPas@k22!"

        company = 'company_name'
        country = 'BE'
        phone_number = '+939393939'

        resp = self.stawberry_test_client(
            query=register_user_mutation,
            asserts_errors=False,
            variables={"username": username, "password": password}
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
            query=query,
            asserts_errors=False,
        )

        me_company_id = resp.data['me']['multiTenantCompany']['id']

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)
        self.assertEqual(company_id, me_company_id)

    def test_non_email_username(self):
        register_user_mutation = """
            mutation registerUser($username: String!, $password: String!) {
                registerUser(data: {username: $username, password: $password}) {
                    username
                }
            }
        """
        username = 'my_bad_username'
        password = "someNewPas@k22!"

        try:
            resp = self.stawberry_test_client(
                query=register_user_mutation,
                variables={"username": username, "password": password}
            )
            self.fail("Should not be able to register with a non-email")
        except:
            pass

    def test_logout(self):
        mutation = """
            mutation logout {
                logout
            }
        """

    def test_me(self):
        query = """
            query me {
              me {
                username
                password
                multiTenantCompany{
                    id
                }
                language
              }
            }
        """

    def test_my_multi_tenant_company(self):
        pass
