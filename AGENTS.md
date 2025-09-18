# Agent Guidelines for OneSilaHeadless

## General Principles
- Respect the owner's workflow: never create Django migration files unless explicitly requested. The team prefers to run `makemigrations` themselves.
- Modify only the files that are required for the task. Avoid opportunistic refactors, whitespace changes, or reformatting in unrelated modules.
- Keep performance in mind. Avoid N+1 queries and ensure GraphQL data access uses `select_related`/`prefetch_related` where needed.
- Protect secrets: never commit API keys or credentials. Require environment variables for sensitive configuration.
- Follow the "always kwargs" pattern for Python callables. Define functions with a leading `*` so they only accept keyword arguments.
- Keep individual source files under ~500 lines. If a file grows beyond this, split it into the conventional folder structure (e.g., `schema/`, `factories/`, `flows/`).
- Prefer incremental, well-tested changes. Add tests for any meaningful behaviour change; very small tweaks are the only exception. Use decorator-based patching for integrations (e.g., `@patch("sales_channels.integrations.amazon.receivers.create_amazon_product_type_rule_task")`). When adding or updating tests locally, try running them with `./manage.py test -k new_test_name` so only the new or changed cases execute. If a failure is clearly caused by the SQLite-in-container setup (the project runs on PostgreSQL), document the limitation and proceed; otherwise, fix the code or the test before shipping.
- When defining Strawberry GraphQL types that reference foreign keys, manually add lazy imports such as `product: Optional[Annotated['ProductType', lazy("products.schema.types.types")]]`.
- Mind concurrency and scale; design solutions that remain efficient as data volume grows.

## Collaboration Notes
- Our broader documentation lives at https://github.com/OneSila/OneSilaDocs/tree/master. It may be slightly outdated but is useful context.
- Security and compliance are paramount. Sanitize third-party input and validate payloads from integrations.
- Pull requests must include:
  - Summary of change
  - Related issue (if available)
  - How it was tested (explicit command list or rationale when tests are not applicable)
- Agents may generate PR descriptions automatically. Ensure the final message follows the template above.

## Code Organization Conventions
- Tasks expose flows for asynchronous work. Name them as `app_name__tasks__action` or `app_name__tasks__action__cronjob` and keep decision logic inside flows/factories.
- Flows should coordinate behaviour without embedding heavy logic in tasks or receivers. Name them clearly (e.g., `StockSyncFlow`).
- Factories handle deterministic work steps. Helper methods start with `_`, while `work()` orchestrates execution.
- Signals belong in `signals.py` and receivers in `receivers.py`. Use naming like `app_name__model__signal_name`, import receivers via `AppConfig.ready`, and trigger custom signals (e.g., `sync_failed`) rather than embedding logic in Django's default signals.

## Tooling Expectations
- Recommended local tooling: `.pre-commit-config.yaml` with `check-yaml`, `end-of-file-fixer`, `trailing-whitespace`, and `autopep8`. Use `setup.cfg` to configure `pycodestyle` (`max-line-length = 160`, ignore `E128`, exclude migrations/venv).
- Test suites typically run through `coverage run --source='.' manage.py test`; follow up with `coverage report -m` or `coverage html` when validating coverage locally.

Adhering to these guidelines keeps the repo healthy and predictable for everyone contributing to OneSilaHeadless.
