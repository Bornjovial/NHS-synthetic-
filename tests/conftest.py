import json
import pandas as pd
import pytest
from unittest.mock import AsyncMock, patch

from src.data_generator import generate_admissions, generate_journeys


# ---------------------------------------------------------------------------
# Stub input DataFrames (used by fixtures to avoid disk reads)
# ---------------------------------------------------------------------------

_stub_patients = pd.DataFrame({
    "FIRST": ["Jane"], "MIDDLE": ["A"], "LAST": ["Smith"],
    "RACE": ["white"], "ETHNICITY": ["nonmixed"], "GENDER": ["F"],
    "ADDRESS": ["1 Test St"], "CITY": ["London"], "POSTCODE": ["SW1A 1AA"],
})

# Emergency admissions data — needs Admitted_Flag, count, Der_Spell_LoS
# and rows covering both age ranges and NovelDiseaseFlag values used in tests
_stub_emergency = pd.DataFrame({
    # Two rows per sex per NovelDiseaseFlag to cover all combinations across age ranges
    "Age_Category":             ["18-90", "18-90", "18-90", "18-90"],
    "Sex_Category":             ["Male",  "Female", "Male",  "Female"],
    "ChiefComplaintDescription":["Chest pain", "Shortness of breath", "Chest pain", "Shortness of breath"],
    "DiagnosisDescription":     ["Pneumonia", "COPD exacerbation", "Novel condition", "Novel condition"],
    "rare_disease":             [0, 0, 0, 0],
    "NovelDiseaseFlag":         [0, 0, 1, 1],
    "AdditionalSymptoms":       ["None", "None", "None", "None"],
    "AdditionalInformation":    ["None", "None", "None", "None"],
    "ConfirmedBy":              ["None", "None", "None", "None"],
    "SupportedBy":              ["None", "None", "None", "None"],
    "Admitted_Flag":            [1, 1, 1, 1],
    "count":                    [100, 100, 100, 100],
    "Der_Spell_LoS":            [3.0, 4.0, 5.0, 5.0],
})

_stub_elective = pd.DataFrame({
    "Age_Category": ["18-40"], "Sex": ["Male"],
    "Speciality": ["Orthopaedics"], "Procedure": ["Hip replacement"],
})

_stub_admissions = pd.DataFrame({
    "patient_id": ["test-id-1"],
    "admission_type": ["emergency"],
    "specialty": ["Respiratory Medicine"],
    "ward": ["Respiratory Ward"],
    "chief_complaint": ["Chest pain"],
    "diagnosis": ["Pneumonia"],
    "admitting_consultant": ["Dr. Test Consultant (Consultant)"],
    "date": ["2023-10-15"], "time": ["14:37"],
    "triage_category": ["Category 2 (Urgent)"],
    "allergies": ["None"], "current_medications": ["None"],
    "past_medical_history": ["None"],
    "medical_record_number": ["123456789"],
    "nhs_number": ["987654321"],
    "bed_location": ["A01"],
    "expected_length_of_stay": ["5"],
    "surgery_required": ["False"],
})


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
