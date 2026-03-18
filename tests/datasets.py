import pytest
from datetime import datetime

from dataset_utils import prepare_note_data, prepare_patient_data, prepare_admission_data, prepare_encounter_data, format_note


example_patient = {
    'name': 'Wayne Lawrence Rhodes',
    'date_of_birth': '1965-08-15',
    'age': '58',
    'gender': 'Male',
    'address': '263 Lawrence Annex Unit 32, Paignton, TQ4',
    'contact_number': '+44 7700 900123',
    'next_of_kin': {
        'name': 'Jennifer Rhodes',
        'relationship': 'Wife',
        'contact_number': '+44 7700 900456'
    },
    'nhs_number': '9476543210',
    'medical_record_number': '0123456789',
    'gp_details': {
        'name': 'Dr. Sarah Thompson',
        'practice_name': 'Paignton Medical Practice',
        'address': '123 Main Street, Paignton, TQ4 5AG',
        'contact_number': '+44 1803 123456'
    },
    'admission_details': {
        'date': '2023-10-11',
        'time': '14:30',
        'method': 'A&E',
        'reason': 'Chest pain',
        'triage_category': 'Category 2',
        'allergies': ['Penicillin'],
        'current_medications': ['Aspirin 75mg', 'Atorvastatin 40mg'],
        'past_medical_history': ['Hypertension', 'Hyperlipidemia'],
        'admitting_consultant': 'Dr. John Smith',
        'specialty': 'Cardiology',
        'ward': 'Cardiology Ward A',
        'anticipated_discharge_date': '2023-10-15',
        'admission_id': '8bd6246a-3c8e-4b5b-b254-cf17ac6cb937',
        'encounter_id': '2c4dcdee-da53-4a45-94bd-5acc3cfe2dc8',
        'bed_location': 'A2',
        'admission_type': 'emergency'
    },
    'patient_id': 'b0d45b22-97fd-4ca4-aa23-7604c7d73df6'
}


example_event = {
    'event_type': "emergency_admission",
    'date': "2023-10-11",
    'time': "14:30",
    'staff': ["Dr. John Smith"],
    'details': "Admission event details",
    'note_id': "f83d9cfc-0386-4995-9ebf-50c0ac8485d5"
}


example_note = {
    "note_subject": "Admission Note for Wayne Lawrence Rhodes",
    "note_type": "Test note",
    "Example Note Text": "This is an example note"
}
    

def test_prepare_patient_data():
    expected_result = {
        "full_name": "Wayne Lawrence Rhodes",
        "person_id": "b0d45b22-97fd-4ca4-aa23-7604c7d73df6",
        "date_of_birth": datetime(1965, 8, 15).date(),
        "age": 58,
        "mrn": "0123456789",
        "nhs_number": "9476543210",
        "gender_identity": "Male"
    }
    
    result = prepare_patient_data(example_patient)
    
    # common entires must be the same
    common_keys = result.keys() & expected_result.keys()
    assert all([result[k] == expected_result[k] for k in common_keys])
    

def test_prepare_admission_data():
    expected_result = {
        "admission_id": "8bd6246a-3c8e-4b5b-b254-cf17ac6cb937",
        'encounter_id': '2c4dcdee-da53-4a45-94bd-5acc3cfe2dc8',
        "admission_status": "Admitted",
        "admission_method": "A&E",
        "admission_title": "Rhodes, Wayne Lawrence | 15-08-1965",
        "date_of_birth": datetime(1965, 8, 15).date(),
        "bed_location": "Cardiology Ward A · Bay 2 · Bed A2",
        "admission_timestamp": datetime(2023, 10, 11, 14, 30),
        "mrn": "0123456789",
        "nhs_number": "9476543210",
        "patient_id": "b0d45b22-97fd-4ca4-aa23-7604c7d73df6",
        "patient_name": "Wayne Lawrence Rhodes",
        "first_name": "Wayne",
        "surname": "Rhodes",
        "full_name": "Rhodes, Wayne Lawrence",
        "site_name": "Chelsea and Westminster Hospital",
        "site_id": "RQM01",
        "ward": "Cardiology Ward A",
        "admission_source_hospital_provider_spell": "test"
    }
    
    result = prepare_admission_data(example_patient, version="test")

    # common entires must be the same
    common_keys = result.keys() & expected_result.keys()
    assert all([result[k] == expected_result[k] for k in common_keys])

    
def test_prepare_encounter_data():
    expected_result = {
        'encounter_id': '2c4dcdee-da53-4a45-94bd-5acc3cfe2dc8',
        "patient_id": "b0d45b22-97fd-4ca4-aa23-7604c7d73df6",
        "patient_name": "Wayne Lawrence Rhodes"
    }
    
    result = prepare_encounter_data(example_patient)
    
    # common entires must be the same
    common_keys = result.keys() & expected_result.keys()
    assert all([result[k] == expected_result[k] for k in common_keys])
    

def test_prepare_note_data():
    expected_result = {
        "admission_id": "8bd6246a-3c8e-4b5b-b254-cf17ac6cb937",
        "note_type": "Medicine Inpatients",
        "clean_note_text": "Example Note Text\nThis is an example note\n\n",
        "note_subject": "Admission Note for Wayne Lawrence Rhodes",
        "note_type": "Test note",
        "creation_timestamp": datetime(2023, 10, 11, 14, 30),
        "ingest_timestamp": datetime(2023, 10, 11, 15, 0),
        "updt_dt_tm": datetime(2023, 10, 11, 15, 0)
    }
    
    result = prepare_note_data(example_patient, example_event, example_note)
    
    # common entires must be the same
    common_keys = result.keys() & expected_result.keys()
    assert all([result[k] == expected_result[k] for k in common_keys])

    
def test_format_note():
    example_note = {
        "Purpose": "To test the note format function",
        "Approach": {
            "Part 1": "Write a test",
            "Part 2": "Run the test"
        }
    }
    
    expected_output = """Purpose
To test the note format function

Approach

Part 1
Write a test

Part 2
Run the test

"""

    assert format_note(example_note) == expected_output
    