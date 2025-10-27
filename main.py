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
        InlineKeyboardButton("Confirmar", callback_data="Confirmar"),

    ],
    [
        InlineKeyboardButton("Editar", callback_data="Editar"),

    ],
    [
        InlineKeyboardButton("Cancelar", callback_data="Cancelar"),
    ],
]

field_edit_buttons = [
    [
        InlineKeyboardButton("Valor", callback_data="Valor"),

    ],
    [
        InlineKeyboardButton("Categoria", callback_data="Categoria"),

    ],

]

category_buttons = [
    [
        InlineKeyboardButton("Serviços", callback_data="Serviços"),

    ],
    [
        InlineKeyboardButton("Viagens", callback_data="Viagens"),

    ],
    [
        InlineKeyboardButton("Mercado", callback_data="Mercado"),
    ],
    [
        InlineKeyboardButton("Restaurantes", callback_data="Restaurantes"),

    ],
    [
        InlineKeyboardButton("Contas", callback_data="Contas"),

    ],
    [
        InlineKeyboardButton("Outros", callback_data="Outros"),
    ],
]


numeric_keyboard = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['.', '0', '←'],
    ['OK'],# Include decimal point and Done button
]

reply_markup = InlineKeyboardMarkup(keyboard)

numeric_keyboard_markup = ReplyKeyboardMarkup(
    numeric_keyboard,
    resize_keyboard=True,  # Make keyboard smaller to fit screen
)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    response = context.user_data["transaction"]
    # CallbackQueries need to be answered, even if no notification to the user is needed
    
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    match query.data:
        case "Confirmar":
            response = context.user_data["transaction"]
            dbmanager.register_transaction(response)
            await query.edit_message_text(text="Transação Confirmada")

        case "Editar":
            await query.edit_message_text(text="Selecione o campo para correção",reply_markup=InlineKeyboardMarkup(field_edit_buttons))
        case "Cancelar":
            await query.edit_message_text(text="Transação Cancelada")
        case "Valor":
            await query.edit_message_text(text="Editar",reply_markup=numeric_keyboard_markup)
        case "Categoria":
            await query.edit_message_text(text="Editar",reply_markup=InlineKeyboardMarkup(category_buttons))
        case "Serviços"|"Viagens"|"Mercado"|"Restaurantes"|"Contas"|"Outros":
            response["category"] = query.data
            context.user_data["transaction"] = response
            reply = f'''Valor:R${response["value"]/100:.2f}\nCategoria:{response["category"]}'''
            await query.edit_message_text(reply, reply_markup=reply_markup)    
        case num if 0 <= num <=9:
            context.user_data["new_value"] = context.user_data["new_value"]*10 + num
            await query.edit_message_text(text="Editar",reply_markup=InlineKeyboardMarkup(category_buttons))
            

            
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
    context.user_data["new_value"] = 0
    reply = f'''Valor:R${response["value"]/100:.2f}\nCategoria:{response["category"]}'''
    await update.message.reply_text(reply, reply_markup=reply_markup)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_name = update.message.chat.effective_name
    dbmanager.register_user(user_id, user_name)
    msg = update.message.voice
    llm.voice_processing(msg)

if __name__ == '__main__':
    print("Starting bot...")

    application = ApplicationBuilder().token(api_token).build()
    
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT, handle_message)
    button_handler = CallbackQueryHandler(button)
    voice_handler = MessageHandler(filters.VOICE, handle_voice)

    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    application.add_handler(button_handler)
    application.add_handler(voice_handler)

    print("Polling...")
    application.run_polling(poll_interval=3)
