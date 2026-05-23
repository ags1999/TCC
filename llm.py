from google import genai
from google.genai import types
import os
import logging
from pydantic import BaseModel
import json
from enum import Enum

logger = logging.getLogger(__name__)


class ExpenseCategory(Enum):
    SERVICES    = "Serviços"
    TRAVEL      = "Viagens"
    GROCERIES   = "Mercado"
    RESTAURANTS = "Restaurantes"
    BILLS       = "Contas"
    OTHER       = "Outros"


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class UserTransactions(BaseModel):
    value: int
    category: ExpenseCategory


# ─── Prompt base ─────────────────────────────────────────────────────────────

_PROMPT_TEXT = (
    "Você é um chatbot assistente financeiro. O usuário enviou uma mensagem descrevendo "
    "uma transação. Analise a mensagem e forneça:\n"
    "1) O valor descrito na transação, em centavos, retornando 0 se nenhum valor foi descrito.\n"
    "2) A categoria da transação, retornando 'Outros' caso não se encaixe em nenhuma alternativa."
)

_PROMPT_PHOTO = (
    "Você é um chatbot assistente financeiro. O usuário enviou uma imagem descrevendo uma "
    "transação. Analise a imagem e forneça:\n"
    "1) O valor total descrito na transação, em centavos, retornando 0 se nenhum valor foi descrito. "
    "Se a imagem descrever múltiplos itens (ex: nota fiscal de supermercado), retorne o valor total. "
    "Se forem listados descontos, subtraia do valor total.\n"
    "2) A categoria da transação, retornando 'Outros' caso não se encaixe em nenhuma alternativa."
)

_SCHEMA_CONFIG = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=UserTransactions,
)

_FALLBACK = json.dumps({"value": 0, "category": "Outros"})


# ─── Funções de processamento ─────────────────────────────────────────────────

async def msg_processing(msg: str) -> str:
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=_PROMPT_TEXT + msg,
            config=_SCHEMA_CONFIG,
        )
        logger.info(f"msg_processing concluído: {response.text}")
        return response.text
    except Exception as e:
        logger.error(f"Erro em msg_processing(): {e}", exc_info=True)
        return _FALLBACK


async def voice_processing(audio_path: str) -> str:
    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        if not audio_bytes:
            raise ValueError(f"Arquivo de áudio vazio: {audio_path}")

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                _PROMPT_TEXT,
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
            ],
            config=_SCHEMA_CONFIG,
        )
        logger.info(f"voice_processing concluído: {response.text}")
        return response.text
    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado em voice_processing(): {e}")
        return _FALLBACK
    except ValueError as e:
        logger.error(f"Arquivo inválido em voice_processing(): {e}")
        return _FALLBACK
    except Exception as e:
        logger.error(f"Erro inesperado em voice_processing(): {e}", exc_info=True)
        return _FALLBACK


async def photo_processing(photo_path: str) -> str:
    try:
        if not os.path.exists(photo_path):
            raise FileNotFoundError(f"Arquivo de imagem não encontrado: {photo_path}")
        with open(photo_path, "rb") as f:
            photo_bytes = f.read()
        if not photo_bytes:
            raise ValueError(f"Arquivo de imagem vazio: {photo_path}")

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                _PROMPT_PHOTO,
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
            ],
            config=_SCHEMA_CONFIG,
        )
        logger.info(f"photo_processing concluído: {response.text}")
        return response.text
    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado em photo_processing(): {e}")
        return _FALLBACK
    except ValueError as e:
        logger.error(f"Arquivo inválido em photo_processing(): {e}")
        return _FALLBACK
    except Exception as e:
        logger.error(f"Erro inesperado em photo_processing(): {e}", exc_info=True)
        return _FALLBACK


# ─── Function Calling (em desenvolvimento) ────────────────────────────────────

def query():
    print("Query")


def transaction():
    print("Transaction")


def query_processing(msg: str):
    try:
        config = types.GenerateContentConfig(tools=[query, transaction])
        prompt = (
            "Você é um chatbot assistente financeiro. O usuário enviou uma mensagem onde "
            "descreve uma transação ou uma consulta a um banco de dados. "
            "Determine a função adequada para o tratamento da mensagem. "
        ) + msg
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        logger.info(f"query_processing concluído: {response.text}")
        return response.text

    except Exception as e:
        logger.error(f"Erro em query_processing(): {e}", exc_info=True)
        return None