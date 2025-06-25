from core.tests import TestCase
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import ExportDefinitionFactory
from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition
from sales_channels.integrations.amazon.tests.schema_data import BATTERY_SCHEMA, NUM_BATTERIES_SCHEMA, \
    NUMBER_OF_LITHIUM_METAL_CELLS_SCHEMA, CUSTOMER_PACKAGE_TYPE_SCHEMA, POWER_PLUG_TYPE_SCHEMA, CONTROLLER_TYPE_SCHEMA, \
    PRODUCT_SITE_LAUNCH_DATE_SCHEMA, COLOR_SCHEMA


class ExportDefinitionFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.public_definition = AmazonPublicDefinition.objects.create(
            product_type_code="BATTERY",
            raw_schema=BATTERY_SCHEMA["battery"],
            api_region_code='EU_UK',
            code="battery",
            name="Battery"
        )

    def test_battery_export_definition_parsing(self):
        factory = ExportDefinitionFactory(self.public_definition)
        factory.run()

        results = factory.results
        expected_codes = {
            "battery__cell_composition",
            "battery__iec_code",
            "battery__weight"
        }

        parsed_codes = {entry["code"] for entry in results}
        self.assertTrue(expected_codes.issubset(parsed_codes))

        cell_composition = next((x for x in results if x["code"] == "battery__cell_composition"), None)
        self.assertIsNotNone(cell_composition)
        self.assertEqual(cell_composition["type"], "SELECT")
        self.assertTrue(cell_composition.get("allow_not_mapped_values"))

        self.assertEqual(
            cell_composition["values"],
            [
                {"value": "alkaline", "name": "Alkaline"},
                {"value": "lead_acid", "name": "Lead Acid"},
                {"value": "lithium_ion", "name": "Lithium Ion"},
                {"value": "lithium_metal", "name": "Lithium Metal"},
                {"value": "lithium_polymer", "name": "Lithium Polymer"},
                {"value": "NiCAD", "name": "NiCAD"},
                {"value": "NiMh", "name": "NiMH"},
                {"value": "other_than_listed", "name": "Other Than Listed"},
                {"value": "sodium_ion", "name": "Sodium Ion"},
                {"value": "wet_alkali", "name": "Wet Alkali"},
            ]
        )

        iec_code = next((x for x in results if x["code"] == "battery__iec_code"), None)
        self.assertIsNotNone(iec_code)
        self.assertEqual(iec_code["type"], "SELECT")

        weight = next((x for x in results if x["code"] == "battery__weight"), None)
        self.assertIsNotNone(weight)
        self.assertEqual(weight["type"], "FLOAT")


    def test_num_batteries_schema_extraction(self):

        definition = AmazonPublicDefinition.objects.create(
            product_type_code="POWER",
            raw_schema=NUM_BATTERIES_SCHEMA["num_batteries"],
            api_region_code="EU_UK",
            code="num_batteries",
            name="Number of Batteries"
        )

        factory = ExportDefinitionFactory(definition)
        results = factory.run()

        quantity = next((x for x in results if x["code"] == "num_batteries__quantity"), None)
        self.assertIsNotNone(quantity)
        self.assertEqual(quantity["type"], "INT")

        battery_type = next((x for x in results if x["code"] == "num_batteries__type"), None)
        self.assertIsNotNone(battery_type)
        self.assertEqual(battery_type["type"], "SELECT")
        self.assertEqual(len(battery_type["values"]), 9)
        self.assertIn({"name": "AA", "value": "aa"}, battery_type["values"])

    def test_number_of_lithium_metal_cells_extraction(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="POWER_LITHIUM",
            raw_schema=NUMBER_OF_LITHIUM_METAL_CELLS_SCHEMA["number_of_lithium_metal_cells"],
            api_region_code="EU_UK",
            code="number_of_lithium_metal_cells",
            name="Number of Lithium Metal Cells"
        )

        factory = ExportDefinitionFactory(definition)
        results = factory.run()

        lithium_metal_cells = next(
            (x for x in results if x["code"] == "number_of_lithium_metal_cells"), None
        )
        self.assertIsNotNone(lithium_metal_cells)
        self.assertEqual(lithium_metal_cells["type"], "INT")

    def test_customer_package_type_extraction(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="PACKAGING",
            raw_schema=CUSTOMER_PACKAGE_TYPE_SCHEMA["customer_package_type"],
            api_region_code="EU_UK",
            code="customer_package_type",
            name="Customer Package Type"
        )

        factory = ExportDefinitionFactory(definition)
        results = factory.run()

        customer_package_type = next(
            (x for x in results if x["code"] == "customer_package_type"), None
        )
        self.assertIsNotNone(customer_package_type)
        self.assertEqual(customer_package_type["type"], "DESCRIPTION")

    def test_power_plug_type_schema_extraction(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="PLUG",
            raw_schema=POWER_PLUG_TYPE_SCHEMA["power_plug_type"],
            api_region_code="EU_UK",
            code="power_plug_type",
            name="Power Plug Type"
        )

        factory = ExportDefinitionFactory(definition)
        results = factory.run()

        plug = next((x for x in results if x["code"] == "power_plug_type"), None)
        self.assertIsNotNone(plug)
        self.assertEqual(plug["type"], "SELECT")
        self.assertEqual(len(plug["values"]), 27)
        self.assertIn({"name": "Type G", "value": "type_g_3pin_uk"}, plug["values"])


    def test_controller_type_schema_extraction(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="CONTROLLER",
            raw_schema=CONTROLLER_TYPE_SCHEMA["controller_type"],
            api_region_code="EU_UK",
            code="controller_type",
            name="Controller Type"
        )

        factory = ExportDefinitionFactory(definition)
        results = factory.run()

        controller = next((x for x in results if x["code"] == "controller_type"), None)
        self.assertIsNotNone(controller)
        self.assertEqual(controller["type"], "SELECT")
        self.assertTrue(controller.get("allow_not_mapped_values"))
        self.assertGreaterEqual(len(controller["values"]), 10)
        self.assertIn({"value": "Amazon Alexa", "name": "Amazon Alexa"}, controller["values"])


    def test_product_site_launch_date_schema_extraction(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="LAUNCH_DATE",
            raw_schema=PRODUCT_SITE_LAUNCH_DATE_SCHEMA["product_site_launch_date"],
            api_region_code="EU_UK",
            code="product_site_launch_date",
            name="Product Site Launch Date"
        )

        factory = ExportDefinitionFactory(definition)
        results = factory.run()

        launch_date = next((x for x in results if x["code"] == "product_site_launch_date"), None)
        self.assertIsNotNone(launch_date)
        self.assertEqual(launch_date["type"], "DATE")

    def test_color_schema_extraction(self):
        definition = AmazonPublicDefinition.objects.create(
            product_type_code="COLOR",
            raw_schema=COLOR_SCHEMA["color"],
            api_region_code="EU_UK",
            code="color",
            name="Color"
        )

        factory = ExportDefinitionFactory(definition)
        results = factory.run()

        import pprint
        pprint.pprint(results)

        color = next((x for x in results if x["code"] == "color"), None)
        self.assertIsNotNone(color)
        self.assertEqual(color["type"], "SELECT")
        self.assertTrue(color.get("allow_not_mapped_values"))

        self.assertIn({"name": "Red", "value": "Red"}, color["values"])
        self.assertIn({"name": "Black", "value": "Black"}, color["values"])