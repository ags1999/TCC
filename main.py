import asyncio
from dotenv import load_dotenv
import logging
import os
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import llm


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

#Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

#Responses

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str =update.message.chat.type
    msg_text:str = update.message.text
    llm.msg_processing(msg_text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg_text)



if __name__ == '__main__':
    print("Starting bot...")

    application = ApplicationBuilder().token(api_token).build()
    
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT, handle_message)

    application.add_handler(start_handler)
    application.add_handler(msg_handler)

    print("Polling...")
    application.run_polling(poll_interval=3)