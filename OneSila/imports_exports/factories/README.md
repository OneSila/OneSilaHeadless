## 🧱 ImportPropertyInstance

Handles the creation or update of a `Property` object and its `PropertyTranslation`.

### 🔑 Required Fields

At least one of:
- `name`: `str` — Human-readable name of the property.
- `internal_name`: `str` — Technical/internal name of the property (snake_case recommended).

> If `type` is not provided, it will be **auto-detected** using LLM-based heuristics.

### ⚙️ Optional Fields

| Field                   | Type   | Default  | Description                                      |
|-------------------------|--------|----------|--------------------------------------------------|
| `type`                  | `str`  | auto     | One of the allowed types (see below).            |
| `is_public_information` | `bool` | `True`   | Whether the property is visible to the customer. |
| `add_to_filters`        | `bool` | `True`   | Whether the property appears in filters.         |
| `has_image`             | `bool` | `False`  | Whether the property has images per value.      |
| `translations`          | `list` | `[]`     | Language and name list to create translations.   |

### 🔄 Updatable Fields

These fields are updated **only if the value differs**:
- `is_public_information`
- `add_to_filters`
- `has_image`

### 🧪 Allowed `type` Values

```python
Property.TYPES.ALL
# example: ['TEXT', 'DESCRIPTION', 'INT', 'FLOAT', 'BOOLEAN', 'DATE', 'DATETIME', 'SELECT', 'MULTISELECT']
```

### 📥 Example Payloads

<details>
<summary><strong>1. Fully specified data</strong></summary>

```json
{
  "name": "Color",
  "internal_name": "color",
  "type": "TEXT",
  "is_public_information": true,
  "add_to_filters": true,
  "has_image": false
}
```

</details>

<details>
<summary><strong>2. Minimal data with type provided</strong></summary>

```json
{
  "name": "Size"
}
```

or

```json
{
  "internal_name": "size"
}
```

</details>

<details>
<summary><strong>3. Auto-detected type (via LLM)</strong></summary>

```json
{
  "internal_name": "weight",
  "is_public_information": false,
  "add_to_filters": false,
  "has_image": false
}
```

</details>


## 🎯 ImportPropertySelectValueInstance

Handles the creation or update of a `PropertySelectValue` and its `PropertySelectValueTranslation`.

### 🔑 Required Fields

- `value`: `str` — The select value to import (e.g., `"Red"` or `"XL"`).

