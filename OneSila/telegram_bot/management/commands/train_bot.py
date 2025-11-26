from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import shutil


from telegram_bot.bot import bot, Update

class Command(BaseCommand):
    help = ("Run the telegram bot poll")

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        import spacy
        import json
        from spacy.training import Example

        # ✅ Load the pre-trained spaCy model instead of a blank model
        nlp = spacy.load("en_core_web_sm")

        if "textcat_multilabel" not in nlp.pipe_names:
            textcat = nlp.add_pipe("textcat_multilabel", last=True)
        else:
            textcat = nlp.get_pipe("textcat_multilabel")
        
        with open("telegram_bot/training_data.json", "r") as f:
            training_data = json.load(f)

        # Add new intent labels
        for intent_data in training_data["intents"]:
            textcat.add_label(intent_data["intent"])

        nlp.initialize()

        # Prepare training examples
        examples = []
        for intent_data in training_data["intents"]:
            for example_text in intent_data["examples"]:
                doc = nlp.make_doc(example_text)
                cats = {label: 1.0 if label == intent_data["intent"] else 0.0 for label in textcat.labels}
                example = Example.from_dict(doc, {"cats": cats})
                examples.append(example)

        # Initialize the model before training
        # nlp.initialize(lambda: examples)

        # Train the model
        optimizer = nlp.create_optimizer()

        for i in range(20):  # Train for 10 iterations
            losses = {}
            for example in examples:
                nlp.update([example], sgd=optimizer, losses=losses)
            print(f"Iteration {i+1}, Loss: {losses}")

        # Save the updated model
        nlp.to_disk("telegram_bot/en_core_web_sm_james_extend_model")
        print("Training completed! Model saved as 'telegram_bot/en_core_web_sm_james_extend_model'")