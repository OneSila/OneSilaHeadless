# Mirakl Header Discovery

This document captures how we currently derive the product-side CSV headers for a Mirakl category template from the imported schema.

It is based on live schema inspection and comparison against:

- `templates/men-clothing-mens_suits-example.csv`
- `templates/toys-action_figures-example.csv`

## Current discovery rule

For one Mirakl category and one Mirakl sales channel view, the product-side headers are currently understood as:

1. all common properties
2. then inherited category properties from root to leaf
3. only properties applicable to the selected view
4. ignore properties with `requirement_level = DISABLED`
5. deduplicate by code, first appearance wins

In OneSila terms this means:

- `MiraklProperty.is_common = True`
  - include it only if it has `MiraklPropertyApplicability` for the current `MiraklSalesChannelView`
- category-specific properties
  - include them through `MiraklProductTypeItem`
  - starting from the root parent category
  - then each child category
  - until the selected leaf category
  - also only if the remote property has applicability for the current view

## Example

For category chain:

- `men`
- `men-clothing`
- `men-clothing-mens_suits`

The generated property-code headers matched the CSV example almost exactly:

- common fields first
- then `men`
- then `men-clothing`
- then `men-clothing-mens_suits`

Observed exception:

- `size_msuits_ire` existed in the schema but did not appear in the CSV example
- likely explanation: deprecated / stale / no longer applicable field

Observed inconsistency:

- the sample CSV appears to contain at least one stale or inconsistent field compared to live schema
- this means the live imported schema should be treated as the stronger source of truth than the sample CSV

## Important implementation note

The current working assumption is:

- product-side headers before offer columns can be discovered from schema
- offer-side columns are separate and start later in the template

For example in `men-clothing-mens_suits-example.csv`:

- product-side columns are before `sku`
- offer-side columns start at `sku`

## Current risk

We still need to decide whether Mirakl templates can be fully reconstructed from imported schema alone.

Known risk areas:

- some operators may expose different "common" fields
- some fields may exist in schema but not in the delivered template
- some template columns may be operator-specific semantic aliases rather than direct schema property codes
- media / image handling may differ per operator subtype
- units / measurement fields may require extra semantic pairing logic

## Notable `type_parameters` signatures

Across the Mirakl channels we've inspected there are recurring `type_parameters` combinations that encode broad field families. These are useful to recognize during schema import because they tell us whether the property behaves like a select, image, numeric, date, etc. The following table summarizes the ones we have already seen and what they typically mean on Mirakl:

| Signature                          | Meaning (typical Mirakl usage)               |
| ---------------------------------- | -------------------------------------------- |
| `[]`                               | Plain field (text, boolean, etc.)            |
| `[LIST_CODE=**]`                   | Select / multiselect list attribute          |
| `[DEFAULT_VALUE=**, LIST_CODE=**]` | Select list with default                     |
| `[PRECISION=**]`                   | Numeric field                                |
| `[PRECISION=**, UNIT=**]`          | Numeric with unit (dimensions, weight, etc.) |
| `[PATTERN=dd/MM/yyyy]`             | Date field                                   |
| `[MAX_SIZE=**, TYPE=**]`           | File/image upload                            |

### Common validation signatures

When importing the schema we also capture Mirakl’s `validations` metadata. The most frequent patterns we’ve seen include:

- `MAX_LENGTH|255` — limits text to 255 characters.
- `MIN_LENGTH|3` — enforces a minimum of 3 characters.
- `PRODUCT_REFERENCE|EAN-8|UPC|EAN-13` — restricts the value to one of the listed identifier types.
- `FORBIDDEN_WORDS|"word1,word2"` — blocks titles or descriptions containing the comma-separated list of substrings (often used for product titles).

We will need to preserve these when recreating field mappings and when building import payloads, so we know how to validate or coerce the local data before sending it to Mirakl.

