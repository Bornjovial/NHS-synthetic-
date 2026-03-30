# Adapting the Pipeline

This pipeline was designed to be versatile and configurable, allowing for the creation of a wide variety of clinical notes.

As a result, there are a number of files you can adapt to change the behavior of the pipeline:

## 1. `config/params.py`

This file contains the basic parameters needed to run the pipeline. Example parameters include:

1. **TEST_MODE** - If True, runs pipeline in test mode and generates one clinical note per patient.
2. **model** - The model name to pass to the LLM endpoint. Must match the model name served by your local server (e.g. `"qwen2.5:72b"` for Ollama, `"Qwen/Qwen2.5-72B-Instruct-AWQ"` for vLLM).
3. **llm_concurrency** - Maximum number of concurrent LLM calls. Reduce for local models (2–4); increase for hosted APIs (8–16). Can also be set via `--concurrency` on the command line.
4. **llm_num_ctx** - Context window size passed to the model (e.g. `8192`). Overrides the server default. No effect on Ollama — set `num_ctx` in a Modelfile instead (see README).
5. **llm_max_tokens** - Maximum tokens the model may generate per response.
6. **number_of_generations** - The number of patient journeys to generate.
7. **resume** - If True, resumes an interrupted run by skipping already-completed patients and appending to checkpoint files. Enable via `--resume` on the command line rather than editing this file directly.
8. **evaluate** - If True, runs LLM-judged quality evaluation (fluency, groundedness, relevance) and readability scoring after the pipeline completes, writing `evaluation_results.csv`. Enable via `--evaluate` on the command line.
9. **number_of_staff_names** - The number of staff names (approximately) to generate for each patient journey.
10. **elective_admissions_dataset / emergency_admissions_dataset / patients_input_dataset** - Filename stems (without `.csv`) of input data files to read from `DATA_DIR`.

Each parameter has a comment next to it explaining exactly what it does.

## 2. `config/config.py`

This file is similar to `params.py`. However, we expect you will not need to make as many changes to the file. Example parameters within the config include:

1. **LLM_BASE_URL** - The base URL of the OpenAI-compatible API server (e.g. `http://localhost:11434/v1` for Ollama, `http://localhost:8000/v1` for vLLM, or `https://api.openai.com/v1` for the OpenAI API).
2. **LLM_API_KEY** - API key for the LLM endpoint. Set to `"not-needed"` for local servers that don't require authentication.
3. **DATA_DIR** - Directory to read input CSV files from (default: `./data`).
4. **OUTPUT_DIR** - Directory to write generated output CSV files to (default: `./output`).
5. **possible_event_types** - A dictionary containing the possible event types and descriptions to be used when generating clinical notes.
6. **doctor_roles** - The possible roles that can be assigned to a doctor.
7. **sections_to_ignore_typos** - Note sections where you do not wish to add typos.
8. **style_instructions** - The medical professional personas used to add variation to clinical notes.
9. **allergy_prevalence** - The prevalence of different allergies, sampled when generating patients.

## 3. `src/doc_templates.py`

This file contains detailed document templates used when generating clinical notes. Examples include:

1. **patient_details** - The expected output from an LLM generating a patient.
2. **elective admission** - The style and expected output of an elective admission note.
3. **general ward round** - The style and expected output of a general ward round note note.

These templates are injected directly into LLM prompts. The description of each key directly effects the quality of the note generated. As these notes were designed with input from clinicians, and large changes may need changes in the downstream code, be **very careful** changing this file.

## 4. `src/prompts.py`

This file contains **all** prompts for our pipeline. Prompts are organised into the section of the pipeline they are used in:

1. Patients and Admissions
2. Patient Journeys
3. Clinical Notes
4. Processing
5. Evaluation Prompts

As these prompts were carefully designed and iterated with input from clinicians, be **very careful** changing this file.

## 5. `src/schemas.py`

This file contains schemas used for saving final outputs. You may wish to change this file depending on your use case for generating synthetic clinical notes.
