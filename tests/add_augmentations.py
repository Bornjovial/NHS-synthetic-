import pytest
import pytest_asyncio

from processing import add_abbreviations_to_strings, add_abbreviations_to_dict, add_typos_to_dict

from palantir_models.models import OpenAiGptChatLanguageModel
model = OpenAiGptChatLanguageModel.get("GPT_4o")

from copy import deepcopy

@pytest.mark.asyncio
async def test_abbreviation_added():
    string = ["Patient has been diagnosed with tuberculosis following a chest X-ray. Patients next of kin informed. History of smoking."]
    output = await add_abbreviations_to_strings(string, model)
    output = output[0]
    
    assert isinstance(output[0], str)
    assert isinstance(output[1], int)
    
    possible_abbreviations = ["Pt", "pt", "TB", "tb", "cxr", "CXR", "NOK", "#NOK", "nok", "ho", "h/o", "H/O"]
    abbreviations_used = [ab in output[0] for ab in possible_abbreviations]
    
    assert any(abbreviations_used)

@pytest.mark.asyncio
async def test_abbreviation_in_values():

    dictionary = {
        "chest x-ray was positive": "chest x-ray was positive",
        "tests done": {
            "chest x-ray was positive": "chest x-ray was positive",
            "chest x-ray was negative": "chest x-ray was negative"
        },
        "ignore":"chest x-ray is positive this should not change",
    }
    
    output = await add_abbreviations_to_dict(deepcopy(dictionary),
                                    model,
                                    ["ignore"],
                                    True,
                                    False)
    output = output[0]
    
    
    input_values = [v for k, v in dictionary.items()]
    output_values = [v for k, v in output.items()]
    
    differing_values = [input_values[i] != output_values[i] for i in range(len(input_values))]
    
    # Check keys remain the same
    assert list(output.keys()) == ["chest x-ray was positive", "tests done", "ignore"]
    assert list(output["tests done"].keys()) == ["chest x-ray was positive", "chest x-ray was negative"]
    
    #Check ignored key is present and not changed
    assert output["ignore"] == "chest x-ray is positive this should not change"
    
    # Check abbreviations added to values
    assert any(differing_values)

@pytest.mark.asyncio
async def test_abbreviation_in_headings():

    dictionary = {
        "chest x-ray was positive": "chest x-ray was positive",
        "tests done": {
            "chest x-ray was positive": "chest x-ray was positive",
            "chest x-ray was negative": "chest x-ray was negative"
        },
        "ignore":"chest x-ray is positive this should not change",
    }
    
    output = await add_abbreviations_to_dict(deepcopy(dictionary),
                                    model,
                                    ["ignore"],
                                    False,
                                    True)
    output = output[0]
    
    def get_keys(dictionary):
        return list(dictionary.keys())
    
    output_keys = []
    for output_key in output.keys():
        if isinstance(output[output_key], dict):
            output_keys.append(output_key)
            output_keys.extend(get_keys(output[output_key]))
        else:
            output_keys.append(output_key)
        
    input_keys = ["chest x-ray was positive",
                 "tests done",
                 "chest x-ray was positive",
                 "chest x-ray was negative",
                 "ignore",]
    
    differing_keys = [input_keys[i] != output_keys[i] for i in range(len(input_keys))]
    
    # Check keys are different
    assert any(differing_keys) == True
    
    #Check ignored key is ignored
    assert output["ignore"] == "chest x-ray is positive this should not change"
    
    # Check values are the same
    assert output[output_keys[0]] == "chest x-ray was positive"
    assert output[output_keys[1]][output_keys[2]] == "chest x-ray was positive"
    assert output[output_keys[1]][output_keys[3]] == "chest x-ray was negative"

