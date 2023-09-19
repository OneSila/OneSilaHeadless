# OneSila
## The Only D2C Cockpit you'll ever need.


## Translations
django-translation as used in the Tim project is based on a default language.
However, as we intent to make OneSila an internationally drivern tool it becomes important that
we ensure that users are capable to have default languages in other languages outside of the default one.

There is a potential solution here, this fork seems to have soem maintenance into django 4.1.
Hopefully this can work into 4.2 as well.
https://github.com/lotrekagency/django-hvad
However, what about the polymorphic approach to the products? We won't be using django-polymorphic
but intead `django-model-utils`.  This needs testing out.
