# Agent Guidelines for `products_inspector`

## Scope
Applies to all files in `OneSila/products_inspector/`.

## Adding Inspector Block Checkers
- Define new error codes and block configuration in `constants.py`. Keep error metadata updated in `ERROR_TYPES`.
- Expose block settings via dictionaries stored alongside existing `blocks` entries.
- Provide custom `QuerySet` and `Manager` classes for new proxy models, delegating to the core inspector queryset/manager.
- Implement proxy models that import their block configuration, expose `proxy_filter_fields`, and set meaningful `verbose_name` values.

## Signals and Factories
- Declare paired success/failure signals for new inspectors, caching when appropriate.
- Register factories with `InspectorBlockFactoryRegistry` and raise `InspectorBlockFailed` when validation fails.
- Receivers should refresh inspectors via `inspector_block_refresh.send(...)` following the documented pattern.

## Testing & Frontend Impact
- Add targeted tests validating the new block's behaviour.
- Coordinate with frontend teams: add translations for new error codes and update the `errorMap` logic when backend behaviour changes.
