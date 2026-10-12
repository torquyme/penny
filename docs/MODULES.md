# Module API v1

Modules are directories immediately below `modules/`. Discovery looks for `*/module.json`. No core edits or registration calls are needed.

## Manifest

```json
{
  "api_version": 1,
  "id": "my_module",
  "name": "My module",
  "version": "1.0.0",
  "description": "Describe what this module does and its network activity.",
  "category": "Discovery",
  "entrypoint": "main.py",
  "timeout_seconds": 30,
  "inputs": [
    {"key": "target", "label": "Target", "type": "string", "required": true},
    {"key": "limit", "label": "Limit", "type": "integer", "default": 10},
    {"key": "verbose", "label": "Verbose", "type": "boolean", "default": false}
  ]
}
```

- API version must be `1`. IDs must be unique, start with a lowercase letter, and use letters, digits, underscores or hyphens (up to 64 characters).
- Entrypoint must be an existing `.py` file within the module directory.
- Timeouts range from 1 to 300 seconds; default is 30.
- Inputs support `string`, `integer` and `boolean`. Every input needs a unique lowercase identifier key and a label. `required` defaults to false. `multiline: true` renders a text area for strings.
- The host validates types and required fields. Modules validate semantic constraints such as URL scheme, limits, port ranges and target scope.
- Defaults must match their declared type. Optional fields without values may be absent from `inputs`; use `inputs.get()`.

## Entrypoint

```python
from toolkit.sdk import finding

def run(context, inputs):
    context.log(f"Inspecting {inputs['target']}")
    return {
        "summary": "Assessment complete",
        "data": {"target": inputs["target"]},
        "findings": [finding("Observation", "Evidence to review", "info")]
    }
```

`context.run_id` identifies the run. `context.log(message)` collects messages. A module must expose `run(context, inputs)` and return a JSON-compatible object with a string `summary`. `data` is optional JSON-compatible content. `findings` is optional and contains objects with string `title`, `description`, and `severity` (`info`, `low`, `medium`, `high`, `critical`). NaN and Infinity are rejected. Printed stdout is captured as a log; use `context.log()` for clarity. Results and logs appear when execution finishes.

The host imports the entrypoint in a fresh worker using the application's Python interpreter. Bundled modules use only the standard library. Additional dependencies currently need manual installation into that interpreter. Package-relative imports and automatic dependency installation are not provided by API v1.

Raise an exception for a failed assessment. The host surfaces its type and message and keeps the UI responsive. Handle expected conditions (for example HTTP 404) as structured data when useful. Set network timeouts below the module timeout. Manage cleanup of files, connections and child processes yourself. Worker termination cannot undo side effects.

## Run record

JSON export uses `schema_version: 1`, `run_id`, UTC `started_at` and `finished_at`, module ID/version, validated inputs, status and logs. Status is one of `completed`, `failed`, `cancelled`, or `timed_out`. Successful runs contain `result`; failed runs include `error`. Inputs are exported verbatim: API v1 has no secret input type, so do not add passwords or tokens as ordinary inputs.

## Compatibility

Keep `api_version: 1` for modules using this contract. Bump your module's own version when its behavior changes. Breaking host contracts require a new API version. Discovery rejects unsupported versions instead of executing them.


## Contributor CLI

See [DEVELOPER_WORKFLOW.md](DEVELOPER_WORKFLOW.md). Scaffold with `python -m toolkit.dev new my_module`, then run `python -m toolkit.dev validate modules/my_module`. The static validator requires an explicit top-level synchronous `def run(context, inputs)` with two positional parameters and no variadic/keyword-only parameters. It does not import or execute the entrypoint. `python -m toolkit.dev run my_module` exercises the real worker/result contract.
