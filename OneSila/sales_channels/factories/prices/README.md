# Remote Price Integration Guide

## Signal Workflow

### 1. Adding a Price List to a Sales Channel
- **Trigger**: A new `SalesChannelIntegrationPricelist` is created.
- **Action**: Trigger a price change signal for all products assigned to the sales channel.
- **Signal**: `update_remote_price`

### 2. Removing a Price List from a Sales Channel
- **Trigger**: A `SalesChannelIntegrationPricelist` is deleted.
- **Action**: Trigger a price change signal for all products assigned to the sales channel.
- **Signal**: `update_remote_price`

### 3. Updating Price List Dates
- **Trigger**: `SalesPriceList` is updated (specifically `start_date` or `end_date` fields).
- **Action**: Trigger a price change signal for all products associated with the price list.
- **Signal**: `update_remote_price`

### 4. Deleting a Price List
- **Trigger**: A `SalesPriceList` is deleted.
- **Action**: Trigger a price change signal for all products associated with the price list.
- **Signal**: `update_remote_price`

### 5. Adding/Updating/Deleting Price List Items
- **Trigger**: `SalesPriceListItem` is created, updated, or deleted.
- **Action**: Trigger a price change signal for the affected product.
- **Signal**: `update_remote_price`

### 6. Updating Product Price or RRP
- **Trigger**: `SalesPrice` is updated (e.g., `price` or `rrp` fields).
- **Action**: Trigger a price change signal for the affected product.
- **Signal**: `update_remote_price`

### 7. Periodic Price Changes
- **Trigger**: A promotion's start or end date matches today or yesterday, respectively.
- **Action**: Trigger a price change signal for all products linked to the affected price list.
- **Signal**: `price_changed`

### 8. Handling Price Changes for Products
- **Trigger**: `price_changed` signal is received.
- **Action**: Trigger `update_remote_price` for the product if conditions are met.
- **Signal**: `update_remote_price`

## Key Points
- **Factory Check**: The actual check if the product is online (assigned to a sales channel) will occur within the factory handling the `update_remote_price` signal.
- **Performance**: Signals are used extensively to ensure all potential price changes trigger the appropriate updates. Each change to price lists, items, or direct product prices initiates the signal, ensuring synchronization with remote systems.
