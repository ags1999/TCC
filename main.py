import asyncio
from dotenv import load_dotenv
import logging
import os
import telegram
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler


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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def main():
    api_token = config["TELEGRAM_API_TOKEN"]
    bot = telegram.Bot(api_token)
    async with bot:
        updates = (await bot.get_updates())[0]
        print(updates)
        await bot.send_message(text='Hi John!', chat_id=1895118626)


if __name__ == '__main__':

    asyncio.run(main())
    #application = ApplicationBuilder().token(api_token).build()
    
    #start_handler = CommandHandler('start', start)
    #application.add_handler(start_handler)
    
    #application.run_polling()