# Changing Functions

The pipeline was originally written for [Palantir Foundry](https://www.palantir.com/platforms/foundry/), but has been adapted to run locally using any OpenAI-compatible API server.

The two platform-specific functions in `src/processing.py` now use the `openai` Python SDK with a configurable `base_url`, so they work with Ollama, vLLM, the OpenAI API, or any other compatible endpoint. If you need to adapt them further (e.g. for a different SDK or storage backend), the interface contracts below still apply.

## 1. `call_llm`

The `call_llm` function is the single abstraction layer between the pipeline and the language model provider.

If you wish to use a different LLM provider (e.g., OpenAI, Azure, Anthropic, a local model, etc.), you should modify only the internal implementation of this function, while keeping its interface unchanged.

Maintaining the same inputs and outputs is essential for ensuring that the rest of the pipeline continues to function correctly.

**Inputs**

| Parameter      | Type                | Description                                                                                       |
| -------------- | ------------------- | ------------------------------------------------------------------------------------------------- |
| `prompt`       | `str`               | The latest user prompt to send to the model.                                                      |
| `model`        | object              | A handle or identifier for the model to use. The exact format can vary depending on the provider. |
| `temp`         | `float`             | Sampling temperature controlling output randomness.                                               |
| `max_attempts` | `int`               | Number of retry attempts if the request fails.                                                    |
| `chat_history` | `list[str] \| None` | Optional alternating conversation history: `[user_0, assistant_0, user_1, assistant_1, ...]`.     |

**Outputs**

Required Output

The function must return a `String`.

Specifically:

- The raw text content produced by the LLM.
- If all retries fail, the function should return `None`.
- No other return types should be introduced.

**Behavioral Requirements**

Any replacement implementation should preserve the following behavior:

1. Prompt Handling

- The prompt must always be appended as the latest user message.
  
2. Chat History Formatting

- `chat_history` is provided as an alternating list of user and assistant messages.
- Implementations must convert this into the format required by the chosen LLM API.
  
3. Retry Logic

- The function should retry failed calls up to `max_attempts`.
- Errors should be logged or printed for debugging.
  
4. Temperature Control

The temp parameter must be passed through to the provider if supported.

5. Graceful Failure

If all attempts fail, the function should:

- log the failure
- return None.

## 2. `read_write_data`

The `read_write_data` function acts as the abstraction layer between the pipeline and the underlying data storage system.

Currently, it uses the `Dataset` API to read and write tables. If you wish to use a different storage system (e.g., local files, SQL databases, cloud storage, or another data platform), you should modify only the internal implementation of this function while keeping the function interface unchanged.

Maintaining the same inputs and outputs ensures the rest of the pipeline continues to work without modification.

**Inputs**

| Parameter       | Type                   | Description                                                                                                                                       |
| --------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `table_name`    | `str`                  | Identifier of the dataset to read from or write to. The interpretation of this name depends on the storage backend (table name, file path, etc.). |
| `read_or_write` | `str`                  | Operation to perform. Must be `"read"` or `"write"`.                                                                                              |
| `data`          | `pd.DataFrame \| None` | DataFrame to write when `read_or_write="write"`. Ignored when reading. |

**Outputs**

The function must return:

- `pd.DataFrame` when `read_or_write == "read"`
- `None` when `read_or_write == "write"`

The pipeline assumes these exact return behaviors.

**Behavioral Requirements**

Any replacement implementation should preserve the following behavior:

1. Read Operation

- When `read_or_write == "read"`, the function must retrieve the dataset identified by `table_name`.
- The returned object must be a pandas DataFrame.

2. Write Operation

- When `read_or_write == "write"`, the function must write the provided DataFrame to the dataset.
- The function should return None.

3. Validation

- If `read_or_write` is not `"read"` or `"write"`, the function should raise an exception.
- If `read_or_write == "write"` but `data` is `None`, an exception should also be raised.

4. DataFrame Compatibility

- All reads must return data in a pandas DataFrame format, even if the underlying system uses a different structure (e.g., Arrow tables or SQL query results).
