import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError

from core.tests import TestCase
from sales_channels.integrations.mirakl.models import MiraklProperty, MiraklPublicDefinition


class MiraklPublicDefinitionCommandTests(TestCase):
    def test_export_command_writes_current_definitions(self):
        MiraklPublicDefinition.objects.create(
            hostname="mirakl.example.com",
            property_code="product_title",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
            language="en",
            default_value="",
            yes_text_value="",
            no_text_value="",
        )

        with TemporaryDirectory() as temp_directory:
            directory = Path(temp_directory)
            stdout = StringIO()
            with patch(
                "sales_channels.integrations.mirakl.utils.public_definitions.helpers.PUBLIC_DEFINITIONS_DIR",
                directory,
            ):
                call_command(
                    "export_mirakl_public_definitions",
                    "my_snapshot",
                    stdout=stdout,
                )

            exported_files = list(directory.glob("*.json"))
            self.assertEqual(len(exported_files), 1)
            self.assertRegex(exported_files[0].name, r"^\d{2}_\d{2}_\d{4}_my_snapshot\.json$")
            payload = json.loads(exported_files[0].read_text(encoding="utf-8"))
            self.assertEqual(
                payload,
                [
                    {
                        "default_value": "",
                        "hostname": "mirakl.example.com",
                        "language": "en",
                        "no_text_value": "",
                        "property_code": "product_title",
                        "representation_type": MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
                        "yes_text_value": "",
                    }
                ],
            )
            self.assertIn("Exported 1 Mirakl public definitions", stdout.getvalue())

    def test_export_command_can_filter_by_hostname(self):
        MiraklPublicDefinition.objects.create(
            hostname="mirakl.example.com",
            property_code="product_title",
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
        )
        MiraklPublicDefinition.objects.create(
            hostname="other-mirakl.example.com",
            property_code="brand",
            representation_type=MiraklProperty.REPRESENTATION_PROPERTY,
        )

        with TemporaryDirectory() as temp_directory:
            directory = Path(temp_directory)
            stdout = StringIO()
            with patch(
                "sales_channels.integrations.mirakl.utils.public_definitions.helpers.PUBLIC_DEFINITIONS_DIR",
                directory,
            ):
                call_command(
                    "export_mirakl_public_definitions",
                    "filtered_snapshot",
                    "--hostname=mirakl.example.com",
                    stdout=stdout,
                )

            exported_files = list(directory.glob("*.json"))
            self.assertEqual(len(exported_files), 1)
            payload = json.loads(exported_files[0].read_text(encoding="utf-8"))
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["hostname"], "mirakl.example.com")
            self.assertIn("for hostname mirakl.example.com", stdout.getvalue())

    def test_import_command_updates_existing_definitions_by_default(self):
        MiraklPublicDefinition.objects.create(
            hostname="mirakl.example.com",
            property_code="product_title",
            representation_type=MiraklProperty.REPRESENTATION_PROPERTY,
            language=None,
            default_value="old",
            yes_text_value="yes",
            no_text_value="no",
        )

        with TemporaryDirectory() as temp_directory:
            directory = Path(temp_directory)
            file_path = directory / "25_03_2026_test_import.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "hostname": "mirakl.example.com",
                            "property_code": "product_title",
                            "representation_type": MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
                            "language": "fr",
                            "default_value": "new-default",
                            "yes_text_value": "oui",
                            "no_text_value": "non",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            stdout = StringIO()
            with patch(
                "sales_channels.integrations.mirakl.utils.public_definitions.helpers.PUBLIC_DEFINITIONS_DIR",
                directory,
            ):
                call_command(
                    "import_mirakl_public_definitions",
                    file_path.name,
                    stdout=stdout,
                )

        definition = MiraklPublicDefinition.objects.get(
            hostname="mirakl.example.com",
            property_code="product_title",
        )
        self.assertEqual(definition.representation_type, MiraklProperty.REPRESENTATION_PRODUCT_TITLE)
        self.assertEqual(definition.language, "fr")
        self.assertEqual(definition.default_value, "new-default")
        self.assertEqual(definition.yes_text_value, "oui")
        self.assertEqual(definition.no_text_value, "non")
        self.assertIn("created=0, updated=1, skipped=0", stdout.getvalue())

    def test_import_command_can_skip_existing_definitions(self):
        MiraklPublicDefinition.objects.create(
            hostname="mirakl.example.com",
            property_code="product_title",
            representation_type=MiraklProperty.REPRESENTATION_PROPERTY,
            default_value="keep-me",
        )

        with TemporaryDirectory() as temp_directory:
            directory = Path(temp_directory)
            file_path = directory / "25_03_2026_skip_existing.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "hostname": "mirakl.example.com",
                            "property_code": "product_title",
                            "representation_type": MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
                            "language": "fr",
                            "default_value": "replace-me",
                            "yes_text_value": "oui",
                            "no_text_value": "non",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            stdout = StringIO()
            with patch(
                "sales_channels.integrations.mirakl.utils.public_definitions.helpers.PUBLIC_DEFINITIONS_DIR",
                directory,
            ):
                call_command(
                    "import_mirakl_public_definitions",
                    file_path.name,
                    "--skip-existing",
                    stdout=stdout,
                )

        definition = MiraklPublicDefinition.objects.get(
            hostname="mirakl.example.com",
            property_code="product_title",
        )
        self.assertEqual(definition.representation_type, MiraklProperty.REPRESENTATION_PROPERTY)
        self.assertEqual(definition.default_value, "keep-me")
        self.assertIn("created=0, updated=0, skipped=1", stdout.getvalue())

    def test_import_command_can_filter_by_hostname(self):
        with TemporaryDirectory() as temp_directory:
            directory = Path(temp_directory)
            file_path = directory / "25_03_2026_hostname_filter.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "hostname": "mirakl.example.com",
                            "property_code": "product_title",
                            "representation_type": MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
                            "language": "en",
                            "default_value": "title",
                            "yes_text_value": "",
                            "no_text_value": "",
                        },
                        {
                            "hostname": "other-mirakl.example.com",
                            "property_code": "brand",
                            "representation_type": MiraklProperty.REPRESENTATION_PROPERTY,
                            "language": "fr",
                            "default_value": "brand",
                            "yes_text_value": "oui",
                            "no_text_value": "non",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            stdout = StringIO()
            with patch(
                "sales_channels.integrations.mirakl.utils.public_definitions.helpers.PUBLIC_DEFINITIONS_DIR",
                directory,
            ):
                call_command(
                    "import_mirakl_public_definitions",
                    file_path.name,
                    "--hostname=mirakl.example.com",
                    stdout=stdout,
                )

        self.assertTrue(
            MiraklPublicDefinition.objects.filter(
                hostname="mirakl.example.com",
                property_code="product_title",
            ).exists()
        )
        self.assertFalse(
            MiraklPublicDefinition.objects.filter(
                hostname="other-mirakl.example.com",
                property_code="brand",
            ).exists()
        )
        self.assertIn("for hostname mirakl.example.com", stdout.getvalue())
        self.assertIn("created=1, updated=0, skipped=0", stdout.getvalue())

    def test_import_command_rejects_invalid_filename(self):
        with self.assertRaisesMessage(
            CommandError,
            "File name must match dd_mm_yyyy_name_parameter.json.",
        ):
            call_command("import_mirakl_public_definitions", "bad.json")
