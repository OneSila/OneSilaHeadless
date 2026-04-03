# OneSila MCP Notes

This document captures how we want to use FastMCP inside OneSila.

It is not only about "making tools work". The goal is to use MCP in a way that gives clients better UX, safer writes, stronger schemas, and cleaner server-side structure.

## Current Direction

We already have:

- company-scoped MCP auth in `llm.mcp.auth`
- a central MCP server in [OneSila/mcp.py](/home/david/Desktop/Desktop/backup/OneSilla/OneSilaHeadless/OneSila/OneSila/mcp.py)
- a small shared base in [llm/mcp/mcp_tool.py](/home/david/Desktop/Desktop/backup/OneSilla/OneSilaHeadless/OneSila/llm/mcp/mcp_tool.py)
- app-specific tools in per-file classes such as:
  - [properties/mcp/tools/search_properties.py](/home/david/Desktop/Desktop/backup/OneSilla/OneSilaHeadless/OneSila/properties/mcp/tools/search_properties.py)
  - [properties/mcp/tools/get_property.py](/home/david/Desktop/Desktop/backup/OneSilla/OneSilaHeadless/OneSila/properties/mcp/tools/get_property.py)

That structure is fine as a starting point. The next step is to make the tools more "real MCP" and less "JSON string wrappers".

## What We Should Standardize

### 1. Use strong tool metadata

For every tool we should define:

- a human title
- `readOnlyHint`
- `idempotentHint`
- `destructiveHint`
- `openWorldHint`

This matters because MCP clients use these hints to decide how to present tools and when to ask for confirmation.

Suggested defaults:

- Read tools:
  - `readOnlyHint=True`
  - `idempotentHint=True`
  - `destructiveHint=False`
  - `openWorldHint=False`
- Write tools that create/update internal OneSila data:
  - `readOnlyHint=False`
  - `idempotentHint=False` unless truly idempotent
  - `destructiveHint=False`
  - `openWorldHint=False`
- Delete or irreversible actions:
  - `destructiveHint=True`

Example:

```python
annotations = {
    "title": "Search Properties",
    "readOnlyHint": True,
    "idempotentHint": True,
    "destructiveHint": False,
    "openWorldHint": False,
}
```

### 2. Prefer structured output

We should treat `output_schema` as mandatory for OneSila MCP tools.

Why:

- the client gets machine-readable output
- serializers become explicit
- we do not depend on ad-hoc JSON strings
- we can give both human-readable summaries and structured payloads

For OneSila, the default rule should be:

- every tool defines an explicit `OUTPUT_SCHEMA` constant
- every tool returns a `ToolResult`
- `structured_content` must match `OUTPUT_SCHEMA`
- `content` should be a short human-readable summary, not the primary data container

This means our serializer logic should move toward:

- build typed Python payload
- validate by contract through `output_schema`
- return summary text plus structured payload

Not this:

- dump arbitrary JSON string and hope clients parse it consistently

Recommended pattern:

```python
SEARCH_PROPERTIES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "has_more": {"type": "boolean"},
        "offset": {"type": "integer"},
        "limit": {"type": "integer"},
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": ["string", "null"]},
                    "internal_name": {"type": ["string", "null"]},
                    "type": {"type": "string"},
                    "type_label": {"type": ["string", "null"]},
                },
                "required": ["id", "name", "type"],
            },
        },
    },
    "required": ["has_more", "offset", "limit", "results"],
}
```

Then:

```python
@tool(
    name="search_properties",
    output_schema=SEARCH_PROPERTIES_OUTPUT_SCHEMA,
)
async def execute(...) -> ToolResult:
    results = [...]

    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Found {len(results)} matching properties."
            )
        ],
        structured_content={
            "has_more": has_more,
            "offset": offset,
            "limit": limit,
            "results": results,
        },
    )
```

Benefits:

- better MCP client compatibility
- easier future resources/prompts/tool chaining
- cleaner frontend or agent consumption
- easier regression checking because the output shape is explicit

OneSila-specific recommendation:

- keep `output_schema` next to the tool class in the same file at first
- if a tool grows large, move schema and payload types into a sibling `schemas.py` or `types.py`
- return both internal values and business-friendly labels when useful

Examples:

- `type` + `type_label`
- `language` + `language_label`
- `status` + `status_label`

For simple read tools, the tool should return a `ToolResult` with:

- `content`: short readable summary
- `structured_content`: the real payload

Example target shape:

