import pytest
from processing import remove_failures

def test_failures_removed():

    inputs = [{"dict_1":"test_1"},
             {"FAILURE":"test_2"},
             {"dict_2": {"nested_dict_1": "test_1"}}
             ]

    clean_list, removed_ids = remove_failures(inputs)
    
    assert len(removed_ids) == 1
    assert removed_ids[0] == 1

    assert(len(clean_list) == 3)
    assert clean_list[0] == {"dict_1":"test_1"}
    assert clean_list[1] == None
    assert clean_list[2] == {"dict_2": {"nested_dict_1": "test_1"}}

def test_failures_in_values_not_removed():

    inputs = [{"dict_1":"test_1"},
            {"dict_2":"FAILURE"},
             {"dict_3": {"FAILURE": "test_1"}}]

    clean_list, removed_ids = remove_failures(inputs)
    
    assert len(removed_ids) == 0
    
    assert(len(clean_list) == 3)
    assert clean_list[0] == {"dict_1":"test_1"}
    assert clean_list[1] == {"dict_2":"FAILURE"}
    assert clean_list[2] == {"dict_3": {"FAILURE": "test_1"}}