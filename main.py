from pydantic import BaseModel
import os
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, Response
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
conversation_memory = {}

# Provide your menu structure or load from JSON/CSV here
MENU_TEXT = """
Menu:
- Boneless Wings (6,10,20) - $12.99, $19.99, $34.99
- Traditional Wings (6,10,20) - $11.99, $18.99, $32.99
- French Fries - $4.99
- Mozzarella Sticks - $7.49
- Soft Drinks (Pepsi, Sprite) - $2.49
"""

SYSTEM_PROMPT = f"""
You're an AI ordering assistant. Here's the menu you reference:\n{MENU_TEXT}
Ask clarifying questions, confirm the order, and repeat total price.
"""

class ChatInput(BaseModel):
    user_id: str
    message: str


from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/order")
async def order(input: ChatInput):
    user_id = input.user_id
    memory = conversation_memory.get(user_id, [])
    memory.append({"role": "user", "content": input.message})

    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + memory,
    )

    reply = chat_completion.choices[0]["message"]["content"]
    memory.append({"role": "assistant", "content": reply})
    conversation_memory[user_id] = memory

    return JSONResponse(content={"reply": reply})

@app.post("/voice")
async def voice(
    SpeechResult: str = Form(None),
    From: str = Form(...),
):
    if SpeechResult:
        # Proxy to the /order function for consistency
        try:
            chat_resp = await order(ChatInput(user_id=From, message=SpeechResult))
            reply_json = await chat_resp.json()
            reply_text = reply_json.get("reply", "Sorry, I didn’t understand that.")
        except Exception as e:
            reply_text = f"There was an error: {str(e)}"
    else:
        reply_text = "Hi! Welcome to Buffalo Wild Wings. What would you like to order today?"

    response = ET.Element("Response")
    gather = ET.SubElement(
        response,
        "Gather",
        input="speech",
        action="/voice",
        method="POST",
        timeout="3"
    )
    ET.SubElement(gather, "Say").text = reply_text
    ET.SubElement(response, "Say").text = "Goodbye."
    ET.SubElement(response, "Hangup")
    return Response(content=ET.tostring(response), media_type="application/xml")
