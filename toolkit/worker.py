"""Private subprocess entrypoint. Stdout is reserved for one JSON response."""
import contextlib
import importlib.util
import io
import json
import sys
import traceback

from toolkit.sdk import ModuleContext


def main() -> None:
    captured = io.StringIO()
    context = None
    try:
        request = json.load(sys.stdin)
        context = ModuleContext(request["run_id"])
        with contextlib.redirect_stdout(captured):
            spec = importlib.util.spec_from_file_location("toolkit_extension", request["entrypoint"])
            extension = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = extension
            spec.loader.exec_module(extension)
            result = extension.run(context, request["inputs"])
        if not isinstance(result, dict) or not isinstance(result.get("summary"), str):
            raise ValueError("run() must return an object with a string summary")
        findings = result.get("findings", [])
        if not isinstance(findings, list):
            raise ValueError("findings must be a list")
        for item in findings:
            if not isinstance(item, dict) or not all(isinstance(item.get(k), str) for k in ("title", "description", "severity")):
                raise ValueError("Each finding requires title, description and severity strings")
            if item["severity"] not in {"info", "low", "medium", "high", "critical"}:
                raise ValueError("Invalid finding severity")
        response = {"ok": True, "result": result, "logs": context.logs}
        json.dumps(response, allow_nan=False)
    except Exception as exc:
        response = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                    "logs": context.logs if context else []}
        traceback.print_exc(file=sys.stderr)
    if captured.getvalue():
        response["logs"].append(captured.getvalue().strip())
    sys.stdout.write(json.dumps(response, allow_nan=False))


if __name__ == "__main__":
    main()
