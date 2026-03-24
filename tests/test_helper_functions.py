import pytest
import pandas as pd
from src.data_generator import generate_random_person, generate_hospital_staff
import random

@pytest.fixture
def fake_patient_data(request):
    """
    Pytest fixture that returns a fake patient DataFrame.

    Usage in test:
        def test_x(fake_patient_data):
            df = fake_patient_data
    Optional parameter:
        middle_name_nullable=True/False
    """
    # Get optional parameter
    use_middle = getattr(request, "param", True)

    races = ["Florn", "Gleeb", "Trivian", "Zylar"]
    ethnicities = ["Blorp", "Quen", "Xylo", "Varn"]

    data = [
        {
            "FIRST": "John",
            "MIDDLE": "A" if use_middle else None,
            "LAST": "Doe",
            "RACE": random.choice(races),
            "ETHNICITY": random.choice(ethnicities),
            "GENDER": "M",
            "ADDRESS": "123 Main St",
            "CITY": "Springfield",
            "POSTCODE": "12345"
        },
        {
            "FIRST": "Jane",
            "MIDDLE": "B" if use_middle else None,
            "LAST": "Smith",
            "RACE": random.choice(races),
            "ETHNICITY": random.choice(ethnicities),
            "GENDER": "F",
            "ADDRESS": "456 Elm St",
            "CITY": "Rivertown",
            "POSTCODE": "67890"
        },
        {
            "FIRST": "Alice",
            "MIDDLE": "C" if use_middle else None,
            "LAST": "Johnson",
            "RACE": random.choice(races),
            "ETHNICITY": random.choice(ethnicities),
            "GENDER": "F",
            "ADDRESS": "789 Oak St",
            "CITY": "Lakeside",
            "POSTCODE": "11223"
        },
        {
            "FIRST": "Bob",
            "MIDDLE": "D" if use_middle else None,
            "LAST": "Williams",
            "RACE": random.choice(races),
            "ETHNICITY": random.choice(ethnicities),
            "GENDER": "M",
            "ADDRESS": "321 Pine St",
            "CITY": "Hilltown",
            "POSTCODE": "44556"
        }
    ]

    return pd.DataFrame(data)



def test_name_generation(fake_patient_data):
    patient_df = fake_patient_data
    patient_details = generate_random_person(patient_df)
    assert len(patient_details["name"].split(" ")) == 3

@pytest.mark.parametrize("fake_patient_data", [False], indirect=True)
def test_name_generation_wo_middle_name(fake_patient_data):
    patient_df = fake_patient_data
    patient_details = generate_random_person(patient_df)
    assert len(patient_details["name"].split(" ")) == 2

def test_name_generation_last_name_only(fake_patient_data):
    patient_df = fake_patient_data
    patient_details = generate_random_person(patient_df, last_name_only=True)
    assert len(patient_details["name"].split(" ")) == 2
    assert any([title in patient_details["name"] for title in ["Mr", "Mrs", "Miss"]])

def test_address_generation(fake_patient_data):
    patient_df = fake_patient_data
    patient_details = generate_random_person(patient_df)
    assert len(patient_details["address"]) != 0

def test_gender_generation(fake_patient_data):
    patient_df = fake_patient_data
    patient_details = generate_random_person(patient_df)
    assert patient_details["gender"] in ("M", "F")

def test_name_only(fake_patient_data):
    patient_df = fake_patient_data
    patient_details = generate_random_person(patient_df, name_only=True)
    assert "name" in patient_details.keys()
    assert len(patient_details.keys()) == 1

def test_hospital_staff_generation(fake_patient_data):
    patient_df = fake_patient_data
    staff = generate_hospital_staff(patient_df, 5, ["dr"])
    print(staff)
    assert len(staff) == 5
    for person in staff:
        assert person[0:2] == "dr"
