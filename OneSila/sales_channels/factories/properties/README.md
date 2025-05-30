# Property Factory Integration Guide

## Signal Workflow

### 1. Creating a Remote Property
- **When to Create**: A remote property is created when a `PropertyTranslation` instance is created and it's the first translation for a property that is marked as `is_public_information`.
- **Signal Emitted**: `create_remote_property`

### 2. Updating a Remote Property
- **When to Update**:
  - When additional translations are added to an existing property.
  - When a `PropertyTranslation` is updated.
  - When a `PropertyTranslation` is deleted.
  - When the `add_to_filters` field in the `Property` model changes.
- **Signal Emitted**: `update_remote_property`

### 3. Deleting a Remote Property
- **When to Delete**:
  - When `is_public_information` is set to False in a `Property`.
  - When a `Property` marked as `is_public_information` is deleted.
- **Signal Emitted**: `delete_remote_property`

## Special Considerations
- **Handling Empty Property Names**: Properties are not created on initial creation due to potential absence of names. The creation process is tied to the first complete translation.
- **Pre-Delete Handling**: The `delete_remote_property` signal is sent during the `pre_delete` phase to ensure remote deletions are handled before potential cascading deletes in the system.

# Remote Property Select Value Integration Guide

## Signal Workflow

### 1. Creating a Remote Property Select Value
- **Trigger**: `PropertySelectValueTranslation` is created as the first translation.
- **Condition**: The associated `Property` is marked as `is_public_information`.
- **Signal**: `create_remote_property_select_value`

### 2. Updating a Remote Property Select Value
- **Trigger**:
  - New translations added or updated.
  - Changes to the `image` field in `PropertySelectValue`.
- **Signal**: `update_remote_property_select_value`

### 3. Deleting a Remote Property Select Value
- **Trigger**:
  - `PropertySelectValue` is deleted.
  - Associated `Property` is set to `is_public_information = False`.
- **Signal**: `delete_remote_property_select_value`

## Key Points
- **Dependencies**: Ensures related `RemoteProperty` exists before creating select values.

# Remote Product Property Integration Guide

## Signal Workflow

### 1. Creating a Remote Product Property
- **Trigger**: A `ProductProperty` instance is created.
- **Condition**: The associated `Property` is marked as `is_public_information`.
- **Additional Condition**: Ensure that the associated `RemoteProduct` and `RemoteProperty` exist; if not, create them first.
- **Signal**: `create_remote_product_property`

### 2. Updating a Remote Product Property
- **Trigger**:
  - Changes to any of the value fields: `value_boolean`, `value_int`, `value_float`, `value_date`, `value_datetime`, `value_select`, `value_multi_select`.
  - Creation, update, or deletion of a `ProductPropertyTextTranslation`.
- **Signal**: `update_remote_product_property`

### 3. Deleting a Remote Product Property
- **Trigger**:
  - `ProductProperty` is deleted.
  - The associated `Property` is set to `is_public_information = False`.
- **Signal**: `delete_remote_product_property`

## Key Points
- **Dependencies**:
  - Before creating a `RemoteProductProperty`, ensure both `RemoteProduct` and `RemoteProperty` exist. Use a preflight process to create these dependencies if they do not exist.
  - For `select` and `multi_select` properties, ensure the related `RemotePropertySelectValue` exists before proceeding.
- **Pre-Delete Handling**: Use the `pre_delete` phase to handle deletions, ensuring that cascading deletes are managed correctly and that remote deletions occur before local cascade actions.
