import pytest 
from palantir_models.models import OpenAiGptChatLanguageModel
from data_generator import call_llm

model = OpenAiGptChatLanguageModel.get("GPT_4o")

def test_call_LLM():
    prompt = "Why is the sky blue?"
    output = call_llm(prompt, model)
    assert isinstance(output, str)

def test_call_LLM_with_history():

    history = ["What is the capital of England?",
               "London",
              "and France?",
              "Paris"]
    prompt = "And Turkey?"

    output = call_llm(prompt, model, chat_history = history)

    assert isinstance(output, str)