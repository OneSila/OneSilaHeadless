# Remote Property Mapping Flexibility - Reference

## Purpose
This document is the single working reference for the remote-property mapping feature.
It covers both parts of the ticket:

1. Type mapping flexibility (remote type can be remapped with compatibility rules).
2. Mapping multiple local properties to the same remote property (future/phase 2).

Use this as the source for implementation, QA, and future regression tests.

---

## Feature Part 1: Type Mapping Flexibility

### Goal
Allow users to remap a remote integration field type to a different OneSila property type (when compatible), without duplicating remote properties.

### High-level behavior
- A remote field keeps its integration-native type in `original_type`.
- The effective working type is `RemoteProperty.type`.
- `type` can differ from `original_type` only when compatibility rules allow it.
- Frontend does the main UX work: compatibility labels, warnings, and disclaimers.
- Backend enforces hard validation only for disallowed mappings.

### Data fields involved
- `RemoteProperty.original_type`
- `RemoteProperty.type`
- `RemoteProperty.allows_unmapped_values`
- `RemoteProperty.yes_text_value`
- `RemoteProperty.no_text_value`
- `RemotePropertySelectValue.bool_value`
- Integration-specific select-value models that do not inherit base select-value also include `bool_value`.

### Save behavior (backend)
- If `original_type` exists and `type` is empty, set `type = original_type` before validation.
- For Magento/Woo remote properties: on save, force both `original_type` and `type` to local property type.
- Validate remap against compatibility matrix (`REMOTE_PROPERTY_TYPE_CHANGE_RULES`).
- Keep type mismatch validation with local property type (current behavior), executed after compatibility check.

### Compatibility source of truth
- Backend source: `REMOTE_PROPERTY_TYPE_CHANGE_RULES` in `sales_channels/constants.py`.
- Frontend and backend must always match this rule table.
- For `SELECT` and `MULTISELECT`, compatibility depends on `allows_unmapped_values`:
  - `SELECT__allows_custom_values`
  - `SELECT__not_allows_custom_values`
  - `MULTISELECT__allows_custom_values`
  - `MULTISELECT__not_allows_custom_values`

### Disclaimers and UX copy
Frontend already prepared detailed compatibility/disclaimer copy per original->target mapping.
This copy should be treated as user-facing explanation, while backend matrix is the enforcement layer.

### Value transformation scope (intended)
Keep backend transformations minimal:
- BOOLEAN from TEXT/DESCRIPTION uses `yes_text_value` / `no_text_value`.
- BOOLEAN from SELECT/MULTISELECT uses `bool_value` mapping per remote option.
- DATE/DATETIME textual mappings use ISO format where required.
- No broad generic type-conversion engine.

### Import behavior requirements
- Schema imports must populate `original_type` from remote schema type.
- Schema imports should not overwrite user-remapped `type` on existing mappings.
- `type` should initialize from `original_type` only when `type` is missing.

---

## Feature Part 2: Map Multiple Local Properties to One Remote Property (Future / Bigger Scope)

### Goal
Allow several local properties to map to the same remote property, so we avoid duplicate remote property rows representing the same remote field.

### Why this is needed
Current one-to-one mapping creates duplicated remote properties when multiple local properties semantically map to the same integration field.

### Expected direction
- One remote property can be linked to many local properties.
- Value-level mapping (especially select values) becomes the key layer for harmonization.
- Integrations with mirror models (notably Magento/Woo) need special handling to avoid duplicate mirror entries.

### Design concerns to solve
- Source-of-truth model for many-to-one links (likely dedicated relation table).
- Conflict resolution when multiple mapped locals provide values.
- Priority/selection strategy when more than one local value is available.
- Validation to prevent ambiguous or invalid mapping states.
- Query performance (`select_related` / `prefetch_related`) to avoid N+1 issues.

---

## Test Plan Checklist

### Part 1 - Type flexibility
- Matrix validation tests for allowed/disallowed original->target mappings.
- Tests for SELECT/MULTISELECT compatibility with and without custom values.
- Save fallback test: `original_type` set + missing `type` -> auto-fill `type`.
- Import tests: `original_type` populated from schema imports; `type` preserved when user-changed.
- Integration tests (Amazon/eBay/Shein/Magento/Woo) proving exporters use effective `RemoteProperty.type`.

### Part 1 - Boolean mapping logic
- TEXT/DESCRIPTION -> BOOLEAN via `yes_text_value` / `no_text_value`.
- SELECT/MULTISELECT -> BOOLEAN via `bool_value` mappings.
- Failure cases when required boolean mapping config is missing.

### Part 2 - Multi-local mapping
- Data model tests for many-to-one relation constraints.
- Export conflict-resolution tests (multiple local values -> one remote field).
- Mirror integration tests for Magento/Woo behavior.
- GraphQL mutation/query tests for linking and resolving multiple locals.

---

## Rollout Notes
- Migration ordering across apps is critical due to polymorphic inheritance.
- For rename/remove-field steps, cross-app migration dependencies must be explicit.
- Always verify with:
  - `./manage.py showmigrations sales_channels amazon ebay shein`
  - `./manage.py migrate --plan`

---

## Working Decisions (Current)
- Frontend performs heavy UX validation/explanation.
- Backend remains strict only on hard compatibility and required mapping config.
- Keep transformations narrow and explicit.
- Continue incrementally with tests per integration and per mapping path.
