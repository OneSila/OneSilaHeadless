**Integrations Folder README**


To do this integration:
1. Do the PULL factories (or you end up with strange situations in the final step when creating the ProductSyncFactories)
2. You do the Attributes, Media,......
3. Lastly the Productfactories
4. Only now do the import factories.


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
  - Inside each, you'll have standard Django app files (`apps.py`, `models.py`, `views.py` if needed), plus your layered subfolders:
    - `models.py` – sales-channel-specific mirror models
    - `mixins.py` – API client mixins (e.g., `GetMagentoAPIMixin`, `GetShopifyAPIMixin`)
    - `factories/` – layered `CreateFactory` / `UpdateFactory` classes
    - `admin.py`, etc., as required.

---

## 🚀 Creating a New Integration App

1. **Use the management command to scaffold a new integration**
   ```bash
   python manage.py create_sales_channel_integration <integration_name>
   ```

   This command will:
   - Create the integration directory
   - Generate the app structure
   - Set up the `AppConfig`
   - Create necessary subfolders and files
   - Generate boilerplate for models, mixins, and factories
2. **Add to `INSTALLED_APPS`**
   In your settings (e.g. `base.py`), register the new app:
   ```python
   INSTALLED_APPS = [
       # …
       'sales_channels.integrations.magento2',
       'sales_channels.integrations.shopify',  # new integration
       # …
   ]
   ```
3. **Layered architecture**
   - **Layer 1**: `IntegrationInstanceCreateFactory` & `IntegrationInstanceUpdateFactory` live in a shared base (e.g., `sales_channels/factories/`).
   - **Layer 2**: `RemoteXxxCreateFactory` subclasses for all channels (in each integration's `factories/`).
   - **Layer 3**: Channel‑specific details (`MagentoPropertyCreateFactory`, `ShopifyProductCreateFactory`, etc.).

3. **Models**
   - Define your channel's mirror models in `models.py`:
     ```python
     class ShopifySalesChannel(SalesChannel):
         shop_url = models.URLField()
         access_token = models.CharField(max_length=255)
         # …

     class ShopifyProduct(RemoteProduct):
         # any Shopify‑specific fields
     ```

4. **API mixin**
   In `mixins.py`, add your `Get<Integration>APIMixin` that encapsulates session setup and activation.

5. **Factories**
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

6. **Testing & Sanity Check**
   - Write a TESTS to instantiate your mixin and factories, call .run(), and verify your integration API sees your test data.
   - Add any admin registrations or serializers as needed.
   - Add the logins to a fake test-store to your local settings and se it up in github as well.

---

## ✅ Checklist for New Integrations

- [ ] Integration created via `create_sales_channel_integration` command
- [ ] Mirror models customized in `models.py`
- [ ] API client setup completed in `mixins.py`
- [ ] Create/Update factories implemented and tested
- [ ] Sample `.run()` script or test demonstrating a successful API interaction

Keep this README up-to-date as we refine our integration conventions! 🎉
