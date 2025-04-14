import os
import time
import logging

from google.genai import Client as Gemini
from mistralai import Mistral
from together import Together

from enum import Enum

logger = logging.getLogger(__name__)

# Gemini API key and model
gemini_api_key = os.environ["GEMINI_API_KEY"] if "GEMINI_API_KEY" in os.environ else ""
gemini_client = Gemini(api_key=gemini_api_key)
gemini_nr_questions = 0


def ask_gemini(question: str, retries=10, model="gemini-2.0-flash") -> str:
    try:
        global gemini_nr_questions
        gemini_nr_questions += 1
        logger.debug(f"Sending a question #{gemini_nr_questions} to gemini...")
        logger.debug(f"Question: {question}")
        response = gemini_client.models.generate_content(
            model=model,
            contents=question,
        )
        logger.debug(f"Received a response: {response.text}")
        return response.text
    except Exception as e:
        if retries == 0:
            return "Failed to get a response from Gemini."
        logger.error(f"Failed to get a response from Gemini: {e}")
        logger.error("Retrying in 30 seconds...")
        time.sleep(30)
        return ask_gemini(question, retries - 1, model=model)


# Mistral API key and model
mistral_api_key = (
    os.environ["MISTRAL_API_KEY"] if "MISTRAL_API_KEY" in os.environ else ""
)
mistral_client = Mistral(api_key=mistral_api_key)
mistral_nr_questions = 0


def ask_mistral(question: str, retries=10) -> str:
    try:
        global mistral_nr_questions
        mistral_nr_questions += 1
        logger.debug(f"Sending a question #{mistral_nr_questions} to mistral...")
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user",
                    "content": question,
                },
            ],
        )
        logger.debug(f"Received a response.")
        return response.choices[0].message.content
    except Exception as e:
        if retries == 0:
            return "Failed to get a response from Mistral."
        logger.error(f"Failed to get a response from Mistral: {e}")
        logger.error("Retrying in 30 seconds...")
        time.sleep(30)
        return ask_mistral(question, retries - 1)


# Together API key and model
together_api_key = (
    os.environ["TOGETHER_API_KEY"] if "TOGETHER_API_KEY" in os.environ else ""
)
together_client = Together(api_key=together_api_key)
together_nr_questions = 0


def ask_together(question: str, model: str, retries=10) -> str:
    global together_nr_questions
    together_nr_questions += 1
    try:
        logger.debug(f"Sending a question #{together_nr_questions} to together...")
        response = together_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
        )
        logger.debug(f"Received a response: {response.choices[0].message.content}")
        return response.choices[0].message.content
    except Exception as e:
        if retries == 0:
            return "Failed to get a response from Together."
        logger.error(f"Failed to get a response from Together: {e}")
        logger.error("Retrying in 60 seconds...")
        time.sleep(60)
        return ask_together(question, model, retries - 1)


class Model(str, Enum):
    # Provided by Google
    GEMINI = "gemini"

    GEMINI_2_5 = "gemini-2.5"

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
    elif model == Model.GEMINI_2_5:
        return ask_gemini(question, model="gemini-2.5-pro-exp-03-25")
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
