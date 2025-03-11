import os
import time
import logging

from google.genai import Client as Gemini
from mistralai import Mistral
from together import Together

from enum import Enum

# Gemini API key and model
gemini_api_key = os.environ["GEMINI_API_KEY"]
gemini_client = Gemini(api_key=gemini_api_key)
gemini_nr_questions = 0


def ask_gemini(question: str) -> str:
    global gemini_nr_questions
    gemini_nr_questions += 1
    logging.debug(f"Sending a question #{gemini_nr_questions} to gemini...")
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=question,
    )
    logging.debug(f"Received a response.")
    return response.text


# Mistral API key and model
mistral_api_key = os.environ["MISTRAL_API_KEY"]
mistral_client = Mistral(api_key=mistral_api_key)
mistral_nr_questions = 0


def ask_mistral(question: str) -> str:
    global mistral_nr_questions
    mistral_nr_questions += 1
    logging.debug(f"Sending a question #{mistral_nr_questions} to mistral...")
    response = mistral_client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "user",
                "content": question,
            },
        ],
    )
    logging.debug(f"Received a response.")
    return response.choices[0].message.content


# Together API key and model
together_api_key = os.environ["TOGETHER_API_KEY"]
together_client = Together(api_key=together_api_key)
together_nr_questions = 0


def ask_together(question: str, model: str) -> str:
    global together_nr_questions
    together_nr_questions += 1
    logging.debug(f"Sending a question #{together_nr_questions} to together...")
    response = together_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
    )
    logging.debug(f"Received a response.")
    return response.choices[0].message.content


class Model(Enum):
    # Provided by Google
    GEMINI = "gemini"

    # Provided by Mistral
    MISTRAL = "mistral"

    # Provided by TogetherAI
    LLAMA3_3_FREE = "Llama-3.3-70B-Instruct-Turbo-Free"
    DEEPSEEK_R1 = "DeepSeek-R1"
    DEEPSEEK_V3 = "DeepSeek-V3"


def ask_model(model: Model, question: str) -> str:
    """
    Make an API call to the specified model with the given question.
    """
    if model == Model.GEMINI:
        return ask_gemini(question)
    elif model == Model.MISTRAL:
        return ask_mistral(question)
    elif model == Model.LLAMA3_3_FREE:
        return ask_together(question, "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free")
    elif model == Model.DEEPSEEK_R1:
        return ask_together(question, "deepseek-ai/DeepSeek-R1")
    elif model == Model.DEEPSEEK_V3:
        return ask_together(question, "deepseek-ai/DeepSeek-V3")
    raise ValueError(f"Invalid model: {model}")


def translate_ro_to_en(text: str) -> str:
    """
    Translate Romanian text to English, using Gemini
    """
    prompt = "You are tasked with TRANSLATING a romanian CS/Math problem to English. "
    prompt += "As this is a technical translation, please keep the technical terms as they are, and do not, under any circumstances, simplify the problem, change numbers, or change the context. Please do a 1-to-1 translation from romanian to english, with the exact same numbers and meaning, but in english instead of romanian. "
    prompt += "Your answer will be processed directly, without any modifications, so only provide the translation, not any additional information. "
    prompt += "Please provide the translation of the following text:\n```"
    prompt += text
    prompt += "\n```"

    result = ask_gemini(prompt)
    return result
