# Agent Guidelines for `sales_channels/factories/properties`

## Scope
Instructions apply to property-related sales channel factories.

## Remote Property Lifecycle
- Emit `create_remote_property` only when the first `PropertyTranslation` for a public property is saved. Delay remote creation until names are available.
- Fire `update_remote_property` when translations change, new translations arrive, or `add_to_filters` toggles.
- Fire `delete_remote_property` during `pre_delete` or when `is_public_information` becomes `False`.

## Select Values
- Mirror the property rules for `PropertySelectValueTranslation` events. Ensure the parent property is public before creating select values.
- Sync image updates through `update_remote_property_select_value` and remove values via `delete_remote_property_select_value` when needed.

## Product Properties
- Before creating remote product properties, confirm both `RemoteProduct` and `RemoteProperty` exist. Include preflight logic to create dependencies if absent.
- Keep `create_remote_product_property`, `update_remote_product_property`, and `delete_remote_product_property` signals aligned with the local lifecycle, including translation changes.
- Handle select/multi-select values by verifying remote select values are present prior to pushing updates.
