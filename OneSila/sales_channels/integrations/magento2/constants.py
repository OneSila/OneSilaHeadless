from magento.models import ProductAttribute
from properties.models import Property

PROPERTY_FRONTEND_INPUT_MAP = {
    Property.TYPES.INT: ProductAttribute.TEXT,
    Property.TYPES.FLOAT: ProductAttribute.TEXT,
    Property.TYPES.TEXT: ProductAttribute.TEXT,
    Property.TYPES.DESCRIPTION: ProductAttribute.TEXTAREA,
    Property.TYPES.BOOLEAN: ProductAttribute.BOOLEAN,
    Property.TYPES.DATE: ProductAttribute.DATE,
    Property.TYPES.DATETIME: ProductAttribute.DATETIME,
    Property.TYPES.SELECT: ProductAttribute.SELECT,
    Property.TYPES.MULTISELECT: ProductAttribute.MULTISELECT
}
EXCLUDED_ATTRIBUTE_CODES = [
    "name", "sku", "description", "short_description", "price", "special_price",
    "special_from_date", "special_to_date", "cost", "meta_title", "meta_keyword",
    "meta_description", "image", "small_image", "thumbnail", "media_gallery",
    "tier_price", "news_from_date", "news_to_date", "gallery", "status",
    "minimal_price", "visibility", "custom_design", "custom_design_from",
    "custom_design_to", "custom_layout_update", "page_layout", "category_ids",
    "options_container", "image_label", "small_image_label", "thumbnail_label",
    "quantity_and_stock_status", "custom_layout", "custom_layout_update_file",
    "url_key", "msrp", "msrp_display_actual_price_type", "links_purchased_separately",
    "samples_title", "links_title", "price_type", "sku_type", "weight_type",
    "price_view", "shipment_type", "gift_message_available", "swatch_image",
    "tax_class_id", "configurable"
]
