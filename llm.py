from google import genai
from google.genai import types
import os
from pydantic import BaseModel
import json
from enum import Enum

class ExpenseCategory(Enum):
    SERVICES = "Serviços"
    TRAVEL = "Viagens"
    GROCERIES = "Mercado"
    RESTAURANTS = "Restaurantes"
    BILLS = "Contas"
    OTHER = "Outros"
    

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
'''
chat = client.chats.create(model="gemini-2.5-flash")

response = chat.send_message("You are a financial assistant chatbot. Return following requests as a JSON object matching an implemented command.\
    If the command is not recognized, return the string 'Sorry, I do not understand'.\
    Accepted commands and JSON examples:\
        New transaction:\
        {\
            'command' = 'register',\
            'value' = Monetary Input Value, numeric value only\
        } ",
)
'''


class UserTransactions(BaseModel):
    value: int
    category: ExpenseCategory







def msg_processing(msg: str):

    #prompt = "Extract the monetary value specified in the following message and convert to cents, returning 0 if no value specified. Also, include a short description, returning an empty string if nothing is provided: "
    prompt = '''Você é um chatbot assistente financeiro.O usuário enviou uma mensagem descrevendo uma transação. Analise a mensagem e forneça:
    1)O valor descrito na transação, em centavos, retornando 0 se nenhum valor foi descrito.
    2)A categoria da transação, retornando "Outros" caso não se encaixe em nenhuma alternativa'''
    prompt = prompt + msg
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=UserTransactions,
        ),
    )
    print(response.parsed)
    print("Output: " + response.text)
    return response.text

def voice_processing(audio_path):
    prompt = '''Você é um chatbot assistente financeiro.O usuário enviou uma mensagem descrevendo uma transação. Analise a mensagem e forneça:
    1)O valor descrito na transação, em centavos, retornando 0 se nenhum valor foi descrito.
    2)A categoria da transação, retornando "Outros" caso não se encaixe em nenhuma alternativa'''

    '''
    my_file = client.files.upload(file=audio_path)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            prompt,
            my_file,
        ],
        config={
        "response_mime_type": "application/json",
        "response_schema": UserTransactions,
    },
    )
    '''
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            prompt,
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type='audio/ogg',
            ),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=UserTransactions,
        ),
    )

    return response.text

def photo_processing(photo_path):
    prompt = '''Você é um chatbot assistente financeiro. O usuário enviou uma imagem descrevendo uma transação. Analise a mensagem e forneça:
    1)O valor total descrito na transação, em centavos, retornando 0 se nenhum valor foi descrito.
    Se a imagem descrever múltiplos itens, como por exemplo uma nota fiscal de supermercado, retorne o valor total.
    Se forem listados descontos, subtraia do valor total
    2)A categoria da transação, retornando "Outros" caso não se encaixe em nenhuma alternativa'''

    '''
    my_file = client.files.upload(file=audio_path)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            prompt,
            my_file,
        ],
        config={
        "response_mime_type": "application/json",
        "response_schema": UserTransactions,
    },
    )
    '''
    with open(photo_path, 'rb') as f:
        photo_bytes = f.read()
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            prompt,
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type='image/jpeg',
            ),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=UserTransactions,
        ),

    )

    return response.text

query_parameters_function = {
    "name": "query_parameters",
    "description": "Returns the parameters for an SQL query",
    "parameters": {
        "type": "object",
        "properties": {
            "min_value": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of people attending the meeting.",
            },
            "max_value": {
                "type": "string",
                "description": "Date of the meeting (e.g., '2024-07-29')",
            },
            "min_date": {
                "type": "string",
                "description": "Time of the meeting (e.g., '15:00')",
            },
            "max_date": {
                "type": "string",
                "description": "The subject or topic of the meeting.",
            },
        },
        "required": ["min_value", "max_value", "min_date", "max_date"],
    },
}

def query():
    print("Query")

def transaction():
    print("Transaction")

def query_processing(msg):
    config = types.GenerateContentConfig(
        tools=[query, transaction],
    )
    prompt = "Você é um chatbot assistente financeiro. O usuário enviou uma mensagem onde ele descreve uma transação ou uma consulta a um banco de dados.\
                 Determine a funçao adequada para o tratamento da mensagem."
    prompt = prompt + msg
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )
    print(response.text)

def function_request():
    pass