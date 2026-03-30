"""
Shared stub DataFrames and builder helpers used across conftest.py and test_pipeline_stages.py.
"""
import json
import uuid
import pandas as pd

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


def _make_patients_df(n=1):
    """Build a minimal stage-1-output DataFrame (single column of JSON strings)."""
    rows = []
    for _ in range(n):
        rows.append(json.dumps({
            "patient_id": str(uuid.uuid4()),
            "medical_record_number": "123456789",
            "nhs_number": "987654321",
            "name": "Jane Smith",
            "date_of_birth": "1980-05-15",
            "age": "44",
            "gender": "Female",
            "address": "1 Test St, London, SW1A 1AA",
            "contact_number": "07700900000",
            "allergies": "None",
            "next_of_kin": {"name": "John Smith", "relationship": "Spouse", "contact_number": "07700900001"},
            "gp_details": {"name": "Dr. Alice Brown", "practice_name": "Test Surgery",
                           "address": "2 Health Rd", "contact_number": "02079460000"},
        }))
    return pd.DataFrame(rows)


def _make_admissions_df(n=1):
    """Build a minimal stage-2-output DataFrame (single column of JSON strings)."""
    rows = []
    for _ in range(n):
        rows.append(json.dumps({
            "patient_id": str(uuid.uuid4()),
            "medical_record_number": "123456789",
            "nhs_number": "987654321",
            "bed_location": "A01",
            "expected_length_of_stay": "5",
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
        }))
    return pd.DataFrame(rows)


def _make_journeys_df(n=1):
    """
    Build a minimal journeys DataFrame in multi-column format.

    generate_journeys stores patient_journeys_df as a single-column DataFrame
    (each row = JSON-serialised list of all events). However add_augmentations
    expects the filtered format: one column per event position, each cell a
    JSON-serialised individual event dict. Use this multi-column format for
    stages 4 and 5 stubs.
    """
    events = [
        {"event_type": "ED event", "date": "2023-10-15", "time": "14:37",
         "staff": ["Dr. Test Consultant"], "details": "Patient reviewed. Obs stable.",
         "next_steps_decision": "Admit to ward."},
        {"event_type": "general ward round", "date": "2023-10-16", "time": "09:00",
         "staff": ["Dr. Test Consultant"], "details": "Morning ward round. Improving.",
         "next_steps_decision": "Continue antibiotics."},
    ]
    # Multi-column: one column per event (string-named "0", "1", ...),
    # each cell is a JSON-serialised event dict.
    # String column names are required — generate_clinical_notes accesses journeys[["0"]]
    data = {str(i): [json.dumps(events[i])] * n for i in range(len(events))}
    return pd.DataFrame(data)


def _make_staff_personas_df(n=1):
    """Build a minimal stage-3-output staff personas DataFrame."""
    persona = {
        "persona_1": json.dumps({
            "Dr. Test Consultant": {
                "style": "Concise and factual",
                "abbreviates_content": False,
                "abbreviates_headers": False,
                "template_combine_sections": {},
                "typo_rate": 0.3,
                "id": "GMC123456",
            }
        })
    }
    return pd.DataFrame([json.dumps(persona)] * n)


def _make_notes_df(n=1, notes_per_patient=2):
    """Build a minimal stage-4-output DataFrame (N rows × notes_per_patient columns of JSON notes)."""
    note = json.dumps({
        "note_subject": "ED Admission Note",
        "note_type": "ED",
        "Content": "Patient Jane Smith, 44F, admitted with chest pain. Observations stable.",
    })
    data = {str(i): [note] * n for i in range(notes_per_patient)}
    return pd.DataFrame(data)
