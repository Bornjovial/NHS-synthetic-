import json
import logging
import textstat
import asyncio

import pandas as pd

logger = logging.getLogger(__name__)
from src.processing import call_llm_async
from src.prompts import evaluation_prompts
from config.params import PARAMS

def calculate_readability_score(note: str, readability_type: str):
    clean_note = note.replace(".\n\n", ". ").replace("\n\n", ". ").replace("\n", ": ")
    try:
        if readability_type == "flesch_reading_ease":
            return textstat.flesch_reading_ease(clean_note)
        elif readability_type == "dale_chall_readability_score":
            return textstat.dale_chall_readability_score(clean_note)
    except:
        logger.error("Error calculating readability score")
        return None

    
async def calculate_fluency(notes, temperature = 0):

    prompts = [
        evaluation_prompts["calculate_fluency_prompt"].substitute(
            NOTE = note
        )
        for note in notes
    ]

    tasks = [call_llm_async(prompt, PARAMS["pipeline_config"]["model"], temperature) for prompt in prompts]

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

    tasks = [call_llm_async(prompt, PARAMS["pipeline_config"]["model"], temperature) for prompt in prompts]

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

    tasks = [call_llm_async(prompt, PARAMS["pipeline_config"]["model"], temperature) for prompt in prompts]

    raw_response = await asyncio.gather(*tasks)

    return raw_response


def _parse_score(raw: str) -> int | None:
    """Parse a 1-5 integer score from a raw LLM response string."""
    if raw is None:
        return None
    try:
        return int(str(raw).strip())
    except (ValueError, TypeError):
        pass
    import re
    match = re.search(r"\b([1-5])\b", str(raw))
    return int(match.group(1)) if match else None


async def run_evaluation(evaluation_output_data: list) -> pd.DataFrame:
    """
    Run all quality metrics over a list of evaluation records and return a DataFrame.

    Each record in ``evaluation_output_data`` is a dict produced by
    ``prepare_evaluation_data`` and contains at minimum:
    - ``clean_note_text``: the formatted note string
    - ``journey``: list of journey event dicts
    - ``current_event_i``: index of the current event in the journey (str)
    - ``patient_id``: patient identifier

    Metrics computed per note:
    - ``flesch_reading_ease``: readability score (no LLM)
    - ``dale_chall_readability_score``: readability score (no LLM)
    - ``fluency``: LLM-judged score 1-5
    - ``groundedness``: LLM-judged score 1-5
    - ``relevance``: LLM-judged score 1-5

    Parameters
    ----------
    evaluation_output_data : list[dict]
        Records from ``save_final_outputs.run()``.

    Returns
    -------
    pd.DataFrame
        One row per note with the original record fields plus the five metric columns.
    """
    if not evaluation_output_data:
        logger.warning("run_evaluation: no records to evaluate.")
        return pd.DataFrame()

    notes = [str(r.get("clean_note_text", "")) for r in evaluation_output_data]

    events = []
    patient_infos = []
    for r in evaluation_output_data:
        journey = r.get("journey", [])
        try:
            event_i = int(r.get("current_event_i", 0))
            event = journey[event_i] if event_i < len(journey) else {}
        except (TypeError, IndexError, ValueError):
            event = {}
        events.append(json.dumps(event) if isinstance(event, dict) else str(event))
        patient_infos.append(str(r.get("patient_id", "")))

    # Readability — no LLM, compute inline
    flesch_scores = [calculate_readability_score(n, "flesch_reading_ease") for n in notes]
    dale_chall_scores = [calculate_readability_score(n, "dale_chall_readability_score") for n in notes]

    # LLM-judged metrics — three async calls per note, all launched in parallel
    logger.info(f"run_evaluation: scoring {len(notes)} notes (fluency, groundedness, relevance)...")
    tasks = []
    for note, event, patient_info in zip(notes, events, patient_infos):
        tasks.append(calculate_fluency([note]))
        tasks.append(calculate_groundedness([note], event, patient_info))
        tasks.append(calculate_relevance([note], event, patient_info))

    raw_results = await asyncio.gather(*tasks)

    results = []
    for i, record in enumerate(evaluation_output_data):
        fluency_raw = raw_results[i * 3][0]
        groundedness_raw = raw_results[i * 3 + 1][0]
        relevance_raw = raw_results[i * 3 + 2][0]
        row = record.copy()
        row["flesch_reading_ease"] = flesch_scores[i]
        row["dale_chall_readability_score"] = dale_chall_scores[i]
        row["fluency"] = _parse_score(fluency_raw)
        row["groundedness"] = _parse_score(groundedness_raw)
        row["relevance"] = _parse_score(relevance_raw)
        results.append(row)

    logger.info("run_evaluation: done.")
    return pd.DataFrame(results)