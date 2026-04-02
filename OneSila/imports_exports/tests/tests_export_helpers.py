import unittest
from types import SimpleNamespace
from unittest.mock import patch

from imports_exports.factories.exports.helpers import (
    get_product_translation_payloads,
    serialize_property_translations,
)
from imports_exports.factories.exports.mixins import AbstractExportFactory


class FakeOrderedCollection:
    def __init__(self, items):
        self.items = list(items)

    def all(self):
        return self

    def order_by(self, field_name):
        field_name = field_name.lstrip("-")
        self.items = sorted(self.items, key=lambda item: getattr(item, field_name))
        return self

    def values_list(self, field_name, flat=False):
        values = [getattr(item, field_name) for item in self.items]
        if flat:
            return values
        return [(value,) for value in values]

    def __iter__(self):
        return iter(self.items)


class DummyExportFactory(AbstractExportFactory):
    kind = "dummy"
    supported_columns = ("id",)

    def get_payload(self):
        return []


class ExportHelpersUnitTest(unittest.TestCase):
    def test_export_factory_keeps_language_none_instead_of_defaulting_company_language(self):
        export_process = SimpleNamespace(
            multi_tenant_company=SimpleNamespace(language="en", languages=["en"]),
            language=None,
            parameters={},
            columns=[],
        )

        factory = DummyExportFactory(export_process=export_process)

        self.assertIsNone(factory.language)

    def test_serialize_property_translations_returns_all_when_language_is_none(self):
        property_instance = SimpleNamespace(
            propertytranslation_set=FakeOrderedCollection(
                [
                    SimpleNamespace(language="nl", name="Kleur"),
                    SimpleNamespace(language="en", name="Color"),
                ]
            )
        )

        payload = serialize_property_translations(
            property_instance=property_instance,
            language=None,
        )

        self.assertEqual(
            payload,
            [
                {"language": "en", "name": "Color"},
                {"language": "nl", "name": "Kleur"},
            ],
        )

    def test_product_translation_payloads_filter_by_language_only(self):
        product = SimpleNamespace(
            translations=FakeOrderedCollection(
                [
                    SimpleNamespace(
                        language="en",
                        name="Default EN",
                        sales_channel=None,
                        sales_channel_id=None,
                        subtitle="",
                        short_description="",
                        description="",
                        url_key="",
                        bullet_points=FakeOrderedCollection([]),
                    ),
                    SimpleNamespace(
                        language="nl",
                        name="Default NL",
                        sales_channel=None,
                        sales_channel_id=None,
                        subtitle="",
                        short_description="",
                        description="",
                        url_key="",
                        bullet_points=FakeOrderedCollection([]),
                    ),
                    SimpleNamespace(
                        language="en",
                        name="Channel EN",
                        sales_channel=SimpleNamespace(id=12, hostname="https://channel.example.com"),
                        sales_channel_id=12,
                        subtitle="",
                        short_description="",
                        description="",
                        url_key="",
                        bullet_points=FakeOrderedCollection([]),
                    ),
                ]
            )
        )

        payload = get_product_translation_payloads(
            product=product,
            language="en",
            sales_channel=None,
        )

        self.assertEqual(
            [item["name"] for item in payload],
            ["Default EN", "Channel EN"],
        )

    def test_product_translation_payloads_prefer_channel_and_fallback_to_default(self):
        sales_channel = SimpleNamespace(id=12, hostname="https://channel.example.com")
        product = SimpleNamespace(
            translations=FakeOrderedCollection(
                [
                    SimpleNamespace(
                        language="en",
                        name="Default EN",
                        sales_channel=None,
                        sales_channel_id=None,
                        subtitle="",
                        short_description="",
                        description="",
                        url_key="",
                        bullet_points=FakeOrderedCollection([]),
                    ),
                    SimpleNamespace(
                        language="en",
                        name="Channel EN",
                        sales_channel=sales_channel,
                        sales_channel_id=12,
                        subtitle="",
                        short_description="",
                        description="",
                        url_key="",
                        bullet_points=FakeOrderedCollection([]),
                    ),
                ]
            )
        )

        payload = get_product_translation_payloads(
            product=product,
            language="en",
            sales_channel=sales_channel,
        )
        self.assertEqual([item["name"] for item in payload], ["Channel EN"])

        fallback_payload = get_product_translation_payloads(
            product=product,
            language="en",
            sales_channel=SimpleNamespace(id=99, hostname="https://missing.example.com"),
        )
        self.assertEqual([item["name"] for item in fallback_payload], ["Default EN"])

    @patch("imports_exports.factories.exports.mixins.logger")
    def test_log_progress_only_logs_on_step_or_final_row(self, mocked_logger):
        export_process = SimpleNamespace(
            id=77,
            multi_tenant_company=SimpleNamespace(language="en", languages=["en"]),
            language=None,
            parameters={},
            columns=[],
            percentage=0,
            save=lambda **kwargs: None,
        )
        factory = DummyExportFactory(export_process=export_process)

        factory.update_progress(processed=1, total_records=250)
        factory.update_progress(processed=99, total_records=250)
        factory.update_progress(processed=100, total_records=250)
        factory.update_progress(processed=250, total_records=250)

        self.assertEqual(mocked_logger.info.call_count, 2)
