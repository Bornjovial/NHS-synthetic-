import pandas as pd
import pytest

from src.data_generator import generate_admissions, generate_journeys


# Minimal stub DataFrames that satisfy __init__ without reading from disk

_stub_patients = pd.DataFrame({
    "FIRST": ["Jane"], "MIDDLE": ["A"], "LAST": ["Smith"],
    "RACE": ["white"], "ETHNICITY": ["nonmixed"], "GENDER": ["F"],
    "ADDRESS": ["1 Test St"], "CITY": ["London"], "POSTCODE": ["SW1A 1AA"],
})

_stub_emergency = pd.DataFrame({
    "Age_Category": ["18-40", "41-90", "41-90", "41-90"],
    "Sex_Category": ["Male", "Male", "Female", "Male"],
    "ChiefComplaintDescription": ["Chest pain", "Chest pain", "Shortness of breath", "Chest pain"],
    "DiagnosisDescription": ["Pneumonia", "Pneumonia", "COPD exacerbation", "Novel condition"],
    "rare_disease": [0, 0, 0, 0],
    "NovelDiseaseFlag": [0, 0, 0, 1],
    "AdditionalSymptoms": ["None", "None", "None", "None"],
    "AdditionalInformation": ["None", "None", "None", "None"],
    "ConfirmedBy": ["None", "None", "None", "None"],
    "SupportedBy": ["None", "None", "None", "None"],
    "Admitted_Flag": [1, 1, 1, 1],
    "count": [100, 100, 100, 100],
    "Der_Spell_LoS": [3.0, 5.0, 4.0, 5.0],
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
