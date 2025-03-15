import asyncio
import spacy
import logging
from telegram import Update
from telegram.ext import filters, Application, CommandHandler, MessageHandler, CallbackContext,\
    ApplicationBuilder
from django.conf import settings

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,  # ✅ Changed to DEBUG to show more logs
)
logger = logging.getLogger("telegram_bot")

# Define intent keywords
INTENTS = {
    "weather": ["weather", "temperature", "forecast", "climate"],
}

def detect_intent(user_message):
    doc = nlp(user_message.lower())
    for intent, keywords in INTENTS.items():
        if any(token.lemma_ in keywords for token in doc):
            return intent
    return None

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hi! I'm James. Ask me something!")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    intent = detect_intent(user_message)

    if intent == "weather":
        await update.message.reply_text("Cold as snow!")
    else:
        await update.message.reply_text("I don't understand that.")

async def error_handler(update: Update, context: CallbackContext):
    logger.warning(f"Update {update} caused error {context.error}")



bot = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

bot.add_handler(CommandHandler("start", start))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

bot.add_error_handler(error_handler)
logger.info("James is now polling for messages...")
