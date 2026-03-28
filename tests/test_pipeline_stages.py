"""
Integration tests for each pipeline stage's run() method.

All tests use the mock_llm fixture to avoid real LLM calls, so they run
in CI without a running model server.
"""
import json
import pytest
import asyncio
import uuid

from src.data_generator import (
    generate_patients,
    generate_admissions,
    generate_journeys,
)
import pandas as pd

_stub_patients = pd.DataFrame({
    "FIRST": ["Jane"], "MIDDLE": ["A"], "LAST": ["Smith"],
    "RACE": ["white"], "ETHNICITY": ["nonmixed"], "GENDER": ["F"],
    "ADDRESS": ["1 Test St"], "CITY": ["London"], "POSTCODE": ["SW1A 1AA"],
})

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


# ---------------------------------------------------------------------------
# Stage 1 — generate_patients
# ---------------------------------------------------------------------------

class TestGeneratePatients:

    def test_run_produces_dataframe(self, mock_llm):
        gen = generate_patients(
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(gen.run())
        df = gen.list_of_patients_df
        assert df is not None
        assert len(df) >= 1

    def test_each_row_is_valid_json(self, mock_llm):
        gen = generate_patients(
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(gen.run())
        for _, row in gen.list_of_patients_df.iterrows():
            parsed = json.loads(row.iloc[0])
            assert isinstance(parsed, dict)

    def test_required_patient_fields_present(self, mock_llm):
        gen = generate_patients(
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(gen.run())
        required = {"patient_id", "medical_record_number", "nhs_number", "name", "age", "gender"}
        for _, row in gen.list_of_patients_df.iterrows():
            parsed = json.loads(row.iloc[0])
            assert required.issubset(parsed.keys()), f"Missing fields: {required - parsed.keys()}"

    def test_multiple_generations(self, mock_llm):
        gen = generate_patients(
            names_df=_stub_patients,
            number_of_generations=2,
        )
        asyncio.run(gen.run())
        assert len(gen.list_of_patients_df) == 2

    def test_patient_ids_are_unique(self, mock_llm):
        gen = generate_patients(
            names_df=_stub_patients,
            number_of_generations=2,
        )
        asyncio.run(gen.run())
        ids = [json.loads(row.iloc[0])["patient_id"] for _, row in gen.list_of_patients_df.iterrows()]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Stage 2 — generate_admissions
# ---------------------------------------------------------------------------

class TestGenerateAdmissions:

    def test_run_produces_dataframe(self, mock_llm):
        gen = generate_admissions(
            elective_admission_rate=0,
            patients=_make_patients_df(),
            notional_complaints_stats=_stub_emergency,
            elective_procedures=_stub_elective,
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(gen.run())
        df = gen.list_of_admissions_df
        assert df is not None
        assert len(df) >= 1

    def test_each_row_is_valid_json(self, mock_llm):
        gen = generate_admissions(
            elective_admission_rate=0,
            patients=_make_patients_df(),
            notional_complaints_stats=_stub_emergency,
            elective_procedures=_stub_elective,
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(gen.run())
        for _, row in gen.list_of_admissions_df.iterrows():
            parsed = json.loads(row.iloc[0])
            assert isinstance(parsed, dict)

    def test_required_admission_fields_present(self, mock_llm):
        gen = generate_admissions(
            elective_admission_rate=0,
            patients=_make_patients_df(),
            notional_complaints_stats=_stub_emergency,
            elective_procedures=_stub_elective,
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(gen.run())
        required = {"patient_id", "admission_type", "ward", "specialty", "expected_length_of_stay"}
        for _, row in gen.list_of_admissions_df.iterrows():
            parsed = json.loads(row.iloc[0])
            assert required.issubset(parsed.keys()), f"Missing fields: {required - parsed.keys()}"

    def test_admission_type_is_emergency_when_rate_zero(self, mock_llm):
        gen = generate_admissions(
            elective_admission_rate=0,
            patients=_make_patients_df(),
            notional_complaints_stats=_stub_emergency,
            elective_procedures=_stub_elective,
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(gen.run())
        for _, row in gen.list_of_admissions_df.iterrows():
            parsed = json.loads(row.iloc[0])
            assert parsed["admission_type"] == "emergency"


# ---------------------------------------------------------------------------
# Stage 1+2 schema handoff — patients output feeds admissions input
# ---------------------------------------------------------------------------

class TestStageHandoff:

    def test_patient_output_satisfies_admissions_input(self, mock_llm):
        """Patients written and read back as admissions input without error."""
        patient_gen = generate_patients(
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(patient_gen.run())
        patients_df = patient_gen.list_of_patients_df

        # Admissions reads patients from intermediate CSV; here we pass directly
        admission_gen = generate_admissions(
            elective_admission_rate=0,
            patients=patients_df,
            notional_complaints_stats=_stub_emergency,
            elective_procedures=_stub_elective,
            names_df=_stub_patients,
            number_of_generations=1,
        )
        asyncio.run(admission_gen.run())
        assert len(admission_gen.list_of_admissions_df) >= 1
