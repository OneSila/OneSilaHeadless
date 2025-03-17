# LLM Package README

This package requires test cases. You can play with the code like this:

## Content Generation

```
from products.models import Product
from llm.factories.content import DescriptionGenLLM, ShortDescriptionLLM
from django.conf import settings

product = Product.objects.get(sku='CHAIR-CONFIG-007')

llm = DescriptionGenLLM(product, language_code=settings.LANGUAGE_CODE)
print(llm.generate_response())

# llm = DescriptionGenLLM(product, language_code='nl')
# print(llm.generate_response())


llm = ShortDescriptionLLM(product, language_code=settings.LANGUAGE_CODE)
print(llm.generate_response())

# llm = ShortDescriptionLLM(product, language_code="nl")
# print(llm.generate_response())
```

## Translations
```
from products.models import Product
from llm.factories.translations import StringTranslationLLM
from django.conf import settings

to_translate = [
	"This is an english string",
	"The issue in your code is that the __init__ method of the StringTranslationLLM class is missing self as its first parameter. In Python, instance methods (including __init__) must explicitly define self as the first parameter, which refers to the instance of the class.",
	"Green",
	"Dog Carrier",
	"Car",
	"James Dunn"
]


for i in to_translate:
	llm = StringTranslationLLM(to_translate=i, from_language_code='en', to_language_code='nl')
	print(f"**Original: \n{i}")
	print(f"**Translated: \n{llm.generate_response()}")

```
## Product Reseaercher

This is VERY EXPIRIMENTAL and needs significant improving.  Like A LOT

```
from llm.factories.product_research import ProductResearchLLM
from django.conf import settings

product = "macbook air 13 inch m3"

llm = ProductResearchLLM(product)
print(llm.generate_response())
```

## Background removal

Needs proper converstation how we can do this.  But the code (on demand model) via replicate.com can be used like:

```
from llm.factories.image_editin import CutBackgroundBirefnet

f = CutBackgroundBirefnet(source_url, to_path)
f.run()
```