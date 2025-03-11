import google.generativeai as genai
import os
import time

from enum import Enum

# Gemini API key and model
gemini_api_key = os.environ["GEMINI_API_KEY"]
genai.configure(api_key=gemini_api_key)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

gemini_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)


class Model(Enum):
    GEMINI = "gemini"


def ask_gemini(model: Model, question: str) -> str:
    """
    Ask a question to the Gemini model
    """
    try:
        if model == Model.GEMINI:
            chat_session = gemini_model.start_chat(history=[])
            response = chat_session.send_message(question)
            return response.text
        else:
            raise NotImplementedError(f"Model {model} not implemented")
    except Exception as e:
        print("Error:", e)
        print("Retrying in 10 seconds...")
        time.sleep(10)
        return ask_gemini(model, question)


def translate_ro_to_en(text: str) -> str:
    """
    Translate Romanian text to English
    """
    prompt = "You are tasked with TRANSLATING a romanian CS/Math problem to English. "
    prompt += "As this is a technical translation, please keep the technical terms as they are, and do not, under any circumstances, simplify the problem, change numbers, or change the context. Please do a 1-to-1 translation from romanian to english, with the exact same numbers and meaning, but in english instead of romanian. "
    prompt += "Your answer will be processed directly, without any modifications, so only provide the translation, not any additional information. "
    prompt += "Please provide the translation of the following text:\n```"
    prompt += text
    prompt += "\n```"

    result = ask_gemini(Model.GEMINI, prompt)
    return result
