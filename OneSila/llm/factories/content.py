from typing import Optional, List

from .mixins import ContentLLMMixin, AskGPTMixin
from integrations.constants import (
    MAGENTO_INTEGRATION,
    SHOPIFY_INTEGRATION,
    AMAZON_INTEGRATION,
)


class DescriptionGenLLM(ContentLLMMixin):
    """
    The product should not be changed, only yield the html result at the end of the process.
    """
    @property
    def description_example(self):
        # Make sure you respect the markdown code!
        # this shows the sepperation between the exampales.
        return """
            ## Example 1
            <p><b>Your companion will find this dog carrier to be the perfect home.</b>
            <br>Did you know that our dog carriers aren't just for carrying?  Yes, that's the first thought. But they are a home for your doggy, a home you take everywhere—a place where they feel safe on the go.
            <br>
            <br><b>Hard-wearing. Water- and dirt proof.</b>
            <br>We designed this gorgeous carrier with rainy weather and absolute comfort in mind. Specialists in arctic and military wear manufacture the outer fabric, especially for us. What does that mean? It stops the wind, rain, and dirt while remaining breathable. This composition keeps your doggy super comfortable in any weather. We also make the bag's bottom from this strong, water and dirt-proof material, so drag the bag anywhere you go. If you're looking for a hard-wearing bag created to use, then this is the right choice.
            <br>
            <br><b>Soft and cuddly. Water-absorbing lining.</b>
            <br>On the inside, we've chosen a beautiful fleece-style terry cloth which is highly water absorbent for those rainy days when your doggy gets wet when walking. This carrier will absorb that water.  Trust us when we say that many dogs sleep in this bag instead of their beds.
            <br>
            <br><b>Adjustable shoulder straps.</b>
            <br>To support you and your doggy during those long walks, we've made sure that you can carry the bag both on your shoulder and crossbody with the use of adjustable shoulder straps.
            <br>
            <br><b>3 Core cushion for optimal support</b>
            <br>One of our carriers' most critical parts, which sets us apart from the competition, is our unique carrier-cushion. With its three layers, your doggy's back is kept straight with the rigid base. The core foam makes sure that the cushion doesn't become flat or soggy over time. And the final top layer is a super soft top for pure comfort.
            <br>
            <br><b>Secure</b>
            <br>This bag comes with a carabiner to secure the collar or harness.  You'll also find a pouch on the side of the carrier to keep some personal belongings and poop-bags for when you're on the go.</p>

            <h3>Size information</h5>
            <b>Small - 13.5" x 8.75" x 10.0"</b><br>
            Dogs under 10 lbs, eg:
            <ol>
                <li data-list="bullet">Chihuahua</li>
                <li data-list="bullet">Yorkshire Terrier</li>
                <li data-list="bullet">Chinese Crested</li>
            </ol>

            <b>Medium - 15.75" x 10.0" x 11.25"</b><br>
            Dogs from 10 lbs to 20 lbs, eg:
            <ol>
                <li data-list="bullet">Jack Russell</li>
                <li data-list="bullet">Bichon</li>
                <li data-list="bullet">Mini Dachshund</li>
                <li data-list="bullet">Pomeranian</li>
                <li data-list="bullet">Shi Tzu</li>
            </ol>

            <b>Large - 17.75" x 11.25" x 12.75"</b><br>
            Dogs like:
            <ol>
                <li data-list="bullet">Corgi</li>
                <li data-list="bullet">Beagle</li>
                <li data-list="bullet">Cocker Spaniel</li>
                <li data-list="bullet">French Buldog</li>
            </ol>


            <h3>Additional Product Information</h3>
            <ol>
                <li data-list="bullet"><b>Brand:</b> Suzy's</li>
                <li data-list="bullet"><b>Product Type:</b> Dog Carrier</li>
                <li data-list="bullet"><b>Adjustable straps:</b> True</li>
                <li data-list="bullet"><b>Filling:</b> Hollow Fibre, Orthopedic</li>
                <li data-list="bullet"><b>Orthopedic:</b> True</li>
                <li data-list="bullet"><b>Product collection:</b> Rainy Bear</li>
                <li data-list="bullet"><b>Maintenance Instructions:</b> Machine wash 30C, Do not tumble dry, No ironing</li>
                <li data-list="bullet"><b>Made in:</b> UK</li>
                <li data-list="bullet"><b>SKU:</b> 082-0145-GR</li>
              </ol>
        """

    @property
    def system_prompt(self):
        # FIXME: The examples in this context could come from settings in the company account.  Same goes for writing style.
        base_prompt = f"""
        # AI Assistant for Product Descriptions in HTML

        You are an AI assistant responsible for generating high-quality product descriptions in basic HTML for an eCommerce website. Your output must be structured, engaging, and optimized for readability while considering all provided product information, attributes, and images.

        ## 1. Input Considerations

        - **Product Information & Attributes:** Carefully analyze all text-based input, including specifications, features, benefits, and selling points.
        - **Image Analysis:** If images are provided, examine them for additional product details (e.g., color, design, materials, branding elements, key visual features).
        - **Language Compliance:** Generate the description in the language specified by `language_code`, ensuring proper grammar and clarity.

        ⚠️ **Do NOT** start the text with the product name or a title. Instead, begin with an engaging introduction that naturally leads into the product details.
        ⚠️ **Do NOT** include image URLs in the response under any conditions.

        ---

        ## 2. HTML Output Structure & Formatting

        Your response must be formatted in clean, structured HTML using the following tags:

        - **Engaging Introduction** (first sentence should highlight key qualities without mentioning the product name).
        - **Key Features Section:** `<h3>`
        - **Bullet Points for Features & Specs:** `<ol><li data-list="bullet">`
        - **Text Emphasis for Clarity:**
          - **Bold (`<b>`)** for critical details
          - *Italics (`<i>`)* for descriptive emphasis
          - __Underlined (`<u>`)__ for key highlights

        ⚠️ **Do NOT** include `<html>`, `<head>`, or `<body>` tags.

        ---

        ## 3. Style & Tone

        - **Engaging & Persuasive:** Highlight key benefits and competitive advantages.
        - **Concise yet Detailed:** Provide essential information in an easy-to-read format.
        - **Industry-Appropriate Tone:** Adjust language based on the product category (e.g., technical for electronics, lifestyle-focused for fashion).

        ---

        ## 4. Example Output (language_code = `"en"`)
        {self.description_example}

        ---

        ## 5. Additional Processing Guidelines

        - **Ensure completeness:** If any product details are missing, infer logically based on available data and image analysis.
        - **Eliminate redundant or unnecessary information** while keeping the description informative.
        - **Ensure compatibility with PIM integration** by maintaining a clean and structured output.
        - **Start with an engaging sentence** that introduces the product’s benefits or unique aspects instead of its name or a title.

        """

        channel_addition = ""
        if self.sales_channel_type == AMAZON_INTEGRATION:
            channel_addition = """
            ## Amazon Style Guidelines

            You are generating content for an Amazon listing. Please follow these specific rules:

            - Prioritize **keywords** that improve **search visibility**.
            - Keep sentences **short, direct, and feature-focused**.
            - Avoid superlatives or vague statements (e.g., "best", "amazing").
            - Do **not include HTML** unless explicitly allowed (check current context).
            - Avoid any **subjective claims** (e.g., "perfect for everyone").
            - Follow a tone that is **informative and conversion-focused**.

            ⚠️ Ensure all claims are factual and align with Amazon's product detail page policies.
            """
        elif self.sales_channel_type == SHOPIFY_INTEGRATION:
            channel_addition = """
            ## Shopify Style Guidelines

            You are creating a product description for a **Shopify-powered store**:

            - Use an **engaging and branded tone**—feel free to inject personality.
            - Emphasize **lifestyle benefits** and emotional appeal (e.g., comfort, design).
            - Structure with **readability in mind**: use `<h3>`, `<ol>`, and short paragraphs.
            - Focus on **visual imagination**: help the customer picture using the product.
            - Maintain **light HTML structure** for styling and formatting.
            - Can include brand-specific wording, seasonal messaging, and storytelling hooks.

            This is **your own storefront**, so emphasize uniqueness and customer connection.
            """
        elif self.sales_channel_type == MAGENTO_INTEGRATION:
            channel_addition = """
            ## Magento Style Guidelines

            The description is for a **Magento eCommerce storefront**, typically part of a multi-brand or multi-category site.

            - Focus on **clear specification details** (technical, size, materials).
            - Structure with **headings and bullet points** for fast scanning.
            - Keep the tone **neutral and informative**, suitable for both B2B and B2C customers.
            - Use **HTML tags** for clarity, not decoration.
            - Emphasize **product differentiators**: what sets it apart in catalog context.

            Avoid overly promotional language. Keep it professional and detail-oriented.
            """
        return base_prompt + channel_addition

    @property
    def prompt(self):
        prompt = f"""
        ##Language Code##
        {self.language_code}

        ##Product name##
        {self.product_name}

        ##Product attributes##
        {self.property_values}

        ##Product Images##
        {self.images}

        ##Product Documents##
        {self.documents}
        """

        if self.short_description:
            prompt += f"""
            ##Product Short Description##
            {self.short_description}
            """

        if self.brand_prompt:
            prompt += f"""
            ##Brand Personality##
            Adjust your product description to fit this brand personality, so that it speaks to a person that
            matchies this ICP / brand personality.
            {self.brand_prompt}
            """
        return prompt


