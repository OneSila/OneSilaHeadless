# Agent Guidelines for `llm`

## Scope
Applies to language model utilities under `OneSila/llm/`.

## Development Practices
- Every change must be covered by tests; this package is experimental but requires safeguards.
- Keep factory interfaces simple for shell usage (see README examples for `DescriptionGenLLM`, `ShortDescriptionLLM`, `StringTranslationLLM`, and `ProductResearchLLM`).
- Assume settings like `settings.LANGUAGE_CODE` are available; avoid hardcoded language values.
- When integrating external services (e.g., replicate.com for background removal), abstract credentials behind environment variables.
