# Translations

We want the app to be truly multilingual. Not just depend on the default system language.
This requires us to have translations that are "loose" and we cannot use django-translation.

A good candidate was django-hvad, however with the unmaintained state and lack of playing well
with a polymorphic approach it seemed like a better idea to just keep it simple and add some
basic models to support fields in various languages.
