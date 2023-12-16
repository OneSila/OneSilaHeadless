from django.test import TestCase
import os


class UrlManagementCommandsTestCase(TestCase):
    def test_generate_url(self):
        os.subprocess('./manage.py generate_urls all')

    def test_generate_views(self):
        os.subprocess('./manage.py generate_views all')

    def test_list_urls(self):
        os.subprocess('./manage.py list_urls')
