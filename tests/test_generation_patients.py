from src.data_generator import generate_patients

patient_generator = generate_patients()

def test_generate_allergies():
    """
    Test the generation of allergies.
    """
    
    allergy_prevalence = {
    "pollen" : 0, 
    }
    
    assert patient_generator.generate_patient_allergies(allergy_prevalence) == "None"
    
    allergy_prevalence = {
    "pollen" : 1, 
    }
    
    assert patient_generator.generate_patient_allergies(allergy_prevalence) == "pollen"
    
    allergy_prevalence = {
    "pollen" : 1,
    "nuts" : 1
    }
    
    allergies = patient_generator.generate_patient_allergies(allergy_prevalence)
    
    assert "nuts" in allergies
    assert "pollen" in allergies