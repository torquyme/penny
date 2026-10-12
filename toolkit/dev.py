"""Module authoring CLI: scaffold, statically validate, list, and run extensions."""
import argparse
import ast
import json
from pathlib import Path
import re
import tempfile

from toolkit.modules import discover, read_module
from toolkit.runner import Execution, ROOT

TEMPLATE = '''"""Replace this offline example with your assessment task."""
from toolkit.sdk import finding


def run(context, inputs):
    target = inputs["target"]
    context.log(f"Example module received {target}")
    return {"summary": "Example completed (no network requests)",
            "data": {"target": target},
            "findings": [finding("Example observation", "Replace with evidence from your module.")]}
'''


def scaffold(root: Path, module_id: str, name: str | None = None) -> Path:
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", module_id):
        raise ValueError("Module ID must start with a lowercase letter and use up to 64 lowercase letters, digits, _ or -")
    display_name = name if name is not None else module_id.replace("_", " ").replace("-", " ").title()
    if not display_name.strip():
        raise ValueError("Module name cannot be blank")
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = root / module_id
    if destination.exists():
        raise ValueError(f"Destination already exists: {destination}")
    modules, errors = discover(root)
    if errors:
        raise ValueError("Fix existing module discovery errors before scaffolding: " + "; ".join(errors))
    if any(module.id == module_id for module in modules):
        raise ValueError(f"Module ID already registered: {module_id}")
    with tempfile.TemporaryDirectory(prefix=".scaffold-", dir=root) as temporary:
        staged = Path(temporary) / module_id
        staged.mkdir()
        manifest = {"api_version": 1, "id": module_id, "name": display_name, "version": "0.1.0",
                    "description": "Offline example. Replace this description with the task and its network behavior.",
                    "category": "Community", "entrypoint": "main.py", "timeout_seconds": 30,
                    "inputs": [{"key": "target", "label": "Target", "type": "string", "required": True, "default": "localhost"}]}
        (staged / "module.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (staged / "main.py").write_text(TEMPLATE, encoding="utf-8")
        (staged / "README.md").write_text(f"# {display_name}\n\nDescribe scope, dependencies, evidence and local acceptance tests here.\n", encoding="utf-8")
        staged.rename(destination)
    return destination


def validate(directory: Path):
    module = read_module(directory)
    tree = ast.parse(module.entrypoint.read_text(encoding="utf-8"), filename=str(module.entrypoint))
    compile(tree, str(module.entrypoint), "exec")
    entry = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run"), None)
    if entry is None or len(entry.args.posonlyargs + entry.args.args) != 2 or entry.args.kwonlyargs or entry.args.vararg or entry.args.kwarg:
        raise ValueError("Entrypoint must declare a top-level synchronous run(context, inputs) function")
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="Create an offline example module")
    new.add_argument("id")
    new.add_argument("--name")
    new.add_argument("--root", type=Path, default=ROOT / "modules")
    for command in ("list", "validate", "run"):
        sub = commands.add_parser(command)
        sub.add_argument("--root", type=Path, default=ROOT / "modules")
        if command == "validate":
            sub.add_argument("directory", type=Path, nargs="?")
        elif command == "run":
            sub.add_argument("id")
            sub.add_argument("--inputs", type=Path, help="JSON object file; omitted fields use declared defaults")
            sub.add_argument("--output", type=Path, help="Write the JSON run record to this file")
    args = parser.parse_args(argv)
    try:
        if args.command == "new":
            print(f"Created {scaffold(args.root, args.id, args.name)}")
            return 0
        if args.command == "validate" and args.directory:
            module = validate(args.directory)
            print(f"PASS {module.id} v{module.version} (static checks only; module code not executed)")
            return 0
        modules, errors = discover(args.root)
        if errors:
            raise ValueError("\n".join(errors))
        if args.command == "list":
            for module in modules:
                print(f"{module.id}  v{module.version}  {module.name}")
        elif args.command == "validate":
            if not modules:
                raise ValueError("No modules found")
            for module in modules:
                validate(module.directory)
                print(f"PASS {module.id} (static checks only)")
        else:
            module = next((module for module in modules if module.id == args.id), None)
            if module is None:
                raise ValueError(f"Module not found: {args.id}")
            inputs = json.loads(args.inputs.read_text(encoding="utf-8")) if args.inputs else {}
            if not isinstance(inputs, dict):
                raise ValueError("Inputs file must contain a JSON object")
            record = Execution(module, inputs).run()
            output = json.dumps(record, indent=2, ensure_ascii=False)
            if args.output:
                args.output.write_text(output + "\n", encoding="utf-8")
            print(output)
            return 0 if record["status"] == "completed" else 1
    except (OSError, ValueError, TypeError, SyntaxError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
