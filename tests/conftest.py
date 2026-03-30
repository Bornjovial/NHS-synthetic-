import json
import asyncio
import pytest
from unittest.mock import patch

from src.data_generator import generate_admissions, generate_journeys, generate_clinical_notes, add_augmentations
from stubs import (
    _stub_patients,
    _stub_emergency,
    _stub_elective,
    _stub_admissions,
)


# ---------------------------------------------------------------------------
# Plausible LLM fixture responses — one per stage
# ---------------------------------------------------------------------------

PATIENT_LLM_RESPONSE = json.dumps({
    "name": "Jane Smith",
    "date_of_birth": "1980-05-15",
    "age": "44",
    "gender": "Female",
    "address": "1 Test St, London, SW1A 1AA",
    "contact_number": "07700900000",
    "allergies": "None",
    "next_of_kin": {
        "name": "John Smith",
        "relationship": "Spouse",
        "contact_number": "07700900001",
    },
    "gp_details": {
        "name": "Dr. Alice Brown",
        "practice_name": "Test Surgery",
        "address": "2 Health Rd, London",
        "contact_number": "02079460000",
    },
})

ADMISSION_LLM_RESPONSE = json.dumps({
    "date": "2023-10-15",
    "time": "14:37",
    "method": "A&E",
    "chief_complaint": "Chest pain",
    "ED_diagnosis": "Pneumonia",
    "triage_category": "Category 2 (Urgent)",
    "allergies": "None",
    "current_medications": "None",
    "past_medical_history": "None",
    "admitting_consultant": "Dr. Test Consultant (Consultant)",
    "ward": "Respiratory Ward",
    "specialty": "Respiratory Medicine",
    "admission_type": "emergency",
    "surgery_required": "False",
})

ADMISSION_LOS_RESPONSE = "5"

JOURNEY_LLM_RESPONSE = json.dumps([
    {"event_type": "ED", "date": "2023-10-15", "time": "14:37", "summary": "Patient admitted via A&E"},
    {"event_type": "Ward Round", "date": "2023-10-16", "time": "09:00", "summary": "Morning ward round"},
    {"event_type": "DISCHARGE", "date": "2023-10-20", "time": "11:00", "summary": "Patient discharged"},
])

JOURNEY_COMPLETE_RESPONSE = "NO"  # "NO" means journey is complete (not truncated)

JOURNEY_VALIDATION_RESPONSE = json.dumps([
    {"event_type": "ED", "date": "2023-10-15", "time": "14:37", "summary": "Patient admitted via A&E"},
    {"event_type": "Ward Round", "date": "2023-10-16", "time": "09:00", "summary": "Morning ward round"},
    {"event_type": "DISCHARGE", "date": "2023-10-20", "time": "11:00", "summary": "Patient discharged"},
])

EVENT_DETAILS_RESPONSE = json.dumps({
    "staff": ["Dr. Test Consultant"],
    "details": "Patient reviewed. Observations stable.",
    "next_steps_decision": "Continue current management.",
})

CLINICAL_NOTE_RESPONSE = json.dumps({
    "note_subject": "ED Admission Note",
    "note_type": "ED",
    "Content": "Patient Jane Smith, 44F, admitted with chest pain. "
               "Observations stable. Diagnosed with pneumonia. "
               "Started on amoxicillin 500mg TDS.",
})

ABBREVIATION_RESPONSE = json.dumps({
    "note_subject": "ED Admission Note",
    "note_type": "ED",
    "Content": "Pt Jane Smith, 44F, admitted c/o chest pain. "
               "Obs stable. Dx pneumonia. Started amox 500mg TDS.",
})


# ---------------------------------------------------------------------------
# Mock fixture: patches call_llm_async and call_llm for the whole module
# ---------------------------------------------------------------------------

