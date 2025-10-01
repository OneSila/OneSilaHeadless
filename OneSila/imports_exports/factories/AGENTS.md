# Agent Guidelines for `imports_exports/factories`

## Scope
Applies to import/export factories under `OneSila/imports_exports/factories/`.

## Property Import Flow
- `ImportPropertyInstance` must accept either `name` or `internal_name`. Keep heuristics that auto-detect the `type` when omitted.
- Only update boolean flags (`is_public_information`, `add_to_filters`, `has_image`) when values change; avoid redundant writes.
- Ensure `translations` payloads create/update the related translation models consistently.

## Property Select Values
- `ImportPropertySelectValueInstance` can operate on existing properties or `property_data` dictionaries. Reuse `ImportPropertyInstance` to create properties on the fly.
- Validate dependencies: confirm the associated property exists and is public before creating remote values.

## Product Property Rules
- `ImportProductPropertiesRuleInstance` manages rule creation and optional nested items; `require_ean_code` defaults to `False`.
- Nested items are delegated to `ImportProductPropertiesRuleItemInstance`. Support inline property/rule creation via `_data` payloads.
- Permit updates to `type` and `sort_order` only when values actually change.

## Examples & Testing
- When in doubt, reference the README payload examples. Mirror those structures in fixtures/tests to ensure factories remain backward compatible.
