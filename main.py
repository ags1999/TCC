# import asyncio
from dotenv import load_dotenv
import logging
import os
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import llm
import dbmanager
import json
from datetime import datetime, timezone

def load_environment_variables():
    try:
        # Load variables from .env file into environment
        load_dotenv()
        
        # Retrieve specific environment variables
        api_token = os.getenv("TELEGRAM_API_TOKEN")
        
        # Validate critical variables
        if not all([api_token]):
            raise ValueError("Missing critical environment variables")
        
        return {
            "TELEGRAM_API_TOKEN": api_token
        }
    
    except Exception as e:
        print(f"Error loading environment variables: {e}")
        return None


config = load_environment_variables()
api_token = config["TELEGRAM_API_TOKEN"]


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

keyboard = [
    [
        InlineKeyboardButton("Confirmar", callback_data="1"),

    ],
    [
        InlineKeyboardButton("Editar", callback_data="2"),

    ],
    [
        InlineKeyboardButton("Cancelar", callback_data="3"),
    ],
]

reply_markup = InlineKeyboardMarkup(keyboard)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    match query.data:
        case "1":
            response = context.user_data["transaction"]
            dbmanager.register_transaction(response)
            await query.edit_message_text(text="Transação Confirmada")

        case "2":
            pass
        case "3":
            await query.edit_message_text(text="Transação Cancelada")
    #await query.edit_message_text(text=f"Selected option: {query.data}", reply_markup=reply_markup)

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_msg = "Olá, eu sou o LedgerBot, seu assistente financeiro inteligente!"
    #await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=start_msg)

# Responses


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_name = update.message.chat.effective_name
    dbmanager.register_user(user_id, user_name)



    
    message_type: str =update.message.chat.type
    msg_text: str = update.message.text
    response = llm.msg_processing(msg_text)
    response = json.loads(response)
    response["ID"] = user_id
    date = update.message.date
    print(date)
    context.user_data["transaction"] = response
    reply = f'''Valor:R${response["value"]/100:.2f}\nCategoria:{response["category"]}'''
    await update.message.reply_text(reply, reply_markup=reply_markup)



if __name__ == '__main__':
    print("Starting bot...")

    application = ApplicationBuilder().token(api_token).build()
    
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT, handle_message)
    button_handler = CallbackQueryHandler(button)

    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    application.add_handler(button_handler)

    print("Polling...")
    application.run_polling(poll_interval=3)
