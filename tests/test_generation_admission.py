import pytest
import pytest_asyncio

from src.data_generator import generate_admissions

admission_generator = generate_admissions(elective_admission_rate = 0)

def test_chief_complaint_generation():
    """
    Confirm that age, chief complaint and diagnosis are generated correctly
    as part of admission complaint generation
    """
    admission_details = admission_generator.generate_emergency_admission_complaint("M", 77)
    
    assert len(admission_details["chief_complaint"]) > 0
    assert len(admission_details["diagnosis"]) > 0