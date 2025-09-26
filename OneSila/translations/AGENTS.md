# Agent Guidelines for `translations`

## Scope
These instructions apply to all files under `OneSila/translations/`.

## Working Principles
- Maintain the "loose" translation model. Do not attempt to reintroduce `django-translation` or similar tightly coupled systems.
- Translation support is implemented via bespoke models; keep schema changes additive and backwards compatible.
- When enhancing translation logic, favour simple data structures that play nicely with polymorphic models.
- Ensure new functionality includes tests covering multilingual behaviour and fallbacks.
