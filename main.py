# import asyncio
from dotenv import load_dotenv
import logging
import os
#import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import llm
import dbmanager as dbm
import json
from datetime import datetime

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
    [
        InlineKeyboardButton("1", callback_data="1"),
        InlineKeyboardButton("2", callback_data="2"),
        InlineKeyboardButton("3", callback_data="3"),

    ],
    [
        InlineKeyboardButton("4", callback_data="4"),
        InlineKeyboardButton("5", callback_data="5"),
        InlineKeyboardButton("6", callback_data="6"),

    ],
    [
        InlineKeyboardButton("7", callback_data="7"),
        InlineKeyboardButton("8", callback_data="8"),
        InlineKeyboardButton("9", callback_data="9"),

    ],
    [
        InlineKeyboardButton("OK", callback_data="OK"),
        InlineKeyboardButton("0", callback_data="0"),
        InlineKeyboardButton("←", callback_data="←"),

    ],
]


reply_markup = InlineKeyboardMarkup(keyboard)
numeric_keyboard_markup = InlineKeyboardMarkup(numeric_keyboard)

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
            dbm.register_transaction(response)
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
        case _ if query.data.isdigit():
            context.user_data["new_value"] = context.user_data["new_value"]*10 + int(query.data)
            await query.edit_message_text(text=f"Novo valor:\n{context.user_data["new_value"]/100:.2f}", reply_markup=numeric_keyboard_markup)
        case "←":
            context.user_data["new_value"] = context.user_data["new_value"]/10
            await query.edit_message_text(text=f"Novo valor:\n{context.user_data["new_value"]/100:.2f}", reply_markup=numeric_keyboard_markup)
        case "OK":
            response["value"] = context.user_data["new_value"]
            context.user_data["transaction"] = response
            context.user_data["new_value"] = 0
            reply = f'''Valor:R${response["value"] / 100:.2f}\nCategoria:{response["category"]}'''
            await query.edit_message_text(reply, reply_markup=reply_markup)






        #await query.edit_message_text(text=f"Selected option: {query.data}", reply_markup=reply_markup)

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_msg = "Olá, eu sou o LedgerBot, seu assistente financeiro inteligente!"
    #await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=start_msg)

async def consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dbm.retorna_consulta()

# Responses
async def registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_name = update.message.chat.effective_name
    dbm.register_user(user_id, user_name)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_name = update.message.chat.effective_name
    dbm.register_user(user_id, user_name)

    
    message_type: str =update.message.chat.type
    msg_text: str = update.message.text
    response = llm.msg_processing(msg_text)
    response = json.loads(response)
    response["ID"] = user_id
    date = update.message.date
    response["date"] = date
    print(date)
    context.user_data["transaction"] = response
    context.user_data["new_value"] = 0
    reply = f'''Valor: R${response["value"]/100:.2f}\nCategoria:{response["category"]}'''
    await update.message.reply_text(reply, reply_markup=reply_markup)
    #await update.message.reply_text(reply)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ogg_path=None
    user_id = update.message.chat.id
    user_name = update.message.chat.effective_name
    dbm.register_user(user_id, user_name)
    try:
        voice: Voice = update.message.voice
        chat_id = update.effective_chat.id

        # 1. Baixar o arquivo OGG enviado pelo usuário
        os.makedirs("data", exist_ok=True)
        ogg_file = await context.bot.get_file(voice.file_id)
        ogg_path = f"data/{chat_id}.ogg"
        await ogg_file.download_to_drive(ogg_path)
        if not os.path.exists(ogg_path):
            raise FileNotFoundError(f"Arquivo não encontrado após download: {ogg_path}")
        response = llm.voice_processing(ogg_path)
        response = json.loads(response)
        response["ID"] = user_id
        date = update.message.date
        response["date"] = date
        print(date)
        context.user_data["transaction"] = response
        context.user_data["new_value"] = 0
        reply = f'''Valor: R${response["value"] / 100:.2f}\nCategoria:{response["category"]}'''
        await update.message.reply_text(reply, reply_markup=reply_markup)
        #await update.message.reply_text(reply)

    except Exception as e:
        print(f"Erro no processamento de voz: {e}")
        await update.message.reply_text("Desculpe, ocorreu um erro ao processar seu áudio.")

    finally:
    # Limpeza: remover arquivo temporário se existir
        if ogg_path and os.path.exists(ogg_path):
            try:
                os.remove(ogg_path)
            except Exception as cleanup_error:
                print(f"Erro ao remover arquivo temporário {ogg_path}: {cleanup_error}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    photo = update.message.photo[-1]
    file = await photo.get_file()

    # Download the photo
    photo_path = f"data/{photo.file_id}"
    await file.download_to_drive(photo_path)
    #logger.info(f"Photo downloaded to {photo_path}")
    response = llm.photo_processing(photo_path)
    response = json.loads(response)
    response["ID"] = user_id
    date = update.message.date
    response["date"] = date
    print(date)
    context.user_data["transaction"] = response
    context.user_data["new_value"] = 0
    reply = f'''Valor: R${response["value"] / 100:.2f}\nCategoria:{response["category"]}'''
    await update.message.reply_text(reply, reply_markup=reply_markup)
    #await update.message.reply_text(reply)

if __name__ == '__main__':
    llm.query_processing("Gastei 10 reais no mercado")
    llm.query_processing("Mostre todos os gastos")
    print("Starting bot...")

    application = ApplicationBuilder().token(api_token).build()
    
    start_handler = CommandHandler('start', start)
    con_handler = CommandHandler('consulta', consulta)
    msg_handler = MessageHandler(filters.TEXT, handle_message)
    button_handler = CallbackQueryHandler(button)
    voice_handler = MessageHandler(filters.VOICE, handle_voice)
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)

    application.add_handler(start_handler)
    application.add_handler(con_handler)
    application.add_handler(msg_handler)
    application.add_handler(button_handler)
    application.add_handler(voice_handler)
    application.add_handler(photo_handler)

    print("Polling...")
    application.run_polling(poll_interval=3)
