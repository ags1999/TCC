import asyncio
from dotenv import load_dotenv
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import llm
import dbmanager as dbm
import json
from datetime import datetime


logger = logging.getLogger(__name__)


def load_environment_variables():
    try:
        load_dotenv()
        api_token = os.getenv("TELEGRAM_API_TOKEN")
        if not all([api_token]):
            raise ValueError("Missing critical environment variables")
        return {"TELEGRAM_API_TOKEN": api_token}
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
    [InlineKeyboardButton("Confirmar", callback_data="Confirmar")],
    [InlineKeyboardButton("Editar",    callback_data="Editar")],
    [InlineKeyboardButton("Cancelar",  callback_data="Cancelar")],
]

field_edit_buttons = [
    [InlineKeyboardButton("Valor",     callback_data="Valor")],
    [InlineKeyboardButton("Categoria", callback_data="Categoria")],
]

category_buttons = [
    [InlineKeyboardButton("Serviços",     callback_data="Serviços")],
    [InlineKeyboardButton("Viagens",      callback_data="Viagens")],
    [InlineKeyboardButton("Mercado",      callback_data="Mercado")],
    [InlineKeyboardButton("Restaurantes", callback_data="Restaurantes")],
    [InlineKeyboardButton("Contas",       callback_data="Contas")],
    [InlineKeyboardButton("Outros",       callback_data="Outros")],
]

numeric_keyboard = [
    [InlineKeyboardButton("1", callback_data="1"),
     InlineKeyboardButton("2", callback_data="2"),
     InlineKeyboardButton("3", callback_data="3")],
    [InlineKeyboardButton("4", callback_data="4"),
     InlineKeyboardButton("5", callback_data="5"),
     InlineKeyboardButton("6", callback_data="6")],
    [InlineKeyboardButton("7", callback_data="7"),
     InlineKeyboardButton("8", callback_data="8"),
     InlineKeyboardButton("9", callback_data="9")],
    [InlineKeyboardButton("OK", callback_data="OK"),
     InlineKeyboardButton("0",  callback_data="0"),
     InlineKeyboardButton("←",  callback_data="←")],
]

years = [str(y) for y in range(2025, datetime.today().year + 1)]
years_keyboard = [[InlineKeyboardButton(text=y, callback_data=y)] for y in years]

months = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
]
months_keyboard = [
    [InlineKeyboardButton(text=months[i], callback_data=months[i]),
     InlineKeyboardButton(text=months[i + 1], callback_data=months[i + 1])]
    for i in range(0, len(months), 2)
]

reply_markup          = InlineKeyboardMarkup(keyboard)
numeric_keyboard_markup = InlineKeyboardMarkup(numeric_keyboard)


