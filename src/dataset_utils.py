import json
from datetime import datetime, timedelta
import uuid
import pandas as pd
from src.schemas import patient_schema, encounter_schema, admission_schema, note_schema, schema_dict
import numpy as np
import random
import string
import time
from ast import literal_eval
from src.processing import read_write_data

def prepare_note_data(patient_information, event, note):
    """
    Combines note with its metadata, returning a list with the dataset fields
    for each note, so that notes can be saved in a dataset.
    """
    # Datetime of the event
    date = event["date"]
    time = event["time"]
    date_and_time = " ".join((date,time))
    creation_timestamp =  datetime.strptime(
        parse_and_normalize_datetime(date_and_time),
        "%Y-%m-%d %H:%M")
    
    if "FAILURE" not in note.keys():
        subject = note["note_subject"]
        note_type = note["note_type"]
        note_text = format_note(note)
    else:
        subject = f"FAILURE: Note for {event['event_type']} event"
        note_type = f"FAILURE: Note for {event['event_type']} event"
        note_text = note
    
    patient_information = patient_information.copy()
    
    note_data = {key: None for key in note_schema.keys()}
    note_data["clinical_note_id"] = str(uuid.uuid4()) # generate a clinical note id 
    note_data["clean_note_text"] = note_text
    note_data["markdown_content"] = note_text
    note_data["raw_blob_content"] = note_text
    note_data["creation_timestamp"] = creation_timestamp
    note_data["ingest_timestamp"] = creation_timestamp + timedelta(minutes = 30)
    note_data["updt_dt_tm"] = creation_timestamp + timedelta(minutes = 30)
    note_data["note_subject"] = subject
    note_data["note_type"] = note_type
    note_data["admission_id"] = patient_information["admission_details"]["admission_id"]
    note_data["encounter_id"] = patient_information["admission_details"]["encounter_id"]
    note_data["person_id"] = patient_information["patient_id"]

    return note_data


def prepare_evaluation_data(evaluation_data, journey, journey_i, patient_data, run_name, current_time):
    """
    Prepares the information about each journey in a simplified dictionary.
    """
    
    evaluation_data["journey"] = journey
    evaluation_data["current_event_i"] = str(journey_i)
    evaluation_data["patient_id"] = patient_data["person_id"]
    evaluation_data["run_name"] = run_name
    evaluation_data["current_time"] = current_time
    
    return evaluation_data


def prepare_patient_data(patient_information):
    """
    Prepares the information about each patient in a simplified dictionary
    ready to be saved in an ontology-compatible dataset.
    """
    patient_information = patient_information.copy()
    
    patient_data = {key: None for key in patient_schema.keys()}
    patient_data["person_id"] = patient_information["patient_id"]
    patient_data["nhs_number"] = patient_information["nhs_number"]
    patient_data["gender_identity"] = patient_information["gender"]
    patient_data["mrn"] = patient_information["medical_record_number"]
    patient_data["age"] = int(patient_information["age"])
    patient_data["date_of_birth"] = datetime.strptime(patient_information["date_of_birth"], "%Y-%m-%d").date()
    patient_data["date_of_death"] = datetime(1000, 1, 1).date()
    patient_data["full_name"] = patient_information["name"]
    patient_data["rv_group_ids"] = [""]
    patient_data["rv_modules"] = [""]
    
    return patient_data