def _llm_response_for(prompt: str) -> str:
    """Return an appropriate fixture response based on prompt content."""
    prompt_lower = prompt.lower() if prompt else ""
    # Journey completeness check — prompt contains "terminated early"
    if "terminated early" in prompt_lower:
        return JOURNEY_COMPLETE_RESPONSE
    if "length of stay" in prompt_lower or "los" in prompt_lower:
        return ADMISSION_LOS_RESPONSE
    if "validate" in prompt_lower or "validation" in prompt_lower:
        return JOURNEY_VALIDATION_RESPONSE
    # Clinical note prompts — check before event details (both mention "staff")
    # The clinical note prompt contains "note_subject" in the output format
    if "note_subject" in prompt_lower or "clinical notes for nhs" in prompt_lower:
        return CLINICAL_NOTE_RESPONSE
    if "abbreviat" in prompt_lower:
        return ABBREVIATION_RESPONSE
    # Event details prompt — explicitly asks for staff/details/next_steps
    if "next_steps_decision" in prompt_lower or ("staff" in prompt_lower and "detail" in prompt_lower):
        return EVENT_DETAILS_RESPONSE
    if "journey" in prompt_lower or "event" in prompt_lower:
        return JOURNEY_LLM_RESPONSE
    if "admission" in prompt_lower:
        return ADMISSION_LLM_RESPONSE
    if "patient" in prompt_lower:
        return PATIENT_LLM_RESPONSE
    # Unknown prompt — fall back to patient response but warn so routing errors are visible
    import warnings
    warnings.warn(f"_llm_response_for: no routing match for prompt snippet {prompt_lower[:80]!r}")
    return PATIENT_LLM_RESPONSE


@pytest.fixture
def mock_llm():
    """
    Patches call_llm and call_llm_async in src.processing to return fixture
    responses without hitting a real LLM server. Inject into any test that
    calls a pipeline stage's run() method.
    """
    async def _async_llm(prompt, model=None, temp=0.7, max_attempts=3, chat_history=None, sem=None):
        return _llm_response_for(prompt)

    def _sync_llm(prompt, model=None, temp=0.7, max_attempts=3, chat_history=None):
        return _llm_response_for(prompt)

    with patch("src.processing.call_llm_async", side_effect=_async_llm), \
         patch("src.processing.call_llm", side_effect=_sync_llm):
        yield


# ---------------------------------------------------------------------------
# Generator fixtures (module-scoped, no LLM calls at construction time)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def admission_generator():
    return generate_admissions(
        elective_admission_rate=0,
        patients=_stub_patients,
        notional_complaints_stats=_stub_emergency,
        elective_procedures=_stub_elective,
        names_df=_stub_patients,
    )


@pytest.fixture(scope="module")
def journey_generator():
    return generate_journeys(
        patients=_stub_patients,
        admissions=_stub_admissions,
        name_df=_stub_patients,
    )


@pytest.fixture(scope="module")
def mock_llm_module():
    """
    Module-scoped variant of mock_llm for use in module-scoped generator fixtures.
    Use the function-scoped mock_llm for per-test isolation; use this only for
    module-level fixtures that call run() once and share results across tests.
    """
    async def _async_llm(prompt, model=None, temp=0.7, max_attempts=3, chat_history=None, sem=None):
        return _llm_response_for(prompt)

    def _sync_llm(prompt, model=None, temp=0.7, max_attempts=3, chat_history=None):
        return _llm_response_for(prompt)

    with patch("src.processing.call_llm_async", side_effect=_async_llm), \
         patch("src.processing.call_llm", side_effect=_sync_llm):
        yield


@pytest.fixture(scope="module")
def notes_generator(mock_llm_module):
    """Stage 4 generator, run once per module. LLM validator disabled to avoid extra calls."""
    import src.data_generator as dg
    from stubs import _make_journeys_df, _make_staff_personas_df, _make_patients_df, _make_admissions_df
    original = dg.PARAMS["pipeline_config"]["LLM_validator_iterations_clinical_note"]
    dg.PARAMS["pipeline_config"]["LLM_validator_iterations_clinical_note"] = 0
    try:
        gen = generate_clinical_notes(
            detailed_journeys=_make_journeys_df(),
            staff_personas=_make_staff_personas_df(),
            patients=_make_patients_df(),
            admissions=_make_admissions_df(),
            TEST_MODE=True,
            filter_journey=False,
            simple_template_only=True,
            combine_sections=False,
            model="test-model",
        )
        asyncio.run(gen.run(return_output=False))
    finally:
        dg.PARAMS["pipeline_config"]["LLM_validator_iterations_clinical_note"] = original
    return gen


@pytest.fixture(scope="module")
def augmentation_generator(mock_llm_module):
    """Stage 5 generator, run once per module."""
    from stubs import _make_notes_df, _make_staff_personas_df, _make_journeys_df
    gen = add_augmentations(
        clinical_notes=_make_notes_df(),
        staff_personas=_make_staff_personas_df(),
        detailed_journeys=_make_journeys_df(),
        add_abbreviations_to_content=False,
        add_abbreviations_to_headings=False,
        add_signature=True,
        typo_rate=0.1,
        filter_journey=False,
    )
    asyncio.run(gen.run())
    return gen
