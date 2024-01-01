# Creating apps, models, views and urls

## The app

## Models

### Search fields

The default manager also has the search ability added. Searching through the models should be set by adding:

```python
class MyModel(models.Model):
    my_field = models.CharField(max_length=100)

    class Meta:
        search_fields = ['my_field']
```


### Private Models

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

### Shared Models

In case you do want to add models that are shared across all users.  Perhaps some kind of property, or global setting.  Then you can import `SharedModel` like so:

```python
from core import models

class MySharedThing(models.SharedModel):
    field = models.IntegerField()
```

## Views and URL's

The app will use the django-structure to generate urls. Even though this is a headless backend, there are occasions where
links need to be generated, eg images or emails with links.

As the Django url structure is easy enough to use, we created a few management commands to generate the views and urls


### Generating Views

Once you have completed the models, there is a management command to create the views and urls base pages.
You can print them to screen using:

```
./manage.py generate_views app_name # or all
```

Paste this content in your `views.py` for the new app and make changes should you need to.

### Generating Urls and configuring

Just like with the views, you can also generate the `urls.py` page.  The management command for this is:

```
./manage.py generate_urls app_name # or all
```

Paste this content in your `urls.py` for the new app and make changes should you need to.

Next, configure your OneSila.urls to include the new app.
