# Remote Order Integration Guide

## Overview
The Remote Order Integration periodically pull orders, customers, and order items from remote systems like Magento, Shopify, and Shopware into our local system. This process uses scheduled tasks rather than signals.

## Key Points
- **Periodic Task**: The integration relies on a scheduled task to pull orders, customers, and order items from the remote system.
- **Data Completeness**: Ensures all relevant order details, including customer information and order items, are accurately imported.
- **Simplified Remote Product Handling**: Does not create remote products; only populates price and quantity for order items, using `remote_sku` for minimal tracking if items are deleted locally or not existent.

## Workflow

### 1. Pulling Remote Orders
- **Process**: Periodic task retrieves orders from the remote system.
- **Data Handled**:
  - Orders
  - Customers
  - Order Items
- **Tracking**:
  - Each pulled order is linked to a local `Order` instance.
  - Customer data is synchronized to local `Customer` instances.
  - Order items are created locally with relevant details like price and quantity.

### 2. Handling Order Items
- **Local Creation Only**: Order items are created locally and linked to corresponding products with quantity and price details.
- **Remote SKU Tracking**: Each order item includes a `remote_sku` field to maintain minimal tracking, even if the item is deleted from the remote system.

## Factories

### RemoteOrderPullFactory
- **Purpose**: Manages the import of orders from remote systems.
- **Checks**:
  - Ensures order data integrity and correct linkage with local `Order` instances.
  - Validates and maps customers and addresses to local equivalents.

## Additional Notes
- **No Signal Integration**: This process is managed solely through periodic tasks, without the use of signal-driven workflows.
- **Single Source of Truth**: The local database remains the authoritative source for all order-related data.
- **Minimal Remote Product Creation**: Focuses on necessary details like price and quantity for order items, avoiding additional complexity.

This guide provides a clear understanding of the remote order integration process, emphasizing simplicity and reliability.
