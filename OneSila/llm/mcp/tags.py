TAG_SEARCH = "search"
TAG_GET = "get"
TAG_CREATE = "create"
TAG_EDIT = "edit"
TAG_RECOMMEND = "recommend"

TAG_PRODUCTS = "products"
TAG_PROPERTIES = "properties"
TAG_PROPERTY_SELECT_VALUES = "property_select_values"
TAG_COMPANY = "company"
TAG_LANGUAGES = "languages"
TAG_TYPES = "types"
TAG_FRONTEND = "frontend"
TAG_CONTENT = "content"
TAG_PRICES = "prices"
TAG_IMAGES = "images"
TAG_TAXES = "taxes"


def tool_tags(*values: str) -> set[str]:
    return set(values)