```python
ToolResult(
    content=[TextContent(type="text", text="Found 12 matching properties.")],
    structured_content={
        "has_more": False,
        "offset": 0,
        "limit": 20,
        "results": [...],
    },
)
```

### 3. Docstrings matter

The tool docstring is part of the client experience and should be treated as product copy, not internal dev notes.

Every tool should explain:

- what it does
- when to use it
- what the important arguments mean
- what follow-up tool to call next

For example:

- `search_properties` should say "Use `get_property` for full details on one property."
- a future `recommend_property_type` tool should explain that the caller should confirm before creating the property.

### 4. Typing is part of the MCP contract

In FastMCP, typing is not only for Python quality. It directly affects the schema exposed to the client.

This means we should use:

- `Literal[...]` for enums and fixed domain values
- `Annotated[..., Field(...)]` for limits, ranges, and parameter descriptions
- typed payload objects for serializer output

Example:

```python
PropertyTypeValue = Literal[
    "INT",
    "FLOAT",
    "TEXT",
    "DESCRIPTION",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "SELECT",
    "MULTISELECT",
]

def execute(
    self,
    type: PropertyTypeValue | None = None,
    limit: Annotated[int, Field(ge=1, le=100)] = 20,
    offset: Annotated[int, Field(ge=0)] = 0,
) -> str:
    ...
```

Why this matters:

- clients can see allowed enum values directly
- limits and validation become part of the schema
- the LLM has a better chance of calling the tool correctly

### 5. Use domain language, not only internal enum language

Internal values like `BOOLEAN` are useful for the backend, but the tool UX should expose a friendly explanation as well.

Example:

- internal type: `BOOLEAN`
- human label: `Yes/No Choice`

For property types and similar enums, we should return both:

```json
{
  "type": "BOOLEAN",
  "type_label": "Yes/No Choice"
}
```

This is especially useful for recommendation tools and client-side confirmations.

### 6. Secure server defaults

We should strongly consider:

```python
mcp = FastMCP(
    name="OneSila",
    mask_error_details=True,
)
```

Then use controlled domain errors for messages that are safe to show to clients.

This reduces the risk of leaking internals in MCP error responses.

### 7. Methods should eventually use `add_tool`

FastMCP documents a cleaner method-based pattern:

- attach metadata with `@tool()`
- register the bound method with `mcp.add_tool(...)`

That is a better long-term fit for our class-per-tool structure than hand-building metadata inside `BaseMcpTool`.

Current code works, but later we should evolve toward something like:

```python
from fastmcp.tools import tool

class SearchPropertiesMcpTool(BaseMcpTool):
    @tool(
        name="search_properties",
        description="Search properties using GraphQL-like filters.",
        annotations={
            "title": "Search Properties",
            "readOnlyHint": True,
            "idempotentHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        },
        output_schema=SEARCH_PROPERTIES_OUTPUT_SCHEMA,
    )
    async def execute(self, ...) -> ToolResult:
        ...

tool_instance = SearchPropertiesMcpTool()
mcp.add_tool(tool_instance.execute)
```

## OneSila Conventions We Should Adopt

### Tool structure

One file per tool.

Each tool class should own:

- MCP metadata
- validation
- sanitizing
- queryset or business logic
- serializer/output builder

Do not centralize parameter-specific validation in huge shared validator files.

### Output shape

Every tool should define:

- an explicit output schema constant
- a serializer or output builder method
- a `ToolResult` response

### Read vs write flow

For write tools, the expected UX should usually be:

1. recommend or inspect
2. confirm
3. create or update

The server cannot truly force confirmation in all clients, but our tool design should encourage it.

### OneSila scope

Most tools should be company-scoped and closed-world:

- data should come from the authenticated `MultiTenantCompany`
- `openWorldHint` should usually be `False`

## Example: `search_properties`

Current behavior is correct functionally, but the end goal should be more like this:

```python
SEARCH_PROPERTIES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "has_more": {"type": "boolean"},
        "offset": {"type": "integer"},
        "limit": {"type": "integer"},
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": ["string", "null"]},
                    "internal_name": {"type": "string"},
                    "type": {"type": "string"},
                    "type_label": {"type": ["string", "null"]},
                    "is_public_information": {"type": "boolean"},
                    "add_to_filters": {"type": "boolean"},
                    "has_image": {"type": "boolean"},
                },
                "required": [
                    "id",
                    "name",
                    "internal_name",
                    "type",
                    "is_public_information",
                    "add_to_filters",
                    "has_image",
                ],
            },
        },
    },
    "required": ["has_more", "offset", "limit", "results"],
}
```

