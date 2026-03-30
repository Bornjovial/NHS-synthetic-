# Changelog

All notable changes to this project are documented here.

---

## [Unreleased] — `local-model-adaptation` branch

### Added

- **Checkpoint / resume** (`--resume` flag): stages 3–5 (journeys, clinical notes, augmentations) append each completed patient to a checkpoint CSV immediately after processing. On restart with `--resume`, completed patients are skipped and the checkpoint is atomically promoted to the final intermediate file on completion. (`e3ae5a2`)

- **LLM call observability**: every call to `call_llm` now records timestamp, stage, model, success, attempt count, latency, and token usage to a timestamped `output/run_stats_<timestamp>.jsonl` file. A stage summary (total calls, failure rate, mean/p95 latency, total tokens) is logged at the end of each pipeline stage. (`29bd16c`)

- **`--evaluate` flag**: runs LLM-judged quality scoring (fluency, groundedness, relevance — each 1–5) and readability metrics (Flesch, Dale-Chall) over all generated notes after the pipeline completes; writes `output/evaluation_results.csv`. Integrates the previously notebook-only `evaluation_utils.py` directly into the pipeline. (`29bd16c`)

- **`run_pipeline.py` script entrypoint**: canonical way to run the pipeline in production. Supports `--generations`, `--model`, `--data-dir`, `--output-dir`, `--concurrency`, `--test-mode`, `--run-name`, `--resume`, `--evaluate`. Logs to stdout and a timestamped file under `logs/`. Exits with code 1 on stage failure. (`45252de`)

- **Preflight checks**: on startup, `run_pipeline.py` validates that the LLM endpoint is reachable, all required input CSVs exist, and the output directory is writable — before making any LLM calls. (`7b21834`)

- **Configurable concurrency** (`llm_concurrency` param, `--concurrency` flag): the asyncio semaphore that limits concurrent LLM calls is now configurable. Defaults to 4; recommended 2–4 for local models, 8–16 for hosted APIs. (`eaf42d4`)

- **`llm_num_ctx` / `llm_max_tokens` params**: context window size and max generation tokens are now configurable in `params.py` and passed through to the API on every call. (`cc787c8`)

- **Atomic intermediate writes**: `read_write_data` writes to a `.tmp` file then uses `os.replace` (atomic on POSIX) to promote it, preventing partial files from corrupting subsequent stages on crash. (`eaf42d4`)

- **Singleton OpenAI client**: the `OpenAI` client is created once at module level rather than per-call, eliminating repeated connection setup overhead. (`8c33d9d`)

- **`LLM_API_KEY` from environment variable**: `LLM_API_KEY` is read from the `LLM_API_KEY` environment variable if set, rather than always using the hardcoded value in `config.py`. (`eaf42d4`)

- **Integration tests**: mocked LLM integration tests for all five pipeline stages, covering output shape and schema validation without requiring a live LLM server. (`e281bbf`, `e854989`)

### Changed

- **Local OpenAI-compatible LLM support**: replaced Palantir Foundry platform dependencies with a direct OpenAI-compatible client. The pipeline now works out of the box with Ollama, vLLM, or the OpenAI API. (`87c246c`)

- **`DATA_DIR` / `OUTPUT_DIR` use absolute paths**: prevents working-directory-dependent path resolution issues when running the pipeline from different locations. (`cc787c8`)

- **Test suite refactored**: extracted shared stubs to `tests/stubs.py`, fixed fixture scoping, and corrected raw-string regexes. (`a3fb343`, `1a04508`)

### Fixed

- Name filtering and append-on-missing-file behaviour in dataset utils. (`248e351`)
- `evaluation_utils` temperature parameter and duplicate journey check. (`bef1cd9`)
- Trailing comma tuple, duplicate imports, and `elif` logic bugs. (`2a00a91`)

---

## [Initial release] — `05bb3d1`

Initial pipeline code for synthetic clinical note generation, originally written for Palantir Foundry.
