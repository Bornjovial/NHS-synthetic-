import pytest
from copy import deepcopy

from doc_templates import  document_templates, template_sections_to_combine
# from data_generator import generate_clinical_notes
from processing import pop_nested_value, combine_template_sections, pop_nested_value
from doc_templates import document_templates


def test_possible_combine_sections():
    """
    Ensure that any note headers in the combine sections dict
    are actually present in the relevant note template.
    """
    for event_type, new_sections in template_sections_to_combine.items():
        event_template = deepcopy(document_templates[event_type])
        for new_section, old_sections in new_sections.items():
            assert pop_nested_value(deepcopy(event_template), new_section) is not None
            for section in old_sections:
                assert pop_nested_value(deepcopy(event_template), section) is not None

def test_combine_note_sections():
    """
    Confirm that sections in note templates are combined properly.
    New section names should appear in the new template section.
    Combine section names should not appear in new template headers.
    """
    test_note = {
        "a": "this is a",
        "b": "this is b",
        "c": {
            "i": "this is i",
            "ii": "this is ii"
        },
        "d": {
            "1": "this is 1",
            "2": "this is 2"
        }
    }
    
    combined = combine_template_sections("a", ["b"], deepcopy(test_note))

    
    assert combined == {'a': 'this is a\nthis is b',
                        'c': {'i': 'this is i', 'ii': 'this is ii'},
                        'd': {'1': 'this is 1', '2': 'this is 2'}}
    
    combined = combine_template_sections("a", ["c"], deepcopy(test_note))

    assert combined == {'a': 'this is a\ni: this is i\nii: this is ii',
                        'b': 'this is b',
                        'd': {'1': 'this is 1', '2': 'this is 2'}}
    
    combined = combine_template_sections("c", ["d"], deepcopy(test_note))

    assert combined == {'a': 'this is a',
                        'b': 'this is b',
                        'c': {'1': 'this is 1',
                              '2': 'this is 2',
                              'i': 'this is i',
                              'ii': 'this is ii'}}
    
    combined = combine_template_sections("c", ["b"], deepcopy(test_note))

    assert combined == {'a': 'this is a',
                        'c': {'i': 'this is i', 'ii': 'this is ii\n\nthis is b'},
                        'd': {'1': 'this is 1', '2': 'this is 2'}}