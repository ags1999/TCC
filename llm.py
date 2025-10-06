from google import genai
from google.genai import types
import os
from pydantic import BaseModel

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
    transaction_id: int
    user_id: int
    value: int

def msg_processing(msg: str):

    prompt = "Extract the monetary value specified in the following message and convert to cents, returning 0 if no value specified: "
    prompt = prompt + msg
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_schema": int,
    },
    )   

    print("Value: " + response.text)
    return 0

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