# Creating apps and models

## Models

When creating a new app it's imporant to import models from the core instead of the default django.
eg:

```pyton
from django.db import models

class MyClass(models.Model):
    field = models.CharField(max_length=100)
```

becomes

```pyton
from core import models

class MyClass(models.Model):
    field = models.CharField(max_length=100)
```

This is the main step to ensure that the right information fields will be presented on the tables.

What extra fields will be added?

- multi_tenant_company
- created_at / updated_at timestamps

!!! tip
    Remember, always use:
    `from core import models`


What else will the new model do?

The new model will also come with django dirtyfields exposed by default and have it's
save() method replaced with save(fore_save=False)

This means that OneSila will only truly save if the data has changed.  Otherwise, nothing will happen unless you manually call the `save(force_save=True)`.

!!! tip
    Remember, OneSila will only save() if the data has changed.
    Unless specified it should trigger an empty save.

## Shared Models

In case you do want to add models that are shared across all users.  Perhaps some kind of property, or global setting.  Then you can import `SharedModel` like so:

```python
from core import models

class MySharedThing(models.SharedModel):
    field = models.IntegerField()
```
