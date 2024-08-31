from django.test import TestCase
import os


class UrlManagementCommandsTestCase(TestCase):
    def test_generate_url(self):
        os.system('./manage.py generate_urls all >/dev/null 2>&1')

    def test_generate_views(self):
        os.system('./manage.py generate_views all >/dev/null 2>&1')

    def test_list_urls(self):
        os.system('./manage.py list_urls >/dev/null 2>&1')
