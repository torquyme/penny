# Module contributor workflow

Run these commands from the project root with Python 3.11 or newer. No extra Python packages are required by the scaffold.

## Create and exercise a module

```powershell
python -m toolkit.dev new my_module --name "My module"
python -m toolkit.dev validate modules/my_module
python -m toolkit.dev run my_module
```

The scaffold creates `modules/my_module/module.json`, `main.py` and `README.md`. It is an offline example and does not send network requests. The generator rejects invalid IDs, duplicate IDs and existing directories; it never overwrites a module. Click **Reload modules** in the desktop app to see the new entry.

Use `--root path` to work with an alternate library. IDs use lowercase letters, digits, underscores or hyphens and start with a letter, up to 64 characters.

## Validate versus execute

```powershell
python -m toolkit.dev list
python -m toolkit.dev validate
```

`validate` checks manifest discovery, declared defaults, source syntax and an explicit top-level synchronous two-argument `run(context, inputs)` function. It does not import extension code. A static pass does not guarantee JSON compatibility or assessment correctness.

`run` invokes the same worker used by the desktop. The worker checks the returned summary and findings, JSON serialization and the execution timeout. Invalid results or exceptions produce a failed run and exit code 1. A successful module execution exits 0; completed observations may still include failed individual checks, so inspect the result.

## Inputs and exports

Create `inputs.json`:

```json
{"target": "localhost"}
```

Then run:

```powershell
python -m toolkit.dev run my_module --inputs inputs.json --output my-module-run.json
```

Omitted fields use their declared defaults. The file must contain a JSON object. Inputs and records follow the same rules as desktop execution; there is no secret-input contract yet. Output paths are explicit and may overwrite a file when requested.

## Implementation checklist

1. Replace the template task, description and category; document network activity and dependencies.
2. Keep assessment logic inside the module. Use `toolkit.sdk.ModuleContext` and `finding` through the published API.
3. Validate semantic input constraints inside `run` and keep network timeouts bounded.
4. Return JSON-compatible evidence and observations with reviewable severity claims.
5. Add fixture tests for successful results, expected errors and semantic rejection. `tests/test_dns.py` demonstrates mock-based module testing.
6. Validate and execute the module, then run the applicable project tests.

All field types are available through manifest declarations: strings (with optional `multiline: true`), integers and booleans. Supported findings severities are `info`, `low`, `medium`, `high`, `critical`. See [MODULES.md](MODULES.md) for the exact contract.

Package-relative imports and automatic dependency installation remain unsupported. The project does not claim that installing a module makes its code safe; static validation is a compatibility check, not a security sandbox.