# ─── Handlers ────────────────────────────────────────────────────────────────

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()

    try:
        if query.data in years:
            context.user_data["year"] = query.data
            await query.edit_message_text(
                text="Selecione o mês",
                reply_markup=InlineKeyboardMarkup(months_keyboard)
            )
            return

        if query.data in months:
            year = context.user_data.get("year")
            if not year:
                await query.edit_message_text(text="Erro: ano não selecionado. Use /consulta novamente.")
                return
            buf = dbm.consulta_ano_mes(
                update.effective_chat.id,
                int(year),
                months.index(query.data) + 1
            )
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_photo(photo=buf)
            return

        response = context.user_data.get("transaction")
        if response is None:
            await query.edit_message_text(
                text="Sessão expirada. Por favor, envie a transação novamente."
            )
            return

        match query.data:
            case "Confirmar":
                dbm.register_transaction(response)
                await query.edit_message_text(text="Transação Confirmada")

            case "Editar":
                await query.edit_message_text(
                    text="Selecione o campo para correção",
                    reply_markup=InlineKeyboardMarkup(field_edit_buttons)
                )

            case "Cancelar":
                await query.edit_message_text(text="Transação Cancelada")

            case "Valor":
                context.user_data["new_value"] = 0
                await query.edit_message_text(
                    text="Digite o novo valor:",
                    reply_markup=numeric_keyboard_markup
                )

            case "Categoria":
                await query.edit_message_text(
                    text="Selecione a categoria:",
                    reply_markup=InlineKeyboardMarkup(category_buttons)
                )

            case "Serviços" | "Viagens" | "Mercado" | "Restaurantes" | "Contas" | "Outros":
                response["category"] = query.data
                context.user_data["transaction"] = response
                reply = f'Valor: R${response["value"] / 100:.2f}\nCategoria: {response["category"]}'
                await query.edit_message_text(reply, reply_markup=reply_markup)

            case _ if query.data.isdigit():
                current = context.user_data.get("new_value", 0)
                context.user_data["new_value"] = current * 10 + int(query.data)
                await query.edit_message_text(
                    text=f'Novo valor:\nR${context.user_data["new_value"] / 100:.2f}',
                    reply_markup=numeric_keyboard_markup
                )

            case "←":
                # Divisão inteira para evitar imprecisão de ponto flutuante
                current = context.user_data.get("new_value", 0)
                context.user_data["new_value"] = current // 10
                await query.edit_message_text(
                    text=f'Novo valor:\nR${context.user_data["new_value"] / 100:.2f}',
                    reply_markup=numeric_keyboard_markup
                )

            case "OK":
                response["value"] = context.user_data.get("new_value", 0)
                context.user_data["transaction"] = response
                context.user_data["new_value"] = 0
                reply = f'Valor: R${response["value"] / 100:.2f}\nCategoria: {response["category"]}'
                await query.edit_message_text(reply, reply_markup=reply_markup)

    except KeyError as e:
        logger.error(f"Chave ausente ao processar callback: {e}")
        await query.edit_message_text(
            text="Erro interno: dados da transação incompletos. Por favor, envie a transação novamente."
        )
    except Exception as e:
        logger.error(f"Erro inesperado em button(): {e}", exc_info=True)
        await query.edit_message_text(
            text="Ocorreu um erro inesperado. Por favor, tente novamente."
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_msg = (
        "Olá, eu sou o LedgerBot, seu assistente financeiro inteligente! "
        "Eu posso reconhecer e armazenar seus gastos através de mensagens de texto, voz "
        "e fotos, e gerar gráficos para consulta. Para ver os comandos disponíveis, digite /help."
    )
    try:
        user_id   = update.message.chat.id
        user_name = update.message.chat.effective_name
        dbm.register_user(user_id, user_name)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=start_msg)
    except Exception as e:
        logger.error(f"Erro em start(): {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ocorreu um erro ao iniciar. Por favor, tente novamente."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = (
        "🤖 *LedgerBot — Comandos e Funcionalidades*\n\n"

        "📥 *Registrar uma transação*\n"
        "Envie uma mensagem descrevendo seu gasto em qualquer um dos formatos:\n"
        "• *Texto:* \"Gastei 45 reais no mercado\"\n"
        "• *Voz:* grave um áudio descrevendo o gasto\n"
        "• *Foto:* tire uma foto do cupom fiscal ou da tela de pagamento\n\n"
        "O bot vai extrair o valor e a categoria automaticamente e pedir sua confirmação.\n\n"

        "✏️ *Confirmar ou editar uma transação*\n"
        "Após enviar um gasto, você verá três opções:\n"
        "• *Confirmar* — salva a transação\n"
        "• *Editar* — corrige o valor ou a categoria antes de salvar\n"
        "• *Cancelar* — descarta a transação\n\n"

        "🗂️ *Categorias disponíveis*\n"
        "Serviços · Viagens · Mercado · Restaurantes · Contas · Outros\n\n"

        "📊 *Consultar gastos — /consulta*\n"
        "Gera um gráfico de pizza com seus gastos agrupados por categoria.\n"
        "Selecione o ano e o mês desejados nos menus que aparecerem.\n\n"

        "❓ *Ajuda — /help*\n"
        "Exibe esta mensagem.\n\n"

        "💡 *Dica:* o bot entende linguagem natural — não precisa seguir um formato fixo!"
    )
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_msg,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Erro em help_command(): {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Não foi possível exibir a ajuda. Tente novamente."
        )

async def consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Selecione o ano",
            reply_markup=InlineKeyboardMarkup(years_keyboard)
        )
    except Exception as e:
        logger.error(f"Erro em consulta(): {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Não foi possível iniciar a consulta. Tente novamente."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id   = update.message.chat.id
    user_name = update.message.chat.effective_name

    try:
        dbm.register_user(user_id, user_name)

        msg_text = update.message.text
        try:
            raw = await asyncio.wait_for(
                llm.msg_processing(msg_text),
                timeout=30.0  # segundos
            )
        except asyncio.TimeoutError:
            logger.error("Timeout na chamada à API Gemini")
            await update.message.reply_text(
                "A IA demorou demais para responder. Tente novamente."
            )
            return
        response = json.loads(raw)

        if "value" not in response or "category" not in response:
            raise KeyError("Campos 'value' ou 'category' ausentes na resposta da IA.")

        response["ID"]   = user_id
        response["date"] = update.message.date
        context.user_data["transaction"] = response
        context.user_data["new_value"]   = 0

        reply = f'Valor: R${response["value"] / 100:.2f}\nCategoria: {response["category"]}'
        await update.message.reply_text(reply, reply_markup=reply_markup)

    except json.JSONDecodeError as e:
        logger.error(f"Resposta da IA não é JSON válido: {e}")
        await update.message.reply_text(
            "Não consegui interpretar sua mensagem. Tente descrevê-la de outra forma."
        )
    except KeyError as e:
        logger.error(f"Campo ausente na resposta da IA: {e}")
        await update.message.reply_text(
            "Não consegui extrair os dados da transação. Tente ser mais específico."
        )
    except Exception as e:
        logger.error(f"Erro inesperado em handle_message(): {e}", exc_info=True)
        await update.message.reply_text(
            "Ocorreu um erro ao processar sua mensagem. Tente novamente."
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ogg_path  = None
    user_id   = update.message.chat.id
    user_name = update.message.chat.effective_name

    try:
        dbm.register_user(user_id, user_name)

        voice   = update.message.voice
        chat_id = update.effective_chat.id

        os.makedirs("data", exist_ok=True)
        ogg_file = await context.bot.get_file(voice.file_id)
        ogg_path = f"data/{chat_id}.ogg"
        await ogg_file.download_to_drive(ogg_path)

        if not os.path.exists(ogg_path):
            raise FileNotFoundError(f"Arquivo não encontrado após download: {ogg_path}")

        try:
            raw = await asyncio.wait_for(
                llm.voice_processing(ogg_path),
                timeout=30.0  # segundos
            )
        except asyncio.TimeoutError:
            logger.error("Timeout na chamada à API Gemini")
            await update.message.reply_text(
                "A IA demorou demais para responder. Tente novamente."
            )
            return

        response = json.loads(raw)

        if "value" not in response or "category" not in response:
            raise KeyError("Campos 'value' ou 'category' ausentes na resposta da IA.")

        response["ID"]   = user_id
        response["date"] = update.message.date
        context.user_data["transaction"] = response
        context.user_data["new_value"]   = 0

        reply = f'Valor: R${response["value"] / 100:.2f}\nCategoria: {response["category"]}'
        await update.message.reply_text(reply, reply_markup=reply_markup)

    except FileNotFoundError as e:
        logger.error(f"Arquivo de voz não encontrado: {e}")
        await update.message.reply_text(
            "Não foi possível baixar o áudio. Tente novamente."
        )
    except json.JSONDecodeError as e:
        logger.error(f"Resposta da IA não é JSON válido (voz): {e}")
        await update.message.reply_text(
            "Não consegui interpretar o áudio. Tente enviar uma mensagem de texto."
        )
    except KeyError as e:
        logger.error(f"Campo ausente na resposta da IA (voz): {e}")
        await update.message.reply_text(
            "Não consegui extrair os dados do áudio. Tente ser mais específico."
        )
    except Exception as e:
        logger.error(f"Erro inesperado em handle_voice(): {e}", exc_info=True)
        await update.message.reply_text(
            "Ocorreu um erro ao processar seu áudio. Tente novamente."
        )
    finally:
        if ogg_path and os.path.exists(ogg_path):
            try:
                os.remove(ogg_path)
            except Exception as cleanup_error:
                logger.warning(f"Erro ao remover arquivo temporário {ogg_path}: {cleanup_error}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_path = None
    user_id    = update.message.chat.id
    user_name  = update.message.chat.effective_name

    try:
        dbm.register_user(user_id, user_name)

        photo = update.message.photo[-1]
        file  = await photo.get_file()

        os.makedirs("data", exist_ok=True)
        photo_path = f"data/{photo.file_id}"
        await file.download_to_drive(photo_path)

        if not os.path.exists(photo_path):
            raise FileNotFoundError(f"Arquivo não encontrado após download: {photo_path}")

        try:
            raw = await asyncio.wait_for(
                llm.photo_processing(photo_path),
                timeout=30.0  # segundos
            )
        except asyncio.TimeoutError:
            logger.error("Timeout na chamada à API Gemini")
            await update.message.reply_text(
                "A IA demorou demais para responder. Tente novamente."
            )
            return

        response = json.loads(raw)

        if "value" not in response or "category" not in response:
            raise KeyError("Campos 'value' ou 'category' ausentes na resposta da IA.")

        response["ID"]   = user_id
        response["date"] = update.message.date
        context.user_data["transaction"] = response
        context.user_data["new_value"]   = 0

        reply = f'Valor: R${response["value"] / 100:.2f}\nCategoria: {response["category"]}'
        await update.message.reply_text(reply, reply_markup=reply_markup)

    except FileNotFoundError as e:
        logger.error(f"Arquivo de foto não encontrado: {e}")
        await update.message.reply_text(
            "Não foi possível baixar a imagem. Tente novamente."
        )
    except json.JSONDecodeError as e:
        logger.error(f"Resposta da IA não é JSON válido (foto): {e}")
        await update.message.reply_text(
            "Não consegui interpretar a imagem. Tente uma foto mais nítida ou envie o valor por texto."
        )
    except KeyError as e:
        logger.error(f"Campo ausente na resposta da IA (foto): {e}")
        await update.message.reply_text(
            "Não consegui extrair os dados da imagem. Tente ser mais específico."
        )
    except Exception as e:
        logger.error(f"Erro inesperado em handle_photo(): {e}", exc_info=True)
        await update.message.reply_text(
            "Ocorreu um erro ao processar sua foto. Tente novamente."
        )
    finally:
        if photo_path and os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception as cleanup_error:
                logger.warning(f"Erro ao remover arquivo temporário {photo_path}: {cleanup_error}")


if __name__ == '__main__':  # pragma: no cover
    print("Starting bot...")
    application = ApplicationBuilder().token(api_token).build()

    application.add_handler(CommandHandler('start',    start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('consulta', consulta))
    application.add_handler(MessageHandler(filters.TEXT,  handle_message))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))


    print("Polling...")
    application.run_polling(poll_interval=3)