# Input Data

There are three input tables that need to be passed to the pipeline:

1. `elective_admissions_dataset`
2. `emergency_admissions_dataset`
3. `patients_input_dataset`

Examples of each table are included in the repo. These were used when testing the pipeline so should create realistic notes.

Details regarding each dataset are documented below:

## Elective Admissions Dataset

This dataset contains the columns:

- **Age_Category**: String of form 'x-y' where x and y are number representing the lower bound and higher bound of an age respectively.
- **Sex**: String of 'Male' or 'Female'.
- **Speciality**: String containing speciality for the admission. e.g. 'Orthopaedics'.
- **Procedure**: String containing a short description of the procedure.

❇️ **Tip** ❇️ If appropriate, include 'left' or 'right' in the procedure description.

## Emergency Admissions Dataset

- **Age_Category**: String of form 'x-y' where x and y are number representing the lower bound and higher bound of an age respectively.
- **Sex_Category**: String of 'Male' or 'Female'.
- **ChiefComplaintDescription**: String containing description of chief complaint.
- **DiagnosisDescription**: String containing description of the diagnosis.
- **rare_disease**: Integer `1` or `0` flagging if disease is rare.
- **NovelDiseaseFlag**: Integer `1` or `0` flagging if disease is novel.
- **AdditionalSymptoms**: String or `None` containing details on additional symptoms - useful for novel diseases.
- **AdditionalInformation**: String or `None` containing additional information. Useful for novel diseases.
- **ConfirmedBy**: String or `None` containing details on what confirmed the diagnosis, e.g. a swab. Useful for novel diseases.
- **SupportedBy**: String ot `None` containing details on information supporting the diagnosis, e.g. a rash. Useful for novel diseases.

❇️ **Tips** ❇️

- If appropriate, include 'left' or 'right' in descriptions.

## Patients Input Dataset

- **FIRST**: String of first name.
- **MIDDLE**: String of middle name.
- **LAST**: String of last name.
- **RACE**: String of race. Not currently used in pipeline but could be used for evaluation purposes.
- **ETHNICITY**:  String of ethnicity. Not currently used in pipeline but could be used for evaluation purposes.
- **GENDER**: String of gender. `M` or `F`.
- **ADDRESS**: String of synthetic address.
- **CITY**: String of city.
- **POSTCODE**: String of first half of postcode. e.g. `PL1`.

## Setting Up

This pipeline was tested in Foundry. Therefore, tables were read and written using the `read_write_data` function.

Please see the `changing_functions.md` document for more details.
