from __future__ import annotations

from django.db.models import Prefetch

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.serializers import json_response
from properties.models import Property, PropertySelectValue


class GetPropertyMcpTool(BaseMcpTool):
    name = "get_property"
    read_only = True

    def execute(
        self,
        property_id: int | None = None,
        internal_name: str | None = None,
        name: str | None = None,
    ) -> str:
        """
        Get one property by id, exact internal name, or exact translated name.
        Returns full property details including translations and select values.

        Args:
            property_id: The database id of the property.
            internal_name: Exact property internal name.
            name: Exact translated property name.
        """
        try:
            multi_tenant_company = self.get_multi_tenant_company(required=True)
            property_instance = self._get_property_match(
                multi_tenant_company=multi_tenant_company,
                property_id=property_id,
                internal_name=internal_name,
                name=name,
            )
            property_instance = self._property_queryset(multi_tenant_company=multi_tenant_company).get(id=property_instance.id)
            return json_response(data=self._serialize_property_detail(property_instance=property_instance))
        except Exception as error:
            return self.handle_error(error=error, action=self.name)

    def _get_property_match(
        self,
        *,
        multi_tenant_company,
        property_id: int | None,
        internal_name: str | None,
        name: str | None,
    ) -> Property:
        queryset = Property.objects.filter(multi_tenant_company=multi_tenant_company)

        if property_id is not None and not isinstance(property_id, int):
            raise McpToolError(f"property_id must be an integer, got: {type(property_id).__name__}")

        if not any([property_id is not None, internal_name, name]):
            raise McpToolError("Provide property_id, internal_name, or name.")

        if property_id is not None:
            queryset = queryset.filter(id=property_id)
        if internal_name:
            queryset = queryset.filter(internal_name__iexact=internal_name)
        if name:
            queryset = queryset.filter(propertytranslation__name__iexact=name)

        property_ids = list(
            queryset.order_by("id").values_list("id", flat=True).distinct()[:2]
        )

        if not property_ids:
            raise McpToolError("Property not found.")
        if len(property_ids) > 1:
            raise McpToolError("Multiple properties matched the provided identifiers.")

        return queryset.get(id=property_ids[0])

    def _property_queryset(self, *, multi_tenant_company):
        property_value_queryset = PropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
        ).prefetch_related("propertyselectvaluetranslation_set")

        return Property.objects.filter(multi_tenant_company=multi_tenant_company).prefetch_related(
            "propertytranslation_set",
            Prefetch("propertyselectvalue_set", queryset=property_value_queryset.order_by("id")),
        )

    def _serialize_property_detail(self, *, property_instance: Property) -> dict:
        return {
            "id": property_instance.id,
            "name": property_instance.name,
            "internal_name": property_instance.internal_name,
            "type": property_instance.type,
            "is_public_information": property_instance.is_public_information,
            "add_to_filters": property_instance.add_to_filters,
            "has_image": property_instance.has_image,
            "is_product_type": property_instance.is_product_type,
            "translations": [
                {
                    "language": translation.language,
                    "name": translation.name,
                }
                for translation in property_instance.propertytranslation_set.all()
            ],
            "values": [
                {
                    "id": property_value.id,
                    "value": property_value.value,
                    "translations": [
                        {
                            "language": translation.language,
                            "value": translation.value,
                        }
                        for translation in property_value.propertyselectvaluetranslation_set.all()
                    ],
                }
                for property_value in property_instance.propertyselectvalue_set.all()
            ],
        }
