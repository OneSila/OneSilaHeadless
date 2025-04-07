from llm.factories.importable_properties_detector import DetectRealProductAttributesLLM
from sales_channels.integrations.magento2.constants import EXCLUDED_ATTRIBUTE_CODES
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.factories.sales_channels.sales_channel import TryConnection


class DetectRealAttributesFlow:
    def __init__(self, sales_channel: MagentoSalesChannel):
        self.sales_channel = sales_channel
        self.selected_attributes = []
        self.used_points = 0

    def _fetch_attributes(self):
        api = TryConnection(sales_channel=self.sales_channel).api
        attributes = api.product_attributes.all_in_memory()

        attribute_input_data = []
        for p in attributes:
            try:
                label = p.default_frontend_label
                if not label:
                    continue

                if p.attribute_code in EXCLUDED_ATTRIBUTE_CODES:
                    continue

                extra_info = {}
                if hasattr(p, 'frontend_input'):
                    extra_info["frontend_input"] = p.frontend_input
                if hasattr(p, 'is_visible_on_front'):
                    extra_info["is_visible_on_front"] = p.is_visible_on_front

                attribute_input_data.append({
                    "id": p.attribute_id,
                    "label": label,
                    "extra_info": extra_info,
                })

            except Exception:
                continue

        return attribute_input_data


    def _run_llm(self, attribute_input_data):
        extra_instructions = (
            "This is a Magento import. If `is_visible_on_front` is True, "
            "it's a strong indicator that the attribute should be imported, "
            "but it's not mandatory. Use your judgment based on the label and frontend_input as well. "
            "Attributes like swatch_image, tax_class, configurable, ean_code, shipment_type, dynamic_sku, image_label SHOULD NOT BE INCLUDED!!"
        )

        llm = DetectRealProductAttributesLLM(
            attributes_data=attribute_input_data,
            integration_name="Magento",
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            extra_instructions=extra_instructions
        )

        result = llm.detect_attributes()
        self.used_points = llm.ai_process.transaction.points
        return result

    def flow(self):
        attribute_input_data = self._fetch_attributes()
        self.selected_attributes = self._run_llm(attribute_input_data)
        return self.selected_attributes