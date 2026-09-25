import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ping_model():
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Dis bonjour en une phrase."
    )
    return response.text