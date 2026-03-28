"""
Integration tests for each pipeline stage's run() method.

All tests use the mock_llm fixture to avoid real LLM calls, so they run
in CI without a running model server.
"""
import json
import pytest
import asyncio
import uuid
from unittest.mock import patch

from src.data_generator import (
    generate_patients,
    generate_admissions,
    generate_journeys,
    generate_clinical_notes,
    add_augmentations,
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

# ---------------------------------------------------------------------------
# Stage 3 — generate_journeys
# ---------------------------------------------------------------------------

class TestGenerateJourneys:

    def _make_gen(self):
        return generate_journeys(
            patients=_make_patients_df(),
            admissions=_make_admissions_df(),
            name_df=_stub_patients,
            LLM_validator_iterations=0,
            generate_new_staff_per_patient=False,
            use_intermediate_hospital_staff=False,
            set_new_hospital_staff=False,
            filter_journey=False,
        )

    def test_run_produces_dataframe(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        assert gen.patient_journeys_df is not None
        assert len(gen.patient_journeys_df) >= 1

    def test_each_row_is_valid_json(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        for _, row in gen.patient_journeys_df.iterrows():
            parsed = json.loads(row.iloc[0])
            assert parsed is not None

    def test_each_row_is_a_list_of_events(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        for _, row in gen.patient_journeys_df.iterrows():
            events = json.loads(row.iloc[0])
            assert isinstance(events, list)
            assert len(events) >= 1
            for event in events:
                assert isinstance(event, dict)

    def test_events_have_required_fields(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        required = {"event_type", "date", "time", "staff", "details", "next_steps_decision"}
        for _, row in gen.patient_journeys_df.iterrows():
            for event in json.loads(row.iloc[0]):
                assert required.issubset(event.keys()), f"Missing: {required - event.keys()}"

    def test_staff_personas_df_produced(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        assert gen.list_of_staff_personas_df is not None
        assert len(gen.list_of_staff_personas_df) >= 1


# ---------------------------------------------------------------------------
# Stage 4 — generate_clinical_notes
# ---------------------------------------------------------------------------

class TestGenerateClinicalNotes:

    def _make_gen(self):
        return generate_clinical_notes(
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

    def _run_gen(self, mock_llm_fixture):
        """Run the notes generator with LLM_validator_iterations_clinical_note=0."""
        import src.data_generator as dg
        original = dg.PARAMS["pipeline_config"]["LLM_validator_iterations_clinical_note"]
        dg.PARAMS["pipeline_config"]["LLM_validator_iterations_clinical_note"] = 0
        try:
            gen = self._make_gen()
            asyncio.run(gen.run(return_output=False))
        finally:
            dg.PARAMS["pipeline_config"]["LLM_validator_iterations_clinical_note"] = original
        return gen

    def test_run_produces_dataframe(self, mock_llm):
        gen = self._run_gen(mock_llm)
        assert gen.final_patient_notes_df is not None
        assert len(gen.final_patient_notes_df) >= 1

    def test_each_cell_is_valid_json(self, mock_llm):
        gen = self._run_gen(mock_llm)
        for _, row in gen.final_patient_notes_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert isinstance(parsed, dict)

    def test_notes_have_required_fields(self, mock_llm):
        gen = self._run_gen(mock_llm)
        for _, row in gen.final_patient_notes_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert "note_subject" in parsed
                    assert "note_type" in parsed

    def test_no_failure_notes(self, mock_llm):
        gen = self._run_gen(mock_llm)
        for _, row in gen.final_patient_notes_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert "FAILURE" not in parsed


# ---------------------------------------------------------------------------
# Stage 5 — add_augmentations (zero LLM calls with abbreviations disabled)
# ---------------------------------------------------------------------------

class TestAddAugmentations:

    def _make_gen(self):
        return add_augmentations(
            clinical_notes=_make_notes_df(),
            staff_personas=_make_staff_personas_df(),
            detailed_journeys=_make_journeys_df(),
            add_abbreviations_to_content=False,
            add_abbreviations_to_headings=False,
            add_signature=True,
            typo_rate=0.1,
            filter_journey=False,
        )

    def test_run_produces_dataframe(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        assert gen.clean_final_patient_df is not None
        assert len(gen.clean_final_patient_df) >= 1

    def test_each_cell_is_valid_json(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        for _, row in gen.clean_final_patient_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert isinstance(parsed, dict)

    def test_notes_preserve_content_fields(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        for _, row in gen.clean_final_patient_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert "note_subject" in parsed
                    assert "note_type" in parsed

    def test_signature_added_when_enabled(self, mock_llm):
        gen = self._make_gen()
        asyncio.run(gen.run())
        found_signature = False
        for _, row in gen.clean_final_patient_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    if any("signature" in k.lower() or "sign" in k.lower()
                           for k in parsed.keys()):
                        found_signature = True
        assert found_signature, "Expected at least one note to contain a signature field"

    def test_typos_do_not_corrupt_json(self, mock_llm):
        """Notes with typo_rate > 0 must still be valid JSON."""
        gen = add_augmentations(
            clinical_notes=_make_notes_df(),
            staff_personas=_make_staff_personas_df(),
            detailed_journeys=_make_journeys_df(),
            add_abbreviations_to_content=False,
            add_abbreviations_to_headings=False,
            add_signature=False,
            typo_rate=1.0,  # maximum typo rate
            filter_journey=False,
        )
        asyncio.run(gen.run())
        for _, row in gen.clean_final_patient_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# Stage handoff tests
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

    def test_journeys_output_feeds_notes_input(self, mock_llm):
        """Stub journey/persona DataFrames can initialise generate_clinical_notes without error."""
        notes_gen = generate_clinical_notes(
            detailed_journeys=_make_journeys_df(),
            staff_personas=_make_staff_personas_df(),
            patients=_make_patients_df(),
            admissions=_make_admissions_df(),
            TEST_MODE=True,
            filter_journey=False,
            simple_template_only=True,
        )
        assert notes_gen is not None

    def test_notes_output_feeds_augmentations_input(self, mock_llm):
        """Stage 4 output DataFrame can initialise add_augmentations without error."""
        aug_gen = add_augmentations(
            clinical_notes=_make_notes_df(),
            staff_personas=_make_staff_personas_df(),
            detailed_journeys=_make_journeys_df(),
            add_abbreviations_to_content=False,
            add_abbreviations_to_headings=False,
            filter_journey=False,
        )
        assert aug_gen is not None
