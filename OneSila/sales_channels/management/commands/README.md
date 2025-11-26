# Sales Channels Integration Generator

## Overview

This management command helps create a new sales channel integration with the proper folder structure and template files according to the project conventions.

## Usage

To create a new sales channel integration, run:

```bash
python manage.py create_sales_channel_integration <integration_name>
```

Where `<integration_name>` is the name of the integration you want to create (e.g., `shopify`, `prestashop`, `amazon`).

## What it Does

The command:

1. Creates the `sales_channels/integrations/` directory if it doesn't exist
2. Creates a new Django app in the `sales_channels/integrations/` directory
3. Sets up the folder structure according to the integration patterns
4. Creates template files with appropriate boilerplate code
5. Generates models, factories, and admin configurations

## File Structure Created

```
sales_channels/integrations/<integration_name>/
├── admin.py
├── apps.py
├── constants.py
├── decorators.py
├── defaults.py
├── documents.py
├── exceptions.py
├── factories/
│   ├── __init__.py
│   ├── orders.py
│   └── products.py
├── flows/
│   └── __init__.py
├── helpers.py
├── migrations/
│   └── __init__.py
├── mixins.py
├── models/
│   └── __init__.py
├── models.py
├── receivers.py
├── schema/
│   └── __init__.py
├── signals.py
├── tasks.py
├── tests/
│   └── __init__.py
├── urls.py
├── views.py
└── __init__.py
```

## After Creation

After creating the integration:

1. Add the integration to your `INSTALLED_APPS` in your settings file:
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'sales_channels.integrations.<integration_name>',
   ]
   ```

2. Migrate the database to create the necessary tables:
   ```bash
   python manage.py makemigrations sales_channels.integrations.<integration_name>
   python manage.py migrate
   ```

3. Customize the generated files to implement the integration-specific functionality

## Example

```bash
python manage.py create_sales_channel_integration shopify
```

This will create a new Shopify integration in `sales_channels/integrations/shopify/`.
