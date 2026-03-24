import pytest 
from src.data_generator import call_llm

def test_call_LLM():
    prompt = "Why is the sky blue?"
    output = call_llm(prompt)
    assert isinstance(output, str)

def test_call_LLM_with_history():

    history = ["What is the capital of England?",
               "London",
              "and France?",
              "Paris"]
    prompt = "And Turkey?"

    output = call_llm(prompt, chat_history = history)

    assert isinstance(output, str)