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