from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from django.test import TestCase, TransactionTestCase
import requests


# class CorsTestCase(TransactionTestCaseMixin, TransactionTestCase):
#     def test_cors(self):
#         origin = 'http://192.168.1.3:3000/auth/login'

#         headers = {
#             'Origin': origin,
#             'Access-Control-Request-Method': 'POST',
#             'Access-Control-Request-Headers': 'X-Requested-With',
#         }

#         response = requests.options('http://127.0.0.1:8080/graphql/', headers=headers)
