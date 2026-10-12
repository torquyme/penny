import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from toolkit.dev import main, scaffold, validate
from toolkit.modules import discover
from toolkit.runner import Execution


class DeveloperWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "modules"

    def test_scaffold_discover_validate_execute_without_core_changes(self):
        directory = scaffold(self.root, "community_example", "Community example")
        modules, errors = discover(self.root)
        self.assertEqual(errors, [])
        self.assertEqual([module.id for module in modules], ["community_example"])
        module = validate(directory)
        record = Execution(module, {}).run()
        self.assertEqual(record["status"], "completed", record)
        self.assertEqual(record["result"]["data"]["target"], "localhost")

    def test_scaffold_refuses_invalid_id_and_existing_directory(self):
        for module_id in ("../escape", "BadId", "", "a" * 65):
            with self.assertRaises(ValueError):
                scaffold(self.root, module_id)
        directory = scaffold(self.root, "sample")
        before = (directory / "main.py").read_bytes()
        with self.assertRaises(ValueError):
            scaffold(self.root, "sample")
        self.assertEqual((directory / "main.py").read_bytes(), before)

    def test_validator_does_not_import_code(self):
        directory = scaffold(self.root, "sample")
        (directory / "main.py").write_text("raise RuntimeError('not imported')\ndef run(context, inputs):\n    return {}\n", encoding="utf-8")
        self.assertEqual(validate(directory).id, "sample")

    def test_invalid_signature_and_syntax_fail_validation(self):
        directory = scaffold(self.root, "sample")
        for code in ("def run(one):\n    pass\n", "async def run(context, inputs):\n    pass\n", "def broken(:\n"):
            (directory / "main.py").write_text(code, encoding="utf-8")
            with self.assertRaises((ValueError, SyntaxError)):
                validate(directory)

    def test_cli_runs_from_json_file_and_exports_record(self):
        scaffold(self.root, "sample")
        inputs = self.root.parent / "inputs.json"
        inputs.write_text(json.dumps({"target": "test.example"}), encoding="utf-8")
        output = self.root.parent / "result.json"
        with contextlib.redirect_stdout(io.StringIO()):
            status = main(["run", "sample", "--root", str(self.root), "--inputs", str(inputs), "--output", str(output)])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["inputs"], {"target": "test.example"})

    def test_cli_validation_failure_exit_status(self):
        directory = scaffold(self.root, "sample")
        (directory / "main.py").write_text("# no run entrypoint", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["validate", str(directory)])
        self.assertEqual(error.exception.code, 1)