And **one of**:
- `property`: A reference to an existing `Property` object directly in the class.
- `property_data`: A dictionary to create the property inline using [ImportPropertyInstance](#-importpropertyinstance).

### ⚙️ Optional Fields

| Field          | Type   | Description |
|----------------|--------|------------|
| `property_data`| `dict` | See [ImportPropertyInstance](#-importpropertyinstance) for full structure. |
| `translations` | `list` | Language and name list to create translations.   |


### ✅ Behavior

- If `property_data` is provided, the property will be created or fetched using `ImportPropertyInstance`.
- The system uses a translation-aware factory to store the translated value (`value`) for the current language.


### 💡 Example

```json
{
  "value": "Red",
  "property_data": {
    "name": "Color",
    "internal_name": "color",
    "type": "SELECT"
  }
}
```

## 📦 ImportProductPropertiesRuleInstance

Handles the creation of a `ProductPropertiesRule`, optionally with nested `ProductPropertiesRuleItem` entries.

### 🔑 Required Fields

- `value`: `str` — The value for the product type (used to identify or create a PropertySelectValue).

### ⚙️ Optional Fields

| Field              | Type       | Default | Description |
|--------------------|------------|---------|-------------|
| `require_ean_code` | `bool`     | `False` | Whether products of this rule require an EAN code. |
| `items`            | `list`     | `[]`    | List of rule item dicts (see below for structure). |

### 🔄 Updatable Fields

- `require_ean_code`

### 🔁 Nested Rule Items (optional)

Each item is passed to `ImportProductPropertiesRuleItemInstance`. See below for the expected structure.

---

## 🧩 ImportProductPropertiesRuleItemInstance

Handles the creation of a `ProductPropertiesRuleItem`, linking a `Property` to a rule with a specific behavior.

### 🔑 Required Fields

One of:
- `property`: an existing `Property` object
**OR**
- `property_data`: `dict` (used to import a Property)

One of:
- `rule`: an existing `ProductPropertiesRule` object
**OR**
- `rule_data`: `dict` (used to import a ProductPropertiesRule)

### ⚙️ Optional Fields

| Field         | Type   | Default                  | Description |
|---------------|--------|--------------------------|-------------|
| `type`        | `str`  | `OPTIONAL`               | One of: `REQUIRED`, `OPTIONAL`, `REQUIRED_IN_CONFIGURATOR`, `OPTIONAL_IN_CONFIGURATOR`. |
| `sort_order`  | `int`  | `None`                   | Optional numeric sort order. |

### 🔄 Updatable Fields

- `type`
- `sort_order`

### 🧱 Example (Full Rule with Items)

```json
{
  "value": "T-Shirt",
  "require_ean_code": true,
  "items": [
    {
      "type": "REQUIRED_IN_CONFIGURATOR",
      "sort_order": 1,
      "property_data": {
        "name": "Color",
        "internal_name": "color",
        "type": "SELECT"
      }
    },
    {
      "type": "OPTIONAL",
      "property_data": {
        "name": "Material",
        "type": "TEXT"
      }
    }
  ]
}
```

🔗 See [ImportPropertyInstance](#-importpropertyinstance) and [ImportPropertySelectValueInstance](#-importpropertyselectvalueinstance) for nested structures.


### 🔑 Required Fields
- `name`: `str`
- If `type` is provided, must be either `SIMPLE` or `CONFIGURABLE`

### ⚙️ Optional Fields

| Field                        | Type     | Default       | Description |
|------------------------------|----------|---------------|-------------|
| `sku`                        | `str`    | auto-generated | Unique SKU code for the product |
| `type`                       | `str`    | `SIMPLE`      | Either `SIMPLE` or `CONFIGURABLE` |
| `active`                     | `bool`   | None          | Whether the product is active |
| `vat_rate`                   | `int`    | None          | VAT rate as an integer (e.g. 19) |
| `ean_code`                   | `str`    | None          | EAN code for barcoding |
| `allow_backorder`            | `bool`   | None          | Allow backorders if out of stock |
| `product_type`               | `str`    | None          | Category/type (used in rule) |
| `attributes`                 | `list`   | []            | Attribute values for the rule |
| `translations`               | `list`   | []            | Localized product content |
| `images`                     | `list`   | []            | List of image dicts |
| `prices`                     | `list`   | []            | List of price dicts |
| `variations`                 | `list`   | []            | List of variation data (for configurable) |
| `configurator_select_values` | `list` | []            | Used to auto-generate variations |

### 🔄 Updatable Fields
- `active`
- `allow_backorder`
- `vat_rate`
- `ean_code`

### ✅ Examples

#### 1. Simple product with price and translation
```json
{
  "name": "Plain T-Shirt",
  "sku": "plain-ts",
  "type": "SIMPLE",
  "vat_rate": 19,
  "ean_code": "1234567890123",
  "prices": [
    {
      "price": 49.99,
      "rrp": 59.99,
      "currency": "EUR"
    }
  ],
  "translation_data": [
    {
      "name": "Plain T-Shirt",
      "short_description": "Very nice T-Shirt"
    }
  ]
}
```

#### 2. Configurable product with variations and rule
```json
{
  "name": "T-Shirt",
  "type": "CONFIGURABLE",
  "product_type": "T-Shirt",
  "attributes": [
    {
      "value": "Red",
      "property_data": { "name": "Color" }
    },
    {
      "value": "L",
      "property_data": { "name": "Size" }
    }
  ],
  "configurator_select_values": [
    {
      "value": "Red",
      "property_data": { "name": "Color" }
    },
    {
      "value": "L",
      "property_data": { "name": "Size" }
    }
  ],
  "variations": [
    {
      "name": "Red T-Shirt - L",
      "sku": "tshirt-red-l"
    }
  ]
}
```

---

## 🌍 ImportProductTranslationInstance

Handles translations for a Product's name and content.

### 🔑 Required Fields
- `name`: `str`
- Either `product` or `product_data` must be provided

### ⚙️ Optional Fields

| Field               | Type   | Default |
|--------------------|--------|---------|
| `short_description`| `str`  | None    |
| `description`      | `str`  | None    |
| `url_key`          | `str`  | None    |


## 💰 ImportSalesPriceInstance

Handles creation of a sales price for a product.

### 🔑 Required Fields
- At least one of `rrp` or `price`
- `product` or `product_data` must be provided

### ⚙️ Optional Fields
| Field     | Type   | Default | Description |
|-----------|--------|---------|-------------|
| `currency` | `str` | system default | 3-letter ISO code (e.g., "EUR", "USD"). Must be supported and present in your system. |

### 💡 Examples

```json
{
  "product_data": { "name": "Black Hoodie" },
  "price": 29.99,
  "currency": "EUR"
}
```

---

## 🧱 ImportProductPropertyInstance

Handles setting a property on a product, with flexible value handling based on the property type.

### 🔑 Required Fields
- `value`: Depends on the property's type (e.g., number, text, boolean, list of values, etc.)
- Either `product` or `product_data`
- Either `property` or `property_data`

### ⚙️ Optional Fields
| Field         | Type  | Default |
|---------------|-------|--------|
| `value_is_id` | `bool`| `False` |
| `translations` | `list` | []     |


### 🔄 Updatable Fields
- `value_boolean`
- `value_int`
- `value_float`
- `value_date`
- `value_datetime`
- `value_select`
- `value_multi_select`
- `value_text`
- `value_description`

### 💡 Examples

```json
{
  "product_data": { "name": "Sneakers" },
  "property_data": { "name": "Color", "type": "SELECT" },
  "value": "Red"
}
```

---

## 🖼️ ImportImageInstance

Handles attaching an image to a product.

### 🔑 Required Fields
- Either `image_url` (must start with `https://`) or `image_content` (a base64-encoded image string)

### ⚙️ Optional Fields
| Field           | Type    | Default            | Description |
|------------------|---------|--------------------|-------------|
| `type`           | `str`   | `Image.PACK_SHOT`  | Type of the image (e.g., pack shot, gallery, etc.) |
| `product_data`   | `dict`  | None               | Used to associate the image with a product if `product` is not given |
| `is_main_image`  | `bool`  | `False`            | Only relevant if product is provided or imported |
| `sort_order`     | `int`   | `10`               | Only relevant if product is provided or imported |

### 💡 Notes
- If both `image_url` and `image_content` are provided, `image_content` takes priority.
- If assigning to a product, only HTTPS images are accepted via URL.
- `is_main_image` and `sort_order` are only applied when a product is present.

### 💡 Examples

```json
{
  "product_data": { "name": "Watch" },
  "image_url": "https://example.com/watch.jpg",
  "is_main_image": true,
  "sort_order": 1
}
```

```json
{
  "image_content": "<base64-encoded-image>",
  "type": "GALLERY"
}
```

---

## 🔁 ImportConfigurableVariationInstance

Assigns a single variation to a configurable product.

### 🔑 Required Fields
- `config_product` or `config_product_data`
- `variation_product` or `variation_data`

### 💡 Example

```json
{
  "config_product_data": { "name": "T-Shirt" },
  "variation_data": { "name": "T-Shirt Red - M" }
}
```

---

## 🔁 ImportConfiguratorVariationsInstance

Auto-generates multiple variations for a configurable product using a rule and value combinations.

### 🔑 Required Fields
- `config_product` or `config_product_data`
- `rule` or `rule_data`
- `select_values` or `values`

### 💡 Example Input

```json
{
  "config_product_data": { "name": "T-Shirt" },
  "rule_data": {
    "value": "T-Shirt",
    "require_ean_code": true,
    "items": [
      { "type": "REQUIRED", "property_data": { "name": "Size" } }
    ]
  },
  "values": [
    { "property_data": { "name": "Color" }, "value": "Red" },
    { "property_data": { "name": "Size" }, "value": "Large" }
  ]
}
```

Or a full example when creating a configurable product:

```json
data = {
    "name": "Fancy Flying Product",
    "sku": "SKU9221AF",
    "type": "CONFIGURABLE",
    "active": True,
    "vat_rate": 19,
    "ean_code": "1234567890123",
    "allow_backorder": False,
    "product_type": "Chair",
    "properties": [
        {"property_data": {"name": "Color", "type": "SELECT"}, "value": "Red"},
        {"property_data": {"name": "Material", "type": "SELECT", "value": "Metal"}},
    ],
    "translations": [
        {
            "name": "Fancy Product",
            "short_description": "Short desc",
            "description": "Longer description",
            "url_key": "fancy-product"
        }
    ],
    "images": [
        {
          "image_url": "https://2.com/img-.jpeg",
          "is_main_image": true
        }
    ],
    "prices": [
        {"price": 12.99, "currency": "EUR"},
        {"price": 12.99, "currency": "USD"},
    ],
    "variations": [
        {
            'variation_data': {"name": "Variant 1"}
        },
        {
            'variation_data': {"name": "Variant 2"}
        }
    ],
    "configurator_select_values": [
        {"property_data": {"name": "Size"}, "value": "Large"},
        {"property_data": {"name": "Color"}, "value": "Blue"},
    ]
}
```

### 💡 Notes
- If using `values`, each must contain both `property_data` and `value`.
- If using `select_values`, these must be existing `PropertySelectValue` objects.

---