We will need to keep these in mind during schema import and CSV payload generation so we can consistently apply validation, defaulting, and serialization according to Mirakl’s expectations.

## Possible fallback

If schema-only reconstruction is not reliable enough, we should introduce a dedicated model such as:

- `CategoryTemplate`

Possible role of that model:

- manually import one operator-provided template file per category or category family
- persist the exact header order
- persist which columns are product, semantic, image, property, internal-field, or offer columns
- use that stored template as the rendering contract for push

If we can reliably reconstruct the headers from schema, we may not need this model.
If we cannot, `CategoryTemplate` should become the safety mechanism for production pushes.

## Current conclusion

Right now the best working rule is:

- trust live schema first
- use template examples as validation hints
- postpone the final decision on `CategoryTemplate` until we compare more operator accounts and confirm whether header reconstruction is stable across them

## Debug helper code

The following helper was used to validate the header-discovery rule against live schema:

```python
from collections import OrderedDict

from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklSalesChannelView,
)


def get_mirakl_category_headers(*, sales_channel, sales_channel_view, category_remote_id: str):
    """
    Build the remote-property codes for one category/template.

    Order:
    1. common properties (MiraklProperty.is_common=True) with applicability to the view
    2. inherited product-type items from root -> leaf, also with applicability
    3. ignore DISABLED properties
    4. dedupe by code, first appearance wins
    """

    if not isinstance(sales_channel_view, MiraklSalesChannelView):
        if hasattr(sales_channel_view, "get") and hasattr(sales_channel_view, "model"):
            sales_channel_view = sales_channel_view.get()
        else:
            sales_channel_view = MiraklSalesChannelView.objects.get(id=sales_channel_view)

    category = MiraklCategory.objects.select_related("parent").get(
        sales_channel=sales_channel,
        remote_id=category_remote_id,
    )

    chain = []
    current = category
    while current is not None:
        chain.append(current)
        current = current.parent
    chain.reverse()

    applicable_property_ids = set(
        MiraklPropertyApplicability.objects.filter(
            sales_channel=sales_channel,
            view=sales_channel_view,
        ).values_list("property_id", flat=True)
    )

    ordered_codes = OrderedDict()

    common_properties = (
        MiraklProperty.objects.filter(
            sales_channel=sales_channel,
            is_common=True,
            id__in=applicable_property_ids,
        )
        .exclude(requirement_level="DISABLED")
        .order_by("code")
    )

    for remote_property in common_properties:
        code = (remote_property.code or "").strip()
        if code:
            ordered_codes.setdefault(
                code,
                {
                    "source": "common",
                    "category": None,
                    "property": remote_property,
                },
            )

    for chain_category in chain:
        product_type = (
            MiraklProductType.objects.filter(
                sales_channel=sales_channel,
                category=chain_category,
            ).first()
        )
        if product_type is None:
            continue

        items = (
            MiraklProductTypeItem.objects.filter(
                product_type=product_type,
                remote_property_id__in=applicable_property_ids,
            )
            .exclude(remote_property__requirement_level="DISABLED")
            .select_related("remote_property")
            .order_by("id")
        )

        for item in items:
            code = (item.remote_property.code or "").strip()
            if code:
                ordered_codes.setdefault(
                    code,
                    {
                        "source": "category",
                        "category": chain_category,
                        "property": item.remote_property,
                    },
                )

    headers = list(ordered_codes.keys())

    print("CATEGORY CHAIN:")
    for chain_category in chain:
        print(f"- {chain_category.remote_id} | {chain_category.name}")

    print("\\nHEADERS:")
    for index, code in enumerate(headers, start=1):
        data = ordered_codes[code]
        category_obj = data["category"]
        print(
            f"{index}. {code} "
            f"(source={data['source']}, "
            f"category={getattr(category_obj, 'remote_id', '-')}, "
            f"common={data['property'].is_common}, "
            f"requirement_level={data['property'].requirement_level})"
        )

    return headers
```