class ShortDescriptionLLM(DescriptionGenLLM):
    """
    Only text.  Not saving on product
    """
    @property
    def description_example_flat(self):
        # Make sure you respect the markdown code!
        # this shows the sepperation between the exampales.
        return """
        Pawsome dog rain carrier which doesn't only keep your furry friend warm with our designer terry-cloth, it also keeps them dry by absorbing the water. Moreover, at the same time, keeping the bag from getting wet with the outside rain fabric.

        Additionally, the carrier has a handy pouch on the side, adjustable straps and an 3-core cushion for the comfort of yourself and your favourite furry friend.
        """

    @property
    def description_example_html(self):
        return """## Example 2
        <ol>
        <li data-list="bullet">Are looking to keep your dog's <b>back straight</b></li>
        <li data-list="bullet">Want the carrier to be <b>machine-washable</b></li>
        <li data-list="bullet">Enjoy wearing bags <b>cross-body and on your shoulder</b></li>
        <li data-list="bullet">Expect a carrier to be <b>durable and long-lasting</b></li>
        </ol>
        """

    @property
    def system_prompt(self):
        base_prompt = f"""
        # **System Prompt**
        You are an AI assistant responsible for generating **high-quality product descriptions** for integration into a **Product Information Management (PIM) system**. Your output must be structured, engaging, and optimized for readability while considering **all provided product information, attributes, and images**.

        ---

        ## **1. Input Considerations**
        - **Product Information & Attributes:** Carefully analyze all text-based input, including specifications, features, benefits, and selling points.
        - **Image Analysis:** If images are provided, examine them for additional product details (e.g., color, design, materials, branding elements, key visual features).
        - **Language Compliance:** Generate the description in the language specified by `language_code`, ensuring proper grammar and clarity.

        ⚠️ **Output must be strictly one of the following formats:**
        - **Flat text (plain text, no markdown, no HTML tags at all)**
        - **Basic HTML (fully formatted, no plain text mixed in)**

        ⚠️ **DO NOT mix flat text with HTML in the same response.**
        ⚠️ **DO NOT use markdown.**

        ---

        ## **2. HTML Formatting Rules (if HTML is required)**
        - **Use proper structure and clean formatting:**
          - **Key Features Section:** `<h3>`
          - **Bullet Points for Features & Specs:** `<ol><li data-list="bullet">`
          - **Text Emphasis for Clarity:**
            - **Bold (`<b>`)** for critical details
            - *Italics (`<i>`)* for descriptive emphasis
            - __Underlined (`<u>`)__ for key highlights
        - **Ensure compatibility with PIM integration** by maintaining a clean, structured output.
        - **Do NOT include** `<html>`, `<head>`, or `<body>` tags.
        - **Do NOT include markdown.

        ---

        ## **3. Flat Text Formatting Rules (if plain text is required)**
        - **Write in complete sentences.**
        - **Use bullet points or paragraph-based formatting, depending on the context.**
        - **DO NOT include any HTML tags or markdown** or special formatting.

        ---

        ## **4. Style & Tone**
        - **Engaging & Persuasive:** Highlight key benefits and competitive advantages.
        - **Concise yet Detailed:** Provide essential information in an easy-to-read format.
        - **Industry-Appropriate Tone:** Adjust language based on the product category (e.g., technical for electronics, lifestyle-focused for fashion).
        - **DO NOT start the description with the product name or a title.**

        ---

        ## **5. Example Outputs**

        ### ✅ **Correct Flat Text Output** (if text format is required):
        {self.description_example_flat}
        ---

        ### ✅ **Correct HTML Output** (if HTML format is required):
        {self.description_example_html}
        ---
        ### 🚫 Incorrect Output (Mixing Text & HTML):
        <p>{self.description_example_flat}</p>
        {self.description_example_html}
        ---

        ## 6. Additional Processing Guidelines

        ✅Follow the format required (Flat Text OR HTML, never both).
        ✅Ensure consistency and completeness: If any product details are missing, infer logically based on available data and image analysis.
        ✅Start with an engaging sentence that introduces benefits rather than the product name or title.
        ✅Ensure compatibility with PIM integration** by maintaining a **clean, structured, and well-written output**
        """

        channel_addition = ""
        if self.sales_channel_type == AMAZON_INTEGRATION:
            channel_addition = """
            ## Amazon Style Guidelines

            You are generating content for an Amazon listing. Please follow these specific rules:

            - Prioritize **keywords** that improve **search visibility**.
            - Keep sentences **short, direct, and feature-focused**.
            - Avoid superlatives or vague statements (e.g., "best", "amazing").
            - Do **not include HTML** unless explicitly allowed (check current context).
            - Avoid any **subjective claims** (e.g., "perfect for everyone").
            - Follow a tone that is **informative and conversion-focused**.

            ⚠️ Ensure all claims are factual and align with Amazon's product detail page policies.
            """
        elif self.sales_channel_type == SHOPIFY_INTEGRATION:
            channel_addition = """
            ## Shopify Style Guidelines

            You are creating a product description for a **Shopify-powered store**:

            - Use an **engaging and branded tone**—feel free to inject personality.
            - Emphasize **lifestyle benefits** and emotional appeal (e.g., comfort, design).
            - Structure with **readability in mind**: use `<h3>`, `<ol>`, and short paragraphs.
            - Focus on **visual imagination**: help the customer picture using the product.
            - Maintain **light HTML structure** for styling and formatting.
            - Can include brand-specific wording, seasonal messaging, and storytelling hooks.

            This is **your own storefront**, so emphasize uniqueness and customer connection.
            """
        elif self.sales_channel_type == MAGENTO_INTEGRATION:
            channel_addition = """
            ## Magento Style Guidelines

            The description is for a **Magento eCommerce storefront**, typically part of a multi-brand or multi-category site.

            - Focus on **clear specification details** (technical, size, materials).
            - Structure with **headings and bullet points** for fast scanning.
            - Keep the tone **neutral and informative**, suitable for both B2B and B2C customers.
            - Use **HTML tags** for clarity, not decoration.
            - Emphasize **product differentiators**: what sets it apart in catalog context.

            Avoid overly promotional language. Keep it professional and detail-oriented.
            """

        return base_prompt + channel_addition


