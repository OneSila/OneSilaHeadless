from unittest import TestCase

from jsonschema import validate as jsonschema_validate

from products.mcp.output_types import GET_PRODUCT_OUTPUT_SCHEMA


class ProductOutputTypesTestCase(TestCase):
    def test_get_product_output_schema_accepts_light_sales_channel_references(self):
        payload = {
            "id": 1,
            "sku": "SP0192-1",
            "name": "Paper Cups",
            "type": "SIMPLE",
            "type_label": "Simple",
            "active": True,
            "ean_code": "1234567890123",
            "vat_rate": 21,
            "thumbnail_url": None,
            "has_images": False,
            "onesila_url": "https://example.com/products/sp0192-1",
            "allow_backorder": False,
            "translations": [
                {
                    "language": "en",
                    "name": "Paper Cups",
                    "sales_channel": {
                        "id": 7,
                        "hostname": "https://example.com",
                        "active": True,
                        "type": "magento",
                        "subtype": None,
                    },
                    "subtitle": "Subtitle",
                    "short_description": "Short description",
                    "description": "Description",
                    "url_key": "paper-cups",
                    "bullet_points": ["One", "Two"],
                }
            ],
            "images": [
                {
                    "image_url": "https://example.com/image.jpg",
                    "thumbnail_url": "https://example.com/thumb.jpg",
                    "type": "PACK",
                    "title": "Front",
                    "description": None,
                    "is_main_image": True,
                    "sort_order": 1,
                    "sales_channel": {
                        "id": 7,
                        "hostname": "https://example.com",
                        "active": True,
                        "type": "magento",
                        "subtype": None,
                    },
                }
            ],
        }

        jsonschema_validate(instance=payload, schema=GET_PRODUCT_OUTPUT_SCHEMA)
