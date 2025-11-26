# Agent Guidelines for `sales_channels/factories/taxes`

## Scope
Applies to VAT/tax-related factory code.

## Signal Discipline
- `create_remote_vat_rate` should be triggered immediately after a `VatRate` is first saved.
- `update_remote_vat_rate` should only fire when tracked fields (e.g., `name`, percentages) actually change.
- Keep remote sync idempotent; repeated updates must not duplicate VAT rates remotely.