def prepare_admission_data(
        patient_information,
        version,
        site_name = None,
        site_code = None,
    ):
    """
    Prepares the information about each admission in a simplified dictionary
    ready to be saved in an ontology-compatible dataset.
    """

    if site_name is None:
        site_name = "Oak Tree Trust"
    if site_code is None:
        site_code = "ABC12"
        
    patient_information = patient_information.copy()
    
    admission_datetime = patient_information["admission_details"]["date"] + patient_information["admission_details"]["time"]
    
    admission_data = {key: None for key in admission_schema.keys()}
    admission_data["rv_group_ids"] = [""]
    admission_data["rv_modules"] = [""]
    admission_data["admission_id"] = patient_information["admission_details"]["admission_id"]
    admission_data["admission_status"] = "Admitted"
    admission_data["admission_source_hospital_provider_spell"] = version   
    admission_data["admission_method"] = patient_information["admission_details"]["method"]
    
    name_parts = patient_information["name"].split()
    if len(name_parts) == 1:
        # Single-word name (rare edge case)
        admission_data["first_name"] = name_parts[0]
        admission_data["surname"] = ""
        middle_name = ""
        admission_data["full_name"] = admission_data["first_name"]
    else:
        admission_data["first_name"] = name_parts[0]
        admission_data["surname"] = name_parts[-1]
        middle_name = " ".join(name_parts[1:-1])
        if middle_name:
            admission_data["full_name"] = f"{admission_data['surname']}, {admission_data['first_name']} {middle_name}"
        else:
            admission_data["full_name"] = f"{admission_data['surname']}, {admission_data['first_name']}"
    

    admission_data["patient_name"] = patient_information["name"]
    admission_data["date_of_birth"] = datetime.strptime(patient_information["date_of_birth"], "%Y-%m-%d").date()
    admission_data["admission_title"] = f"{admission_data['full_name']} | {admission_data['date_of_birth'].strftime('%d-%m-%Y')}"
    

    bed_digits = "".join(filter(str.isdigit, patient_information["admission_details"]["bed_location"]))
    bed_suffix = bed_digits[-2:] if len(bed_digits) >= 2 else bed_digits
    admission_data["bed_location"] = (
        f"{patient_information['admission_details']['ward']} · Bay {bed_suffix} · Bed {patient_information['admission_details']['bed_location']}"
    )

    admission_data["admission_timestamp"] = parse_and_normalize_datetime(admission_datetime)
    admission_data["mrn"] = patient_information["medical_record_number"]
    admission_data["nhs_number"] = patient_information["nhs_number"]
    admission_data["patient_id"] = patient_information["patient_id"]
    admission_data["site_name"] = site_name
    admission_data["site_id"] = site_code
    admission_data["ward"] = patient_information["admission_details"]["ward"]
    admission_data["encounter_id"] = patient_information["admission_details"]["encounter_id"]
    
    return admission_data

def prepare_encounter_data(patient_information):
    patient_information = patient_information.copy()
    
    encounter_data = {key: None for key in encounter_schema.keys()}
    encounter_data["encounter_id"] = patient_information["admission_details"]["encounter_id"]
    encounter_data["patient_id"] = patient_information["patient_id"]
    encounter_data["patient_name"] = patient_information["name"]
    encounter_data["rv_group_ids"] = [""]
    encounter_data["rv_modules"] = [""]
    encounter_data["issues"] = [""]
    encounter_data["created_date"] = datetime(1000, 1, 1).date()
    encounter_data["last_poa_expiry_date"] = datetime(1000, 1, 1).date()
    encounter_data["last_poa_outcome_date"] = datetime(1000, 1, 1).date()
    encounter_data["peri_op_risk_stratification_outcome_date"] = datetime(1000, 1, 1).date()
    encounter_data["removal_date"] = datetime(1000, 1, 1).date()
    encounter_data["tci_date"] = datetime(1000, 1, 1).date()
    
    return encounter_data
    
                 
def write_dataset(data_dicts, dataset_name, append=False):
    """
    Takes a list of dictionaries and writes to the dataset with name dataset_name.
    """
    print(f"Writing to {dataset_name} dataset")
    
    if dataset_name in schema_dict.keys():
        schema = schema_dict[dataset_name]
        df = pd.DataFrame(data_dicts).astype(schema)
    else:
        df = pd.DataFrame(data_dicts)

    if append:
        existing_df = read_write_data(dataset_name, "read")
        df = pd.concat([existing_df, df], ignore_index=True)
        
        # Bug fix, may be able to remove later once ran in master
        if "journey" in df.columns:
            
            if "journey" in df.columns:
            # Convert all journey values to JSON-safe strings
                
                def to_json_safe(val):
                    if isinstance(val, str):
                        return val  # Assume already a JSON string
                    elif isinstance(val, np.ndarray):
                        # Convert to list with all elements as JSON-serializable types
                        return json.dumps(val.tolist(), default=_np_safe)
                    else:
                        return json.dumps(val, default=_np_safe)

                def _np_safe(obj):
                    if isinstance(obj, (np.integer, np.floating)):
                        return obj.item()
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif isinstance(obj, bytes):
                        return obj.decode()
                    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

                df["journey"] = df["journey"].apply(to_json_safe)

    read_write_data(dataset_name, "write", df)
    
    print(f"Successfully wrote to {dataset_name} dataset")

    