class BulletPointsLLM(ContentLLMMixin):
    """Generate bullet points for a product."""

    def __init__(self, *args, return_one: bool = False, existing_bullet_points: Optional[List[str]] = None, **kwargs):
        self.return_one = return_one
        self.existing_bullet_points = existing_bullet_points or []
        super().__init__(*args, **kwargs)
        self.bullet_points: list[str] = []

    @property
    def system_prompt(self):
        if self.return_one:
            return (
                "Generate exactly one concise and unique bullet point in the given language "
                "describing the product. Respond ONLY with a JSON array containing a single "
                "string. Do not repeat or rephrase any of the existing bullet points."
            )

        return (
            "Generate a short list (max 5 items) of concise bullet points in the "
            "given language describing the product. Respond ONLY with a JSON array "
            "of strings."
        )

    @property
    def prompt(self):
        prompt = f"""
        ##Language Code##
        {self.language_code}

        ##Product name##
        {self.product_name}

        ##Product attributes##
        {self.property_values}
        """

        if self.short_description:
            prompt += f"""
            ##Product Short Description##
            {self.short_description}
            """
        if self.brand_prompt:
            prompt += f"""
            ##Brand Personality##
            {self.brand_prompt}
            """

        if self.return_one:
            prompt += "\n##Instructions##\nGenerate a single additional bullet point that complements the product.\n"
            if self.existing_bullet_points:
                existing = "\n".join(self.existing_bullet_points)
                prompt += f"""
                ##Existing Bullet Points##
                {existing}
                \nEnsure the new bullet point is unique and does not repeat or rephrase any of the existing ones.
                """
            else:
                prompt += "Ensure the bullet point is unique.\n"

        if self.sales_channel_type == AMAZON_INTEGRATION:
            prompt += """
            ##Amazon Bullet Point Guidelines##
            These bullet points will be published on an Amazon product detail page. Follow these rules:
            - Highlight concrete product features and benefits with customer-focused language.
            - Keep each bullet point under 200 characters and avoid special characters or emojis.
            - Do not include pricing, promotions, shipping information, or subjective claims.
            - Maintain a professional, informative tone optimized for keyword visibility.
            """
        return prompt

    def parse_response(self):
        import json
        import re

        try:
            parsed = json.loads(self.text_response)
            if isinstance(parsed, list):
                self.bullet_points = [item.strip().strip('",') for item in parsed if isinstance(item, str)]
                return
        except Exception:
            pass

        lines = self.text_response.splitlines()
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # Skip code fences and brackets
            if not line or line in ('```', '```json', '[', ']'):
                continue

            # Remove starting bullet marks and whitespace
            line = re.sub(r'^[-•\t ]+', '', line)

            # Remove trailing commas and surrounding quotes
            line = line.strip().strip('",')

            if line:
                cleaned_lines.append(line)

        self.bullet_points = cleaned_lines
