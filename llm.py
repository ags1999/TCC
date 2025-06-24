from google import genai
from google.genai import types
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