And the tool should return:

```python
ToolResult(
    content=[
        TextContent(
            type="text",
            text=f"Found {len(results)} properties."
        )
    ],
    structured_content={
        "has_more": has_more,
        "offset": offset,
        "limit": limit,
        "results": results,
    },
)
```

## High-Value FastMCP Features To Use Next

### Tools

We should actively use:

- `annotations`
- `output_schema`
- `ToolResult`
- `mask_error_details=True`
- `timeout=` on tools that may run long
- `CurrentContext()` or `get_context()` when we want logging, progress, prompts, or resources inside a tool

### Resources

Resources are a good fit for read-only reference data that clients may want repeatedly.

Good OneSila candidates:

- property type reference with human labels and descriptions
- company languages
- import examples for properties and property values
- translation guidance/reference data

Examples:

- `onesila://property-types`
- `onesila://company/languages`
- `onesila://examples/property-create`

What resources should be in OneSila:

- stable reference data
- example payloads
- company-scoped read-only helper data
- guidance data that many tools may reuse

What resources should not be:

- normal CRUD endpoints in disguise
- primary write flows
- things that need business confirmation before access

Recommended first resources:

- `onesila://property-types`
  - returns all property types with:
    - internal code
    - human label
    - short explanation
    - whether translations are expected
    - whether select values are supported
- `onesila://company/languages`
  - returns:
    - main language
    - enabled languages
    - labels per language
- `onesila://examples/property-create`
  - returns example property creation payloads for:
    - text property
    - boolean property
    - select property
- `onesila://examples/property-translation`
  - returns example translation payloads
- `onesila://glossary/property-types`
  - returns business-friendly explanations like:
    - `BOOLEAN` = `Yes/No Choice`
    - `SELECT` = `Single Choice`
    - `MULTISELECT` = `Multiple Choice`

Why this helps:

- the client can read the resource before calling a tool
- tools can also read these resources through context
- we avoid repeating long type explanations in every tool docstring

Example resource shape:

```python
@mcp.resource(
    "onesila://property-types",
    name="Property Types",
    description="Reference for OneSila property types with internal codes and human labels.",
    mime_type="application/json",
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)
def get_property_types() -> str:
    ...
```

We should also use resource templates later.

Good template candidates:

- `onesila://properties/{internal_name}/usage`
- `onesila://properties/{internal_name}/examples`
- `onesila://companies/{company_id}/languages`

For OneSila, template resources are best when:

- the content is still read-only
- the client benefits from a canonical URI
- we want to expose reusable reference data, not just search results

### Prompts

Prompts can improve UX for guided flows, especially when the user or client is unsure what to do next.

Good OneSila candidates:

- suggest a property type from a business label
- ask for confirmation before creating a property
- explain translation payload expectations
- generate import-ready property payloads

Examples:

- `recommend_property_type_prompt`
- `confirm_property_creation_prompt`
- `property_translation_prompt`

Prompts are useful when we want to shape the model's reasoning before it uses tools.

Good prompt use cases in OneSila:

- asking the model to recommend a property type from business language
- asking the model to prepare a property creation payload before calling the create tool
- asking the model to verify that translations are complete
- asking the model to explain a risky write action back to the user before confirmation

Recommended first prompts:

- `recommend_property_type_prompt`
  - input:
    - business name
    - optional description
    - optional sample values
  - output:
    - suggested internal type
    - human explanation
    - warnings or ambiguities
- `confirm_property_creation_prompt`
  - input:
    - property name
    - internal name
    - selected type
    - translations
  - output:
    - concise confirmation request for the user
- `property_translation_prompt`
  - input:
    - property name
    - target languages
    - business context
  - output:
    - translation draft payload
- `bulk_property_values_prompt`
  - input:
    - property type
    - raw business values
  - output:
    - cleaned suggested value payload for the bulk create tool

Prompts should help with:

- interpretation
- confirmation
- payload preparation

Prompts should not replace:

- validation
- authorization
- deterministic business logic

That still belongs in the tool itself.

Example prompt idea:

```python
@mcp.prompt(
    name="confirm_property_creation_prompt",
    description="Generate a short confirmation message before creating a property.",
)
def confirm_property_creation_prompt(
    property_name: str,
    internal_name: str,
    property_type_label: str,
) -> str:
    return (
        f"Please confirm creating the property '{property_name}' "
        f"with internal name '{internal_name}' as '{property_type_label}'."
    )
```

