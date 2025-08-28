from products.models import Product
from eancodes.models import EanCode
from sales_prices.models import SalesPriceList, SalesPriceListItem
from media.models import Media, MediaProductThrough
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    ProductProperty,
)
from sales_channels.models.sales_channels import SalesChannelViewAssign

TOPIC_CHOICES = [
    ("product", "product"),
    ("ean_code", "ean_code"),
    ("price_list", "price_list"),
    ("price_list_item", "price_list_item"),
    ("media", "media"),
    ("media_through", "media_through"),
    ("property", "property"),
    ("select_value", "select_value"),
    ("property_rule", "property_rule"),
    ("property_rule_item", "property_rule_item"),
    ("product_property", "product_property"),
    ("sales_channel_view_assign", "sales_channel_view_assign"),
    ("all", "all"),
]

TOPIC_MAP = {
    Product: "product",
    EanCode: "ean_code",
    SalesPriceList: "price_list",
    SalesPriceListItem: "price_list_item",
    Media: "media",
    MediaProductThrough: "media_through",
    Property: "property",
    PropertyTranslation: "property",
    PropertySelectValue: "select_value",
    PropertySelectValueTranslation: "select_value",
    ProductPropertiesRule: "property_rule",
    ProductPropertiesRuleItem: "property_rule_item",
    ProductProperty: "product_property",
    SalesChannelViewAssign: "sales_channel_view_assign",
}

ACTION_CREATE = "CREATE"
ACTION_UPDATE = "UPDATE"
ACTION_DELETE = "DELETE"
ACTION_CHOICES = [
    (ACTION_CREATE, ACTION_CREATE),
    (ACTION_UPDATE, ACTION_UPDATE),
    (ACTION_DELETE, ACTION_DELETE),
]

VERSION_2025_08_01 = "2025-08-01"
VERSION_CHOICES = [
    (VERSION_2025_08_01, VERSION_2025_08_01),
]

DELIVERY_PENDING = "PENDING"
DELIVERY_SENDING = "SENDING"
DELIVERY_DELIVERED = "DELIVERED"
DELIVERY_FAILED = "FAILED"
DELIVERY_STATUS_CHOICES = [
    (DELIVERY_PENDING, DELIVERY_PENDING),
    (DELIVERY_SENDING, DELIVERY_SENDING),
    (DELIVERY_DELIVERED, DELIVERY_DELIVERED),
    (DELIVERY_FAILED, DELIVERY_FAILED),
]

RETENTION_3M = "3m"
RETENTION_6M = "6m"
RETENTION_12M = "12m"
RETENTION_CHOICES = [
    (RETENTION_3M, RETENTION_3M),
    (RETENTION_6M, RETENTION_6M),
    (RETENTION_12M, RETENTION_12M),
]

MODE_FULL = "full"
MODE_DELTA = "delta"
MODE_CHOICES = [
    (MODE_FULL, MODE_FULL),
    (MODE_DELTA, MODE_DELTA),
]
