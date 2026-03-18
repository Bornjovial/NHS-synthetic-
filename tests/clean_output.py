import pytest
import numpy as np
import pandas as pd
import re
import random

from processing import clean_outputs, normalise_array_struct_column, create_admission_window, random_24_hour_time, build_output_info

def test_valid_json_dict():
    raw_output = '{"key": "value"}'
    output = clean_outputs([raw_output], "dictionary")[0]
    assert output  == {"key": "value"}

def test_valid_json_list():
    raw_output = '[{"key": "value"}, {"key2": "value2"}]'
    output = clean_outputs([raw_output], "list")[0]
    assert output == [{"key": "value"}, {"key2": "value2"}]

def test_malformed_json_dict():
    raw_output = "Some text before {\"key\": \"value\"} some text after"
    output = clean_outputs([raw_output], "dictionary")[0]
    assert output == {"key": "value"}

def test_malformed_json_list():
    raw_output = "Some text before [{\"key\": \"value\"}, {\"key2\": \"value2\"}] some text after"
    output = clean_outputs([raw_output], "list")[0]
    assert output == [{"key": "value"}, {"key2": "value2"}]

def test_invalid_json():
    raw_output = "Invalid string"
    output = clean_outputs([raw_output], "dictionary")[0]
    assert output == {"FAILURE": raw_output}

def test_invalid_cleaning_type():
    raw_output = '{"key": "value"}'
    output = clean_outputs([raw_output], "sgsrgsrgsrg")
    assert output is None

def test_lists_are_returned_as_lists():
    raw_output = [1,2,3,4]
    output = clean_outputs([raw_output], "list")[0]
    assert output == [1,2,3,4]

def test_dicts_are_Returned_as_dicts():
    raw_output = {"key": "value"}
    output = clean_outputs([raw_output], "dictionary")[0]
    assert output == {"key": "value"}
    
def test_multiple_outputs():
    raw_outputs = ['{"key": "value"}', "Some text before {\"key\": \"value\"}  some text after"]
    outputs = clean_outputs(raw_outputs, "dictionary", verbose = True)
    print(outputs)
    assert outputs[0] == {"key": "value"}
    assert outputs[1] == {"key": "value"}

@pytest.mark.parametrize("input_value,expected", [	
    # Simple single value in brackets	
    ("[value]", ["value"]),	
    	
    # Multiple comma-separated values	
    ("[value_a, value_b, value_c]", ["value_a", "value_b", "value_c"]),	
    	
    # Single value with quotes	
    ("['value']", ["value"]),	
    	
    # Multiple values with mixed quotes and spaces	
    ("[ 'a', \"b\", c ]", ["a", "b", "c"]),	
    	
    # Already normalised list	
    (["already", "normalised"], ["already", "normalised"]),	
    	
    # None value	
    (None, None),	
    	
    # NaN value	
    (np.nan, None),	
    	
    # Nested dict with single and multiple bracketed strings	
    ({"key1": "[single]", "key2": "[a, b, c]"},	
     {"key1": ["single"], "key2": ["a", "b", "c"]}),	
    	
    # List of dicts	
    ([{"a": "[1,2]"}, {"b": "[x,y]"}],	
     [{"a": [1, 2]}, {"b": ["x", "y"]}]),	
    	
    # Nested combination	
    ({"outer": [{"inner": "[val1, val2]"}, {"inner": "[val3]"}]},	
     {"outer": [{"inner": ["val1", "val2"]}, {"inner": ["val3"]}]})	
])	
def test_normalise_array_struct_column(input_value, expected):	
    df = pd.DataFrame({"col": [input_value]})	
    df = normalise_array_struct_column(df, "col")	
    assert df["col"].iloc[0] == expected

def test_create_admission_window_single_day():
    result = create_admission_window("2024-01-01", "2024-01-01")
    assert result == ["2024-01-01"]


def test_create_admission_window_multiple_days():
    result = create_admission_window("2024-01-01", "2024-01-05")
    assert result == [
        "2024-01-01",
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
        "2024-01-05",
    ]


def test_create_admission_window_cross_month():
    result = create_admission_window("2024-01-30", "2024-02-02")
    assert result == [
        "2024-01-30",
        "2024-01-31",
        "2024-02-01",
        "2024-02-02",
    ]