Prompts are especially useful for clients that support richer guided flows, but even when the client does not expose prompt UX directly, they are still good reusable server-side building blocks.

### Context

Useful places to adopt MCP context:

- logging validation or matching decisions
- progress reporting for bulk imports
- reading helper resources from inside tools
- prompting the client for clarification in multi-step flows

Potential high-value example:

- bulk property value creation can report progress
- type recommendation can use prompt/resource context

Context is where MCP becomes more than plain request/response.

The main things we should use context for in OneSila:

- logging
- progress reporting
- resource access
- prompt access
- request metadata
- session state for multi-step flows

#### Logging

Use context logging for:

- why a property match was selected
- why a property type recommendation was chosen
- why a translation payload was partially ignored

This is useful for client visibility and debugging.

Example:

```python
await ctx.info(f"Searching property by internal_name={internal_name}")
await ctx.warning("Multiple translation matches found, narrowing by company scope.")
```

#### Progress reporting

This is very useful for bulk tools.

Good first candidates:

- bulk create property values
- bulk save translations
- future bulk product content generation

Example:

```python
await ctx.report_progress(progress=25, total=100)
```

#### Resource access from tools

Tools can read resources to avoid duplicating reference logic.

Examples:

- create-property tool reads `onesila://property-types`
- translation tools read `onesila://company/languages`
- recommendation tools read example payload resources

This keeps the ecosystem consistent.

#### Prompt access from tools

Tools can use prompts to standardize internal assistant-facing reasoning flows.

Examples:

- recommend-property-type tool gets a reusable prompt template
- write tools can assemble a confirmation prompt for the client

This should be used carefully. The tool must still remain deterministic in its final validation and persistence steps.

#### Request metadata

Context can expose request and client information.

Useful later for:

- observability
- auditing
- client-specific behavior if needed

Example:

```python
request_id = ctx.request_id
client_id = ctx.client_id
```

#### Session state

This is highly interesting for OneSila.

Potential uses:

- first tool recommends a property type
- second tool confirms and creates the property
- session stores the proposed payload temporarily

Possible flow:

1. `recommend_property_type`
2. store proposal in session state
3. client asks user for confirmation
4. `create_property_from_recommendation`
5. tool reads session state and persists

We should only use session state for short-lived guidance flows, not as a replacement for the database.

#### Elicitation

FastMCP context can ask the client for structured user input.

This is very valuable for future write flows, but only if the client supports it well.

Potential OneSila uses:

- "Which property type do you want to use?"
- "Please confirm this create action."
- "Choose one of these existing matching properties."

This is worth revisiting once our tool surface is more mature.

## Resources vs Tools vs Prompts

Use a resource when:

- it is read-only
- it is reusable reference data
- it benefits from a stable URI

Use a tool when:

- it performs search, lookup, validation, create, or update logic
- it needs business rules
- it may mutate state

Use a prompt when:

- we want reusable LLM guidance
- we want better confirmation UX
- we want standardized drafting or interpretation

Use context when:

- the tool/resource/prompt needs logging, progress, session state, resource reads, prompt reads, or request metadata

## Suggested Phase 2 MCP Additions

After the current property read tools, the next high-value MCP additions are probably:

1. `onesila://property-types` resource
2. `onesila://company/languages` resource
3. `recommend_property_type_prompt`
4. `recommend_property_type` tool using:
   - resource data
   - context logging
   - structured output with both internal and human labels
5. `create_property` tool using:
   - explicit output schema
   - `ToolResult`
   - confirmation-friendly annotations
   - possibly session state for multi-step confirmation

## Concrete Next Improvements

### Base MCP layer

Improve `BaseMcpTool` so a tool class can define:

- `title`
- `annotations`
- `output_schema`
- optional `tags`
- optional `timeout`

### Serializers

Move away from only returning formatted JSON strings. Keep serializers, but use them to build `structured_content`.

### Property read tools

Upgrade:

- `search_properties`
- `get_property`

to:

- explicit output schemas
- `ToolResult`
- type labels and richer summaries

### Property write tools

When we re-introduce write tools, they should start with:

- `recommend_property_type`
- `create_property`
- `update_property`

with confirmation-friendly metadata and domain labels.

## Working Rule

For OneSila MCP, the default target should be:

- clear tool docstrings
- strong annotations
- explicit output schemas
- `ToolResult` instead of raw JSON strings
- safe error masking
- domain-friendly labels alongside internal values

That is the difference between "we exposed some Python functions" and "we built a good MCP server".
