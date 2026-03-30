"""
Integration tests for each pipeline stage's run() method.

All tests use the mock_llm fixture to avoid real LLM calls, so they run
in CI without a running model server.
"""
import json
import pytest
import asyncio

from src.data_generator import (
    generate_patients,
    generate_admissions,
    generate_journeys,
    generate_clinical_notes,
    add_augmentations,
)
from stubs import (
    _stub_patients,
    _stub_emergency,
    _stub_elective,
    _make_patients_df,
    _make_admissions_df,
    _make_journeys_df,
    _make_staff_personas_df,
    _make_notes_df,
)


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
# Stage 4 — generate_clinical_notes (run once via module-scoped fixture)
# ---------------------------------------------------------------------------

class TestGenerateClinicalNotes:

    def test_run_produces_dataframe(self, notes_generator):
        assert notes_generator.final_patient_notes_df is not None
        assert len(notes_generator.final_patient_notes_df) >= 1

    def test_each_cell_is_valid_json(self, notes_generator):
        for _, row in notes_generator.final_patient_notes_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert isinstance(parsed, dict)

    def test_notes_have_required_fields(self, notes_generator):
        for _, row in notes_generator.final_patient_notes_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert "note_subject" in parsed
                    assert "note_type" in parsed

    def test_no_failure_notes(self, notes_generator):
        for _, row in notes_generator.final_patient_notes_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert "FAILURE" not in parsed


# ---------------------------------------------------------------------------
# Stage 5 — add_augmentations (run once via module-scoped fixture)
# ---------------------------------------------------------------------------

class TestAddAugmentations:

    def test_run_produces_dataframe(self, augmentation_generator):
        assert augmentation_generator.clean_final_patient_df is not None
        assert len(augmentation_generator.clean_final_patient_df) >= 1

    def test_each_cell_is_valid_json(self, augmentation_generator):
        for _, row in augmentation_generator.clean_final_patient_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert isinstance(parsed, dict)

    def test_notes_preserve_content_fields(self, augmentation_generator):
        for _, row in augmentation_generator.clean_final_patient_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    assert "note_subject" in parsed
                    assert "note_type" in parsed

    def test_signature_added_when_enabled(self, augmentation_generator):
        found_signature = False
        for _, row in augmentation_generator.clean_final_patient_df.iterrows():
            for cell in row:
                if cell is not None and str(cell) != "nan":
                    parsed = json.loads(cell)
                    if any("signature" in k.lower() or "sign" in k.lower()
                           for k in parsed.keys()):
                        found_signature = True
        assert found_signature, "Expected at least one note to contain a signature field"

    def test_typos_do_not_corrupt_json(self, mock_llm):
        """Notes with typo_rate=1.0 must still produce valid JSON."""
        gen = add_augmentations(
            clinical_notes=_make_notes_df(),
            staff_personas=_make_staff_personas_df(),
            detailed_journeys=_make_journeys_df(),
            add_abbreviations_to_content=False,
            add_abbreviations_to_headings=False,
            add_signature=False,
            typo_rate=1.0,
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
