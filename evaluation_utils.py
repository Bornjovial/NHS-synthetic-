import textstat
import asyncio
from processing import call_llm_async
from prompts import evaluation_prompts

def calculate_readability_score(note: str, readability_type: str):
    clean_note = note.replace(".\n\n", ". ").replace("\n\n", ". ").replace("\n", ": ")
    try:
        if readability_type == "flesch_reading_ease":
            return textstat.flesch_reading_ease(clean_note)
        elif readability_type == "dale_chall_readability_score":
            return textstat.dale_chall_readability_score(clean_note)
    except:
        print("Error calculating readability score")
        return None

    
async def calculate_fluency(notes, temperature = 0):

    prompts = [
        evaluation_prompts["calculate_fluency_prompt"].substitute(
            NOTE = note
        )
        for note in notes
    ]

    tasks = [call_llm_async(prompt, "GPT_4o") for prompt in prompts]
    
    raw_response = await asyncio.gather(*tasks)
    
    return raw_response


async def calculate_groundedness(notes, event, patient_info, temperature = 0):

    prompts = [
        evaluation_prompts["calculate_groundedness_prompt"].substitute(
            NOTE = note,
            EVENT = event,
            PATIENT_INFO = patient_info
        )
        for note in notes
    ]
    
    tasks = [call_llm_async(prompt, "GPT_4o") for prompt in prompts]
    
    raw_response = await asyncio.gather(*tasks)
    
    return raw_response
    

async def calculate_relevance(notes, event, patient_info, temperature = 0):

    prompts = [
        evaluation_prompts["calculate_relevance_prompt"].substitute(
            NOTE = note,
            EVENT = event,
            PATIENT_INFO = patient_info
        )
        for note in notes
    ]
        
    tasks = [call_llm_async(prompt, "GPT_4o") for prompt in prompts]
    
    raw_response = await asyncio.gather(*tasks)
    
    return raw_response