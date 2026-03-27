import pytest

from src.data_generator import generate_journeys


admission ={"admission_details": {"date": "2023-10-15", "time": "14:37", "method": "A&E", "chief_complaint": "Shortness of breath", "ED_diagnosis": "Lower respiratory tract infection", "triage_category": "Category 2 (Urgent)", "allergies": ["pollen", "sulfonamides"], "current_medications": ["Amlodipine 5mg once daily", "Paracetamol 500mg as needed", "Inhaler (Salbutamol) as needed"], "past_medical_history": ["Hypertension", "Osteoarthritis", "Chronic bronchitis"], "admitting_consultant": "Dr. Graham Gerald Frost (Consultant)", "ward": "Respiratory Ward", "specialty": "Respiratory Medicine", "admission_type": "emergency", "surgery_required": "False", "patient_id": "4c120bf8-9a61-4e3a-b725-4374e0d2d3c6", "medical_record_number": "834326325", "nhs_number": "975394642", "bed_location": "C00", "expected_length_of_stay": "5"}}

def test_simple_journey_prompt_creation(journey_generator):

    prompt = journey_generator.generate_patient_journey_prompt(admission, admission["admission_details"]["expected_length_of_stay"], approx_events_per_day = 3)

    assert isinstance(prompt, str)
    assert "2023-10-15" in prompt
    assert "15" in prompt

def test_events_complete(journey_generator):

    events = ["[ED, ED, OP, DISCHARGE]",'[A+E, OP]']

    prompts = journey_generator.test_events_complete_prompts(events)

    assert events[0] in prompts[0] and events[1] in prompts[1]

def test_staff_persona_generation(journey_generator):

    staff = ["DAVE", "SUE"]

    staff_personas = journey_generator.generate_staff_personas(staff, 0, 1)

    for key in staff_personas.keys():
        assert key in staff
        assert staff_personas[key]["abbreviates_content"] == False
        assert staff_personas[key]["abbreviates_headers"] == True
        assert staff_personas[key]["typo_rate"] > 0.3 and staff_personas[key]["typo_rate"] < 1
