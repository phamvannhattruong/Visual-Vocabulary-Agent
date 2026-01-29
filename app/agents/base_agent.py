import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

class Agent:
    def __init__(self, model = "gemini-2.5-flash"):
        api_key = os.getenv("API_KEY_GEMINI")
        self.gemini = ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=0.7
        )