import re
import unicodedata

SEP_REGEX = re.compile(r"[\s\-_./]+")
ALNUM_REGEX = re.compile(r"[a-z0-9]+")
CODE_TOKEN_REGEX = re.compile(r"^(?=.*[a-z])(?=.*\d)[a-z0-9]+$")  # any token mixing letters+digits

RESERVED_PROPERTY_INTERNAL_NAMES = {"product_type"}
RESERVED_PROPERTY_INTERNAL_NAME_MAP = {"product_type": "product_type_external"}


def _strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(ch))


def _tokens(s: str):
    """Lowercase, strip accents, split on separators; normalize numeric tokens (e.g., '02' -> '2')."""
    s = _strip_accents(s or "").lower()
    s = SEP_REGEX.sub(" ", s)
    toks = ALNUM_REGEX.findall(s)
    out = []
    for t in toks:
        if t.isdigit():
            out.append(str(int(t)))  # drop leading zeros
        else:
            out.append(t)
    return out


def _is_code_like(s: str) -> bool:
    """True if ANY token mixes letters+digits (e.g., 's700bt', 'a54', 'mk2')."""
    return any(CODE_TOKEN_REGEX.match(t) for t in _tokens(s))


def _norm_code(s: str) -> str:
    """Collapse to alnum only (lowercased, accents stripped)."""
    s = _strip_accents(s or "").lower()
    return re.sub(r"[^a-z0-9]", "", s)


def sanitize_internal_name(internal_name: str | None, multi_tenant_company=None, *, allow_reserved: bool = False) -> str | None:
    """Return a normalised internal name, avoiding reserved identifiers unless explicitly allowed."""
    if not internal_name:
        return internal_name

    from django.utils.text import slugify

    normalised = slugify(internal_name).replace('-', '_')

    if normalised in RESERVED_PROPERTY_INTERNAL_NAMES and not allow_reserved:
        replacement = RESERVED_PROPERTY_INTERNAL_NAME_MAP.get(normalised, f"{normalised}_external")
        return replacement

    return normalised


def get_product_properties_dict(product) -> dict[str, list[str]]:
    """
    Fetch all properties and their values for a given product.

    :param product: product instance
    :return: Dictionary of properties and their values

    The return value looks like:
    {
        "property_name": [
            "value1",
            "value2",
            "valueN"
        ]
    }
    """
    # TODO: This should really support languages.
    from properties.models import ProductProperty, Property

    properties = (
        ProductProperty.objects.filter(product=product)
        .select_related("property", "value_select")  # Optimize DB queries
        .prefetch_related("value_multi_select")  # Prefetch related multi-select values
    )

    properties_dict = {}
    for prop in properties:
        prop_type = prop.property.type

        if prop_type == Property.TYPES.MULTISELECT:
            values = {value.value for value in prop.value_multi_select.all()}  # Use a set for uniqueness
        elif prop_type == Property.TYPES.SELECT:
            values = {prop.value_select.value} if prop.value_select else set()
        elif prop_type in {
            Property.TYPES.INT, Property.TYPES.FLOAT, Property.TYPES.TEXT,
            Property.TYPES.BOOLEAN, Property.TYPES.DATE, Property.TYPES.DATETIME
        }:
            values = {str(prop.value)} if getattr(prop, "value", None) is not None else set()
        else:
            values = set()

        properties_dict[str(prop.property.name)] = list(values)  # Convert back to a list for consistency

    return properties_dict


def generate_unique_internal_name(name, multi_tenant_company, instance_id=None):
    """Return a unique internal name for a property."""
    from django.utils.text import slugify
    from .models import Property

    base_name = slugify(name).replace('-', '_')
    internal_name = base_name
    counter = 1

    qs = Property.objects.filter(multi_tenant_company=multi_tenant_company)
    if instance_id:
        qs = qs.exclude(id=instance_id)

    while qs.filter(internal_name=internal_name).exists():
        internal_name = f"{base_name}_{counter}"
        counter += 1

    return internal_name
