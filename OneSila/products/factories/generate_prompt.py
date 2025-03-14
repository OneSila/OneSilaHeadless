from media.models import MediaProductThrough, Media
from products.models import ProductTranslation
from properties.models import ProductProperty, Property


class CreateProductPromptFactory:
    def __init__(self, *, product, language="en"):
        self.product = product
        self.language = language

        self.product_name = product.name
        self.prompt = ""

        self.is_configurable = False
        self.product_translation = None
        self.short_description = None
        self.description = None
        self.rule = None
        self.product_type_attribute = None
        self.attribute = None
        self.attribute_values = {}
        self.images = []

    def get_product_type(self): # configurable or simple
        self.is_configurable = self.product.is_configurable()

    def get_product_translation(self):
        self.product_translation = ProductTranslation.objects.filter(product=self.product, language=self.language).first()
        return self.product_translation

    def get_short_description(self):
        self.short_description = self.product_translation.short_description

    def get_current_description(self):
        self.description = self.product_translation.description

    def get_product_type_attribute(self): # Ex 'Chair'
        self.rule = self.product.get_product_rule()

        if self.rule:
            self.product_type_attribute = self.rule.product_type

        return self.rule

    def get_configurable_product_attributes(self):
        variations = self.product.get_unique_configurable_variations()

        index = 0
        for variation in variations:
            self.get_attributes(variation)
            index += 1

            if index == 3:
                break

    def get_attributes(self, product=None):

        if product is None:
            product = self.product

        for product_property in ProductProperty.objects.filter(product=product, property__is_product_type=False):
            key = product_property.property.name

            value = product_property.get_value()
            if product_property.property.type ==  Property.TYPES.MULTISELECT:
                multi_select_value = []
                for select_value in value.all():
                    multi_select_value.append(select_value.value)

                value = multi_select_value

            if product_property.property.type == Property.TYPES.SELECT:
                value = value.value

            if product_property.property.type in [Property.TYPES.DATE, Property.TYPES.DATETIME]:
                value = str(value)

            if key in self.attribute_values:

                if isinstance(value, list):
                    self.attribute_values[key].merge(value)
                else:
                    self.attribute_values[key].append(value)

            else:
                self.attribute_values[key] = [value]

    def get_images(self):
        return

        for image_ass in MediaProductThrough.objects.filter(product=self.product, media__type=Media.IMAGE):
            self.images.append(image_ass.media.image_web_url)


    def build_prompt(self) -> str:
        parts = []

        # Clearly define product name and type
        parts.append(f"Product Name: {self.product_name}")
        if self.is_configurable:
            parts.append("Type: Configurable product (multiple variations available).")
        else:
            parts.append("Type: Simple product.")

        # Short and full descriptions
        if self.short_description:
            parts.append(f"Short Description: {self.short_description}")

        if self.description:
            parts.append(f"Existing Description: {self.description}")

        # Product type attribute, if available
        if hasattr(self, 'product_type_attribute') and self.product_type_attribute:
            parts.append(f"Product Category: {self.product_type_attribute}")

        # Include attributes and clearly state their origin
        if self.attribute_values:
            attributes_section = "Product Attributes:\n"
            for key, values in self.attribute_values.items():
                joined_values = ", ".join(str(v) for v in values)
                attributes_section = f"- {key}: {joined_values}"
                parts.append(attributes_section)

        # Images, if available
        if hasattr(self, 'images') and self.images:
            parts.append("Images: " + ", ".join(self.images))


        # Final instructions
        parts.append(
            f"\nBased on the above information, create an engaging, clear, SEO-optimized, and user-friendly product description."
            f" The description should be well-structured, using appropriate HTML elements (headings, paragraphs, bullet lists)."
            f" Highlight unique features, benefits, and practical use-cases for potential buyers. Write the description in {self.language.upper()}"
            f"Very important! I want it to be an HTML but this is a description inside of a bigger one so don't give me <body> only the content"
        )

        self.prompt = "\n".join(parts)
        return self.prompt

    def run(self):
        self.get_product_type()
        if self.get_product_translation() is not None:
            self.get_short_description()
            self.get_current_description()

        if self.get_product_type_attribute():
            if self.is_configurable:
                self.get_configurable_product_attributes()
            else:
                self.get_attributes()

        self.get_images()

        self.build_prompt()