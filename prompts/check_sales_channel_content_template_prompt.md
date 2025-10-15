# Prompt: Implement Sales Channel Content Template Validation

You are an expert Django and Strawberry GraphQL engineer working on the OneSila codebase. Implement the "sales channel content template" feature with the following requirements. Follow all repository-specific guidelines in `AGENTS.md`, including the "always kwargs" convention, avoiding opportunistic refactors, and omitting Django migration files.

## Business Context
Sales channels can optionally store an HTML template that wraps product data before it is sent to a marketplace. We need tooling that lets admins validate templates per (sales channel, language) combination before publishing.

## Functional Requirements
1. **Modeling**
   * Introduce a data model (or extend the existing one, if present) scoped to `sales_channel` and `language` that stores:
     - A reference to the sales channel.
     - The language code.
     - The raw template string (e.g., `content_template`).
     - Metadata timestamps (`created_at`, `updated_at`) if not already provided by mixins.
   * Do not generate migration files; document any required schema changes in code comments if necessary.

2. **Template Context Helper**
   * Add a helper that builds the context dictionary for template rendering. It must expose at least:
     - `title`
     - `sku`
     - `price`
     - `currency`
     - `brand`
     - `content` (existing description)
     - `images` (provide both a `main` image and an iterable of all images)
     - `product_properties` (iterable of `{ name, value }` entries with clear documentation)
   * Ensure the helper is reusable by any future renderer and that it only accepts keyword arguments (`*` signature).

3. **Mutation: `check_sales_channel_content_template`**
   * Implement a Strawberry GraphQL mutation that accepts the sales channel identifier, language, and template body.
   * The mutation should:
     - Parse and render the template in a sandboxed/safe mode using a sample product (mock data if necessary) to validate syntax and context usage.
     - Return a structured payload indicating success or failure plus any validation messages (syntax errors, missing variables, etc.).
     - Never persist the template; this is a dry-run validator.
   * Add unit tests that cover successful rendering, syntax errors, and missing variables.

4. **Security & Safety**
   * Sandbox template rendering (no file or attribute access beyond the provided context).
   * Sanitize the rendered HTML or clearly document why sanitization is unnecessary for this validator.

5. **Documentation**
   * Update any relevant README or developer-facing docs to describe:
     - How templates are structured.
     - The variables available in the context and how to loop through collections.
     - How to invoke the new mutation for validation.

## Testing
* Add and run targeted unit tests (preferably `python manage.py test … --settings OneSila.settings.agent`). Document the exact commands executed.

## Deliverables
* All new code checked in without extraneous formatting changes.
* Tests demonstrating the mutation behaviour.
* Updated documentation so teammates can adopt the feature quickly.