def test_random_24_hour_time_format():
    elective_start_hour =  7
    elective_end_hour= 18
    ae_start_hour = 0
    ae_end_hour = 22
    value = random_24_hour_time(elective_start_hour,
                                elective_end_hour,
                                ae_start_hour,
                                ae_end_hour)
    assert re.match(r"^\d{2}:\d{2}$", value)


def test_random_24_hour_time_valid_range_non_elective():
    elective_start_hour =  7
    elective_end_hour= 18
    ae_start_hour = 0
    ae_end_hour = 22
    for _ in range(100):
        value = random_24_hour_time(elective_start_hour,
                                    elective_end_hour,
                                    ae_start_hour,
                                    ae_end_hour,
                                   generate_elective=False)
        hour, minute = map(int, value.split(":"))

        assert 0 <= hour <= 22
        assert 0 <= minute < 55


def test_random_24_hour_time_valid_range_elective():
    elective_start_hour =  7
    elective_end_hour= 18
    ae_start_hour = 0
    ae_end_hour = 22
    
    for _ in range(100):
        value = random_24_hour_time(elective_start_hour,
                                    elective_end_hour,
                                    ae_start_hour,
                                    ae_end_hour,
                                   generate_elective=True)
        hour, minute = map(int, value.split(":"))

        assert 7 <= hour <= 18
        assert 0 <= minute < 55


def test_random_24_hour_time_minute_step():
    elective_start_hour =  7
    elective_end_hour= 18
    ae_start_hour = 0
    ae_end_hour = 22
    for _ in range(100):
        value = random_24_hour_time(elective_start_hour,
                                    elective_end_hour,
                                    ae_start_hour,
                                    ae_end_hour,
                                   generate_elective=False)
        
        _, minute = map(int, value.split(":"))
        assert minute % 5 == 0 # Checks that the minute is divisable by 5.

# Fixture that patches random.shuffle to do nothing
@pytest.fixture
def no_shuffle(monkeypatch):
    """Disable random.shuffle for deterministic tests."""
    monkeypatch.setattr(random, "shuffle", lambda x: None)


def test_only_keep_keys_no_content():
    """Test when only keep_key items exist, Content missing."""
    template = {
        "note_subject": "value1",
        "note_type": "value2"
    }
    expected = "- note_subject: value1\n- note_type: value2"
    assert build_output_info(template) == expected


def test_content_exists_no_other_items(no_shuffle):
    """Test when Content exists but no other remaining items."""
    template = {
        "note_subject": "value1",
        "note_type": "value2",
        "Content": "value3"
    }
    expected = "- note_subject: value1\n- note_type: value2\n- Content: value3."
    assert build_output_info(template) == expected


def test_content_exists_with_remaining_items(no_shuffle):
    """Test when Content exists and there are other items."""
    template = {
        "note_subject": "value1",
        "note_type": "value2",
        "Content": "value3",
        "extra1": "value4",
        "extra2": "value5"
    }
    expected = (
        "- note_subject: value1\n"
        "- note_type: value2\n"
        "- Content: value3.\n"
        "  Other information that could be included in Content:\n"
        "    - You could include information on extra1; this could be about value4.\n"
        "    - You could include information on extra2; this could be about value5."
    )
    assert build_output_info(template) == expected


def test_no_content_with_remaining_items(no_shuffle):
    """Test when Content is missing but other items exist."""
    template = {
        "note_subject": "value1",
        "note_type": "value2",
        "extra1": "value3"
    }
    expected = (
        "- note_subject: value1\n"
        "- note_type: value2\n"
        "- Possible additional Content could include:\n"
        "  - You could include information on extra1; this could be about value3."
    )
    assert build_output_info(template) == expected


def test_content_case_insensitive(no_shuffle):
    """Test that content detection is case-insensitive."""
    template = {
        "note_subject": "value1",
        "note_type": "value2",
        "CONTENT": "value3",
        "extra": "value4"
    }
    expected = (
        "- note_subject: value1\n"
        "- note_type: value2\n"
        "- CONTENT: value3.\n"
        "  Other information that could be included in Content:\n"
        "    - You could include information on extra; this could be about value4."
    )
    assert build_output_info(template) == expected
