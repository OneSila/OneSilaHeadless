# FIXME: This bot really needs ensuring a user is actually part of the admin-team.

import logging
from typing import TYPE_CHECKING

import spacy
from telegram import Update
from telegram.ext import filters, Application, CommandHandler, MessageHandler, CallbackContext,\
    ApplicationBuilder
from django.conf import settings
from .actions import restart_huey
from core.models.multi_tenant import MultiTenantUser

logger = logging.getLogger(__name__)

# Load default spaCy model
nlp = spacy.load("en_core_web_sm")
# try:
#     nlp = spacy.load("en_core_web_sm")
# except OSError:
#     logger.warning("spaCy model en_core_web_sm missing; using blank 'en' pipeline.")
#     nlp = spacy.blank("en")
# nlp = spacy.load("telegram_bot/en_core_web_sm_james_extend_model")

# Store user context
user_context = {}

INTENTS = {
    "greeting": [
        "Hi", "Hello", "Hey", "Good morning", "Hi there", "What's up?", "Yo",
        "Hello bot", "Hey assistant", "Hi friend", "Hello, how are you?", "Greetings!", "Howdy"
    ],
    "goodbye": [
        "See you later", "Goodbye!", "Take care", "Bye!", "Later!", "See you soon",
        "I'm off", "Catch you later", "Good night", "Farewell"
    ],
    "weather": [
        "What's the weather like?", "Tell me the forecast", "Is it hot today?", "Will it rain?",
        "How's the weather?", "Do I need an umbrella?", "What's the humidity?",
        "Give me the weather update", "What's the temperature?", "Is it sunny outside?"
    ],
    "restart_huey": [
        "Restart huey", "Restart the task queue", "Reset the workers", "Restart background jobs",
        "Refresh huey", "Restart the worker process", "Restart task execution",
        "Reboot the Huey process", "Restart Huey now", "Kill and restart the Huey service",
        "Restart the job queue process", "Flush and restart Huey"
    ]
}

def detect_intent(user_message):
    """Detects user intent based on keyword matching and lemmatization."""
    user_message = user_message.lower().strip()
    doc = nlp(user_message)

    for intent, phrases in INTENTS.items():
        # Direct substring match (e.g., "hello" matches "Hello bot")
        if any(phrase.lower() in user_message for phrase in phrases):
            return intent

        # Lemmatized word match (handles variations like "restarting huey" → "restart_huey")
        if any(token.lemma_ in [phrase.lower() for phrase in phrases] for token in doc):
            return intent

    return None  # No match found

def detect_intent_from_training_data(user_message):
    """Uses the trained spaCy model to predict user intent."""
    if not user_message or not isinstance(user_message, str):
        logger.warning("Received invalid user input for intent detection.")
        return None

    doc = nlp(user_message.lower().strip())  # Process input with the trained model

    if not doc.cats:  # Ensure predictions exist
        logger.debug(f"No intent predictions found for '{user_message}'")
        return None

    # Get the intent with the highest confidence score
    predicted_intent = max(doc.cats, key=doc.cats.get)
    confidence = doc.cats[predicted_intent]

    logger.debug(f"Intent prediction for '{user_message}': {predicted_intent} (Confidence: {confidence:.4f})")

    # Apply confidence threshold
    return predicted_intent if confidence > 0.7 else None  # Adjust threshold if needed


def _build_user_creation_message(*, user: "MultiTenantUser") -> str:
    company = getattr(user, "multi_tenant_company", None)
    lines = [
        "🚀 New user registered",
        f"Email: {user.username}",
    ]

    if company:
        lines.append(f"Company: {company.name}")
        if company.language:
            language_label = getattr(company, "get_language_display", lambda: company.language)()
            lines.append(f"Company language: {language_label} ({company.language})")
        if company.full_address:
            lines.append(f"Company address: {company.full_address}")
        lines.append(f"Company id: {company.id}")
    else:
        lines.append("Company: No company linked yet.")

    return "\n".join(lines)


async def notify_new_user_creation(*, chat_id: str, user: "MultiTenantUser"):

    if not bot:
        logger.warning("Telegram bot token missing; cannot notify admins for %s", user)
        return

    if not chat_id:
        logger.warning("Empty chat id for Telegram notification about %s", user)
        return

    message = _build_user_creation_message(user=user)
    await bot.bot.send_message(chat_id=chat_id, text=message)


# Telegram command: /start
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    user_context[user_id] = {}  # Reset context
    await update.message.reply_text("Hi! I'm James. Ask me something!")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    user_message = update.message.text

    # Check if waiting for follow-up
    if user_id in user_context and "awaiting" in user_context[user_id]:
        if user_context[user_id]["awaiting"] == "weather_location":
            location = user_message
            user_context[user_id] = {}  # Clear context
            await update.message.reply_text(f"Fetching the weather for {location}... Cold as snow!")
            return

    intent = detect_intent(user_message)

    # Handle different intents
    if intent == "weather":
        user_context[user_id] = {"awaiting": "weather_location"}
        await update.message.reply_text("Where?")
    elif intent == "greeting":
        await update.message.reply_text("Hello! How can I assist you?")
    elif intent == "goodbye":
        await update.message.reply_text("Goodbye! Have a great day!")
    elif intent == "restart_huey":
        await update.message.reply_text("Restarting Huey!")
        resp = await restart_huey()
        await update.message.reply_text(f"Restart received: {resp}")
    else:
        await update.message.reply_text("I don't understand that.")


async def error_handler(update: Update, context: CallbackContext):
    logger.warning(f"Update {update} caused error {context.error}")



bot = None
if getattr(settings, "TELEGRAM_BOT_TOKEN", None):
    bot = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    bot.add_error_handler(error_handler)
    logger.info("James is now polling for messages...")
else:
    logger.warning("TELEGRAM_BOT_TOKEN is not configured; Telegram bot is disabled.")
