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
    prompt = '''Você é um chatbot assistente financeiro.O usuário enviou uma mensagem descrevendo uma transação. Analize a mensagem e forneça:
    1)O valor descrito na transação, em centavos, retornando 0 se nenhum valor foi descrito.
    2)A categoria da transação, retornando "Outros" caso não se encaixe em nenhuma alternativa'''
    prompt = prompt + msg
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_schema": UserTransactions,
    },
    )   
    print(response.parsed)
    print("Output: " + response.text)
    return response.text

'''
print(response.text)


response = chat.send_message("Gastei 581,25 reais")
print("Test Input")
print(response.text)

response = chat.send_message("Fui ao parque")
print("Test Input 2")
print(response.text)

#for message in chat.get_history():
#    print(f'role - {message.role}',end=": ")
#    print(message.parts[0].text)
'''