def format_note(cleaned_note_dictionary):
    """
    Takes the note dictionary and outputs this to a string with newlines for each
    section of the note.
    """
    # Remove the subject as this should not appear in the note text
    note_wo_subject = {
        i : cleaned_note_dictionary[i]
        for i in cleaned_note_dictionary
        if i!="note_subject" and i!= "note_type"
    }
    
    
    note_str = ""
    for key, value in note_wo_subject.items():
        if key == "Content":
            # Notes with "Content" key have no predetermined template, we only need the value.
            note_str +=  f"{value}"
        elif key == "Signature":
            note_str += f"\n{value}"
        
        else:
            note_str += f"{key}\n"
            if isinstance(value, dict):
                if key in ["Observations", "Obs"]:
                    for k, v in value.items():
                        note_str += f"{k} {v}\n"
                elif key == "Issues":
                    for k, v in value.items():
                        # Each v should be a python list
                        note_str += f"{k}\n-"
                        try:
                            note_str += "\n-".join(literal_eval(v))
                            note_str += "\n"
                        except:
                            note_str += f"{v}\n"
                else:
                    for k, v in value.items():
                        if isinstance(v, dict):
                            note_str += f"\n{k}\n"
                            for k1, v1 in v.items():
                                note_str += f"{k1}: {v1}\n"
                        else:
                            note_str += f"\n{k}\n{v}\n"
            else:
                note_str += f"{value}\n"
            note_str += "\n"
    
    return note_str

def get_journey_evaluation_details(patient, journey, expected_los, run_name, current_time):
    """
    Compiles some metrics on expected journey length vs. actual.
    Also records the number of ward rounds happening during the
    course of a journey
    """
    
    details = {}
    
    details["patient_id"] = patient["patient_id"]
    details["admission_id"] = patient["admission_details"]["admission_id"]
    details["run_name"] = run_name
    details["current_time"] = current_time
    details["number_of_events"] = len(journey)
    
    start_date = pd.to_datetime(journey[0]["date"])
    end_date = pd.to_datetime(journey[-1]["date"])
    details["expected_LOS"] = expected_los
    details["actual_LOS"] = (end_date - start_date).days
    
    ward_rounds = [event for event in journey if "ward" in event["event_type"]]
    details["number_of_ward_rounds"] = len(ward_rounds)
    
    return details

def generate_staff_gmc_and_pin(staff_member):
    digits = string.digits
    letters = string.ascii_uppercase
    
    if 'nurse' in staff_member.lower():
        nmc_num = (
            random.choice(digits) +
            random.choice(digits) +
            random.choice(letters) +
            random.choice(digits) +
            random.choice(digits) +
            random.choice(digits) +
            random.choice(digits) +
            random.choice(letters)
        )
        staff_id = nmc_num
    elif 'dr' in staff_member.lower():
        gmc_num = random.randint(1000000,1999999)
        staff_id = str(gmc_num)
    else:
        staff_id = ''
    return staff_id
            
def add_sign_off_to_note(note, staff_member, staff_member_id):
    
    if 'nurse' in staff_member.lower():
        id_sign_off = f"\nNMC number: {staff_member_id}"
    elif 'dr' in staff_member.lower():
        id_sign_off = f"\nGMC number: {staff_member_id}"
    else:
        id_sign_off = ''
        
    note["Signature"] = f"{staff_member} {id_sign_off}"
    return note

def parse_and_normalize_datetime(value: str) -> str:
    """
    Parse a datetime string from multiple possible formats
    and return it as a string in the canonical format: '%Y-%m-%d %H:%M'
    
    Handles:
        - ISO timestamps: '2026-01-05T07:50:00'
        - Space-separated: '2026-01-05 07:50:00' or '2026-01-05 07:50'
        - No-space: '2026-01-0507:50'
        - Duplicated dates: '2026-01-052026-01-05T07:50:00'
    """
    if not value or not isinstance(value, str):
        raise ValueError(f"Invalid datetime value: {value}")
    value = value.strip()
    # Handle duplicated-date bug: keep last ISO timestamp if present
    if len(value) > 19 and "T" in value:
        value = value[-19:]
    # Known formats to try
    formats = [
        "%Y-%m-%d%H:%M",        # no space
        "%Y-%m-%d %H:%M",       # space-separated
        "%Y-%m-%d %H:%M:%S",    # space + seconds
        "%Y-%m-%dT%H:%M:%S",    # ISO
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")  # canonical output
        except ValueError:
            continue
    # As a last resort, try Python 3.7+ fromisoformat
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        pass
    raise ValueError(f"Unrecognized datetime format: {value}")