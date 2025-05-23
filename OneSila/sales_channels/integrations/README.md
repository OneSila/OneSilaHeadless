**Integrations Folder README**

This document explains how to add new sales-channel integrations under `sales_channels/integrations/` so we keep a consistent structure and approach across all integrations (e.g., Magento, Shopify, etc.).

---

## 📁 Directory Structure

```
sales_channels/
└── integrations/
    ├── __init__.py
    ├── magento2/
    │   ├── apps.py
    │   ├── models.py
    │   ├── factories/
    │   ├── mixins.py
    │   └── …
    └── shopify/
        ├── apps.py
        ├── models.py
        ├── factories/
        ├── mixins.py
        └── …
```

- **Root integration package**: `sales_channels/integrations` is a Python package (contains `__init__.py`).
- **Each integration** is a Django app (one directory per channel):
  - Name the directory after the integration (e.g., `shopify`, `magento2`).
  - Inside each, you’ll have standard Django app files (`apps.py`, `models.py`, `views.py` if needed), plus your layered subfolders:
    - `models.py` – sales-channel-specific mirror models
    - `mixins.py` – API client mixins (e.g., `GetMagentoAPIMixin`, `GetShopifyAPIMixin`)
    - `factories/` – layered `CreateFactory` / `UpdateFactory` classes
    - `admin.py`, etc., as required.

---

## 🚀 Creating a New Integration App

1. **Ensure the integrations package exists**
   ```bash
   ls sales_channels/integrations/__init__.py
   ```

2. **Scaffold a new Django app** under `integrations/`. Two options:
   - **Option A (preferred)**: Pre-create the folder, then run `startapp` into it:
     ```bash
     mkdir sales_channels/integrations/<integration_name>
     python manage.py startapp <integration_name> sales_channels/integrations/<integration_name>
     ```
   - **Option B**: Change directory into `integrations`, then run `startapp`:
     ```bash
     cd sales_channels/integrations
     python ../../manage.py startapp <integration_name>
     ```

3. **Add to `INSTALLED_APPS`**
   In your settings (e.g. `base.py`), register the new app:
   ```python
   INSTALLED_APPS = [
       # …
       'sales_channels.integrations.magento2',
       'sales_channels.integrations.shopify',  # new integration
       # …
   ]
   ```

4. **Define AppConfig**
   In `sales_channels/integrations/<integration_name>/apps.py`:
   ```python
   from django.apps import AppConfig

   class <IntegrationName>Config(AppConfig):
       name = 'sales_channels.integrations.<integration_name>'
       default_auto_field = 'django.db.models.BigAutoField'
       verbose_name = '<Integration Name> Integration'
   ```

5. **Create subfolders**
   Mirror the Magento/Shopify pattern:
   ```bash
   mkdir -p sales_channels/integrations/<integration_name>/{factories,mixins}
   touch sales_channels/integrations/<integration_name>/mixins.py
   ```

6. **Layered architecture**
   - **Layer 1**: `IntegrationInstanceCreateFactory` & `IntegrationInstanceUpdateFactory` live in a shared base (e.g., `sales_channels/factories/`).
   - **Layer 2**: `RemoteXxxCreateFactory` subclasses for all channels (in each integration’s `factories/`).
   - **Layer 3**: Channel‑specific details (`MagentoPropertyCreateFactory`, `ShopifyProductCreateFactory`, etc.).

7. **Models**
   - Define your channel’s mirror models in `models.py`:
     ```python
     class ShopifySalesChannel(SalesChannel):
         shop_url = models.URLField()
         access_token = models.CharField(max_length=255)
         # …

     class ShopifyProduct(RemoteProduct):
         # any Shopify‑specific fields
     ```

8. **API mixin**
   In `mixins.py`, add your `Get<Integration>APIMixin` that encapsulates session setup and activation.

9. **Factories**
   In `factories/products.py`, scaffold your `CreateFactory` and `UpdateFactory`:
   ```python
   class ShopifyProductCreateFactory(RemoteInstanceCreateFactory):
       local_model_class   = Product
       remote_model_class  = ShopifyProduct
       api_package_name    = 'product'
       api_method_name     = 'create'
       field_mapping       = { 'local_field': 'remote_field', … }
       default_field_mapping = { … }
       # override customize_payload(), serialize_response(), etc.
   ```

10. **Testing & Sanity Check**
    - Write a quick Django shell script to instantiate your mixin and factories, call .run(), and verify the Shopify API sees your test product.
    - Add any admin registrations or serializers as needed.

---

## ✅ Checklist for New Integrations

- [ ] `__init__.py` in `sales_channels/integrations/` exists
- [ ] `app` folder created via `startapp`
- [ ] Entry added to `INSTALLED_APPS`
- [ ] `AppConfig` defined with correct `name` and `label`
- [ ] `mixins.py` with API client setup
- [ ] `models.py` mirror models created
- [ ] `factories/` with layered Create/Update factories
- [ ] Sample `.run()` script or test demonstrating a successful create

Keep this README up-to-date as we refine our integration conventions! 🎉
