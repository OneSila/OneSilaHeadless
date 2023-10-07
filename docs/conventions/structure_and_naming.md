# Naming and structure

!!! tip
    👋 Use the management command to set up your initial folder structure when creating a new app.

    ```bash
    ./manage.py create_base_structure app_name
    ```

    This command will create the folders and file structure set out in this guide.


## Schema

folder called `schema` with structure:

- `types`
    - `types.py`
    - `input.py`
    - `ordering.py`
    - `filters.py`
- `queries.py`
- `mutations.py`

The structure of the schema’s should be very obvious from the other apps.
Everything has been imported or subclassed into the core to allow for easy hassle-free schema declarations.

If you do need something from the strawberry lib directly, consider importing it into the appropriate core file/folder.

## Helpers

file called `helpers.py`

This file contains various re-usable simple functions eg:

```python
def multiply(a, b):
    return a*b
```

## Defaults

file called `defaults.py`

Here is where we store default values that should be created / populated when something needs setting up with creation.

## Decorators

file called `decorators.py`

This file stores all relevant decorators for a given app.

## Exceptions

file called `exceptions.py`

This file contains all of the custom Exceptions, raised throughout the app to controle the except behaviour.  In it’s most basic form, they look like:

```python
class MyException(Exception):
    pass
```

## Tasks

All tasks go in `tasks.py`

Tasks are reserved to wrap action-classes and expose them to Huey, or any other task manager. Not to decide on actions - they will call the flows and act like a receiver but for async tasks that are run in the backen or in cronjob

__Construction steps:__

```python
from .flows import SyncStockFlow

def shopware6_local__tasks__sync_stock(*, shopware_product):
    SyncStockFlow(shopware_product=shopware_product).flow()

@db_task(cronjob(day='*'))
@db_task(cronjob(hour='4'))
def shopware6_local__tasks__sync_stock__cronjob(*, shopware_product):
    SyncStockFlow(shopware_product=shopware_product).flow()
```

__Task Naming conventions__

DO

For a normal task, delayed by the task manager.  Eg
`app_name__tasks__action`
Or for a periodic task

`app_name__tasks__action__cronjob`

example:
`shopware6_local__tasks__sync_stock`
and
`shopware6_local__tasks__sync_stock__cronjob`

## Flows

Flows are classes that decide the work.  They are the decision makers and will trigger the factories according to a set of conditions decided internally in the Flow class.

All flows go In either:

- `flows.py`
- Into folder structure like:

    ```python
    flows/
        __init__.py
        stock_sync.py
    ```


__Construction steps:__

```python
class StockSyncFlow:
    def __init__(self, shopware_product):
        self.shopware_product = shopware_product

    def identify_product(self):
        from .factories import SomeFactory
        SomeFactory.run()

    def flow(self):
        self.identify_product()
```

__Naming convention__

We won’t be adding the app name in the class. it’s causing too much repetitive typing and causing long, hard to read names.  So short, sweet and above all *clear*

```python
class SubjectActionFlow():
    def flow(self):
        # Take you actions here.
```

Example

```python
class StockSyncFlow():
    def __init__(self, product):
        self.product = product

    def sync_stock(self):
        from .factories import MagentoStockSyncFactory,\
            ShopwareStockSyncFactory
        from .models import ShopwareProduct, MagentoProduct

        if isinstance(self.product, ShopwareProduct):
            ShopwareProductFactory(self.product).work()
        elif isinstance(self.product, MagentoProduct):
            MagentoProductFactory(self.product).work()

    def flow(self):
        self.sync_stock()
```

## Factories

Factories are classes intended to take a predefined list of steps and execute. Not to make decisions.  They will do the actual work.

All files go in either:

- `factories.py`
- or are separated out in a folder structure like:

    ```python
    factories/
        __init__.py
        stock_sync.py
    ```


__Naming convention:__

```python
class SubjectActionFactory():
    def _get_users(self):
        self.users = User.objects.all()

    def _send_email(self):
        users = self._get_users()

    def _send_notification(self):
        users = self._get_users()

    def work(self):
        self._send_email()
        self._send_notification()
```

What about about the `_`.

1. All of the actual assisting methods, taking action, add and _ in front of the name.
2. The actual `work` method is the only method without underscore.

## Custom Signals

All signals are created in here, and called from this file.  All signals go in `signals.py`

Instead of hooking logic directly into the post_save or conditions you need to trigger a custom signal with a naming like so:
`appname__modelname__verb__action`

they are separated with double `_`:

example:
`magento2__magentoproduct__sync_failed`

Dont use

`telegram__magentoproduct__sync_failed`

or don’t do
`telegram_somthing_failed_random_name`

## Receivers

Receivers is where the actions go related to a receiver. Don’t stick them in models.

The receiver will call the flow, that in turn will know which factory to call.  Receivers can also call tasks if it’s a async process.

All receivers go in [receivers.py](http://receivers.py) BUT you need to add this snipped to every app:

```python
def ready(self):
    from . import receivers
```

Dont use random names.  Use this naming convention:

`app_name__my_model__signal_name`

example:

```python
@receiver(post_save, sender=MyModel)
@receiver(post_save, sender=MyOtherModel)
def my_app__my_model__post_save(sender, instance, **kwargs):
    send_messages()
```

DONT do

```python
@receiver(post_save, sender=MyModel)
@receiver(post_save, sender=MyOtherModel)
def post_save_send_email(sender, instance, **kwargs):
    send_email()

@receiver(post_save, sender=MyModel)
@receiver(post_save, sender=MyOtherModel)
def post_save_send_telegram(sender, instance, **kwargs):
    send_telegram()
```