@pytest.mark.asyncio
async def test_abbreviation_in_headings_and_values():

    dictionary = {
        "chest x-ray was positive": "chest x-ray was positive",
        "tests done": {
            "chest x-ray was positive": "chest x-ray was positive",
            "chest x-ray was negative": "chest x-ray was negative"
        },
        "ignore":"chest x-ray is positive this should not change",
    }
    
    output = await add_abbreviations_to_dict(deepcopy(dictionary),
                                    model,
                                    ["ignore"],
                                    True,
                                    True)
    output = output[0]
    print(output)
    def get_keys(dictionary):
        return list(dictionary.keys())
    
    output_keys = []
    for output_key in output.keys():
        if isinstance(output[output_key], dict):
            output_keys.append(output_key)
            output_keys.extend(get_keys(output[output_key]))
        else:
            output_keys.append(output_key)
    
    input_keys = ["chest x-ray was positive",
                 "tests done",
                 "chest x-ray was positive",
                 "chest x-ray was negative",
                 "ignore"]
    
    differing_keys = [input_keys[i] != output_keys[i] for i in range(len(input_keys))]
    
    # Check keys are different
    assert any(differing_keys) == True
    
    #Check ignored key is ignored
    assert output["ignore"] == "chest x-ray is positive this should not change"
    
    # Check values are different diferent
    differing_values = []
    differing_values.append(output[output_keys[0]] != "chest x-ray was positive")
    differing_values.append(output[output_keys[1]][output_keys[2]] != "chest x-ray was positive")
    differing_values.append(output[output_keys[1]][output_keys[3]] != "chest x-ray was negative")   
    assert any(differing_values)
    
@pytest.mark.asyncio
async def test_string_abbreviation_behaviour():
    
    strings = [
    "Social History - No contributory social factors noted.", # This was a unneccesary abbreviation in feedback.
    "Chest X-ray (CXR) show lungs are clear bilaterally. Specifically, no evidence of focal consolidation, pneumothorax, or pleural effusion.",
    "Patient presents with a history of hypertension, currently well-controlled on medication with no acute symptoms reported.",
    "Procedure - laparoscopic appendectomy for acute appendicitis", # This was a unneccesary abbreviation in feedback. - lap appy
    "Impression - Acute appendicitis (AA)",
    "Surgical wound healing with no infection", # infx not needed
    "2. Elevated C-reactive protein (45 mg/L) resolving.",
    "A CT abdomen and pelvis confirmed the diagnosis of acute appendicitis without perforation or abscess formation.", #Dont want CECT
    "On Examination: A: Airways patient. B: Clear lung fields bilat. No wheeze or creps.", #Dont want AW
    "Past medical history: Hypertension, diabetes mellitus type 2, hyperlipidemia.", #Might not want HLD as clinicans didnt recognise it in feedback
    "The patient was admitted following a myocardial infarction and is currently on dual antiplatelet therapy.",
    "She has a history of chronic obstructive pulmonary disease requiring inhalers",
    "he patient reports osteoarthritis of both knees with reduced mobility"
    ]
    
    expected_checks = [
    lambda s: "NCSF" not in s,
    lambda s: "CXR" in s and "(CXR)" not in s,
    lambda s: "HTN" in s,
    lambda s: "lap appy" not in s,
    lambda s: "AA" in s and "(AA)" not in s and "Acute appendicitis" not in s,
    lambda s: "infx" not in s and "infxn" not in s,
    lambda s: "CRP" in s,   # C-reactive protein -> CRP
    lambda s: "CECT" not in s,
    lambda s: "AW" not in s,
    lambda s: "HLD" not in s, 
    lambda s: "MI" in s,
    lambda s: "COPD" in s,
    lambda s: "OA" in s
    ]
    
    expected_fraction_correct = 0.8
    
    number_correct = 0
    abbreviated_strings = await add_abbreviations_to_strings(strings, model)
    print("TEST:", abbreviated_strings)
    results = [check(s[0]) for s, check in zip(abbreviated_strings,expected_checks)]
    number_correct = results.count(True)
            
    assert (number_correct / len(abbreviated_strings)) > expected_fraction_correct
    
def test_typo_generation_with_0_typo_rate():
    
    dictionary = {
        "positive": "positive",
        "tests done": {
            "positive test": "result was positive",
            "negative test": "result was negative"
        }
    }
    
    output = add_typos_to_dict(deepcopy(dictionary), 0, sections_to_ignore=[])[0]
    
    assert output == dictionary
    

def test_typo_generation_with_high_typo_rate():
    
    dictionary = {
        "positive": "positive",
        "tests done": {
            "positive test": "abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz ",
            "negative test": "result was negative"
        }
    }
    
    output = add_typos_to_dict(dictionary, 5, sections_to_ignore=[])[0]
    
    # Ensure the same keys are present
    assert set(output.keys()) == set(dictionary.keys())
    assert set(output["tests done"].keys()) == set(dictionary["tests done"].keys())
    
    original_values = ["positive",
                       "abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz ",
                       "result was negative"]
    modified_values = [output["positive"], output["tests done"]["positive test"], output["tests done"]["negative test"]]
    
    # Check that at least one value has been changed
    assert any(ov != mv for ov, mv in zip(original_values, modified_values))
    