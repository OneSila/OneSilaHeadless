from django.test import TestCase, TransactionTestCase
from model_bakery import baker
from strawberry.relay import to_base64
from core.models.multi_tenant import MultiTenantUser, MultiTenantCompany
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin

from .mutations import REGISTER_USER_MUTATION, LOGIN_MUTATION, LOGOUT_MUTATION, \
    ME_QUERY


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

    def test_invite_user(self):
        password = '22kk22@ksk!aAD'
        company = MultiTenantCompany.objects.create(name='Invitecompany', country="DE")
        user = MultiTenantUser(username='use323name@mail.com', language="nl", multi_tenant_company=company)
        user.set_password(password)
        user.save()

        user_id = to_base64("MultiTenantUserType", user.id)

        resp = self.stawberry_test_client(
            query=LOGIN_MUTATION,
            variables={"username": user.username, "password": password}
        )

        invite_mutation = """
            mutation inviteUser($username: String!, $language: String!){
              inviteUser(data: {username: $username, language: $language}){
                username
                isActive
                invitationAccepted
              }
            }
        """

        username = "invite@kdka.com"

        resp = self.stawberry_test_client(
            query=invite_mutation,
            variables={'username': username, 'language': 'nl'}
        )

        self.assertTrue(resp.errors is None)
        self.assertFalse(resp.data['inviteUser']['isActive'])
        self.assertFalse(resp.data['inviteUser']['invitationAccepted'])

        resp = self.stawberry_test_client(
            query=LOGOUT_MUTATION,
            variables={}
        )

        accept_mutation = """
            mutation acceptUserInvitation($id: GlobalID!, $username: String!, $password: String!){
              acceptUserInvitation(data: {id: $id, username: $username, password: $password}){
                username
                isActive
                invitationAccepted
              }
            }
        """

        resp = self.stawberry_test_client(
            query=accept_mutation,
            variables={'username': username, 'password': "SomePaddk@2k2", "id": user_id}
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data['inviteUser']['isActive'])
        self.assertTrue(resp.data['inviteUser']['invitationAccepted'])

    def test_enable_disable_user(self):
        password = '22kk22@ksk!aAD'
        company = MultiTenantCompany.objects.create(name='enableuser', country="DE")
        user = MultiTenantUser(username='enabledisable@maadil.com', language="nl", multi_tenant_company=company,
            is_active=False)
        user.set_password(password)
        user.save()

        user_id = to_base64("MultiTenantUserType", user.id)

        enable_query = """
        mutation enableUser($id: GlobalID!){
          enableUser(data: {id: $id}){
            username
            isActive
          }
        }
        """

        resp = self.stawberry_test_client(
            query=enable_query,
            variables={"id": user_id}
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data['inviteUser']['isActive'])

        disable_query = """
        mutation disableUser($id: GlobalID!){
          disableUser(data: {id: $id}){
            username
            isActive
          }
        }
        """

        self.assertTrue(resp.errors is None)
        self.assertFalse(resp.data['inviteUser']['isActive'])
