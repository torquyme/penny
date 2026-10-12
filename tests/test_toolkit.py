import json
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from toolkit.modules import discover, read_module, validate_inputs
from toolkit.runner import Execution, ROOT


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make_module(self, code, **overrides):
        directory = self.root / "sample"
        directory.mkdir(exist_ok=True)
        manifest = {"api_version": 1, "id": "sample", "name": "Sample", "version": "1.0.0",
                    "description": "Test fixture", "category": "Test", "entrypoint": "main.py", "inputs": []}
        manifest.update(overrides)
        (directory / "module.json").write_text(json.dumps(manifest), encoding="utf-8")
        (directory / "main.py").write_text(code, encoding="utf-8")
        return directory

    def test_discovery_never_imports_module(self):
        self.make_module("raise RuntimeError('must not import during discovery')")
        modules, errors = discover(self.root)
        self.assertEqual([m.id for m in modules], ["sample"])
        self.assertEqual(errors, [])

    def test_invalid_manifest_is_skipped(self):
        directory = self.make_module("", api_version=2)
        modules, errors = discover(self.root)
        self.assertEqual(modules, [])
        self.assertIn("api_version", errors[0])
        (directory / "module.json").write_text("[]", encoding="utf-8")
        self.assertIn("manifest must be an object", discover(self.root)[1][0])

    def test_entrypoint_cannot_escape_directory(self):
        (self.root / "outside.py").write_text("", encoding="utf-8")
        directory = self.make_module("", entrypoint="../outside.py")
        with self.assertRaisesRegex(ValueError, "inside"):
            read_module(directory)

    def test_duplicate_ids_rejected(self):
        directory = self.make_module("")
        duplicate = self.root / "duplicate"
        duplicate.mkdir()
        (duplicate / "module.json").write_text((directory / "module.json").read_text(), encoding="utf-8")
        (duplicate / "main.py").write_text("", encoding="utf-8")
        modules, errors = discover(self.root)
        self.assertEqual(len(modules), 1)
        self.assertIn("Duplicate", errors[0])

    def test_validation_and_defaults(self):
        module = read_module(self.make_module("", inputs=[
            {"key": "target", "label": "Target", "type": "string", "required": True},
            {"key": "count", "label": "Count", "type": "integer", "default": 2}]))
        self.assertEqual(validate_inputs(module, {"target": "localhost"}), {"target": "localhost", "count": 2})
        for values in ({}, {"target": " "}, {"target": "localhost", "count": True}, {"target": "localhost", "extra": 1}):
            with self.assertRaises(ValueError):
                validate_inputs(module, values)

    def test_worker_success_unicode_and_print_capture(self):
        code = "def run(context, inputs):\n    print('captured output')\n    context.log('café')\n    return {'summary': 'Done ✓', 'data': {'count': 3}}\n"
        record = Execution(read_module(self.make_module(code)), {}).run()
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["result"]["summary"], "Done ✓")
        self.assertEqual(record["logs"], ["café", "captured output"])
        self.assertIn("finished_at", record)

    def test_worker_failure_and_invalid_result(self):
        for code in ("def run(context, inputs):\n    raise ValueError('expected failure')\n",
                     "def run(context, inputs):\n    return {'summary': 'x', 'findings': [{'bad': True}]}\n"):
            record = Execution(read_module(self.make_module(code)), {}).run()
            self.assertEqual(record["status"], "failed")
            self.assertIn("ValueError", record["error"])

    def test_timeout(self):
        code = "import time\ndef run(context, inputs):\n    time.sleep(10)\n"
        record = Execution(read_module(self.make_module(code, timeout_seconds=1)), {}).run()
        self.assertEqual(record["status"], "timed_out")

    def test_cancel_running_worker(self):
        code = "import time\ndef run(context, inputs):\n    time.sleep(10)\n"
        execution = Execution(read_module(self.make_module(code)), {})
        results = []
        thread = threading.Thread(target=lambda: results.append(execution.run()))
        thread.start()
        deadline = time.monotonic() + 3
        while execution.process is None and time.monotonic() < deadline:
            time.sleep(0.01)
        execution.cancel()
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0]["status"], "cancelled")

    def test_inventory_normalizes_and_rejects(self):
        module = read_module(ROOT / "modules" / "target_inventory")
        record = Execution(module, {"targets": "EXAMPLE.COM\nexample.com\n192.168.1.5/24\n999.999.1.1\nhttps://user:password@example.com\nhttps://example.com:bad\n"}).run()
        self.assertEqual(record["status"], "completed")
        data = record["result"]["data"]
        self.assertEqual([x["value"] for x in data["targets"]], ["example.com", "192.168.1.0/24"])
        self.assertEqual(len(data["rejected"]), 3)

    def test_http_local_server_and_no_redirect_following(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self):
                requests.append(self.path)
                self.send_response(302 if self.path == "/redirect" else 200)
                if self.path == "/redirect":
                    self.send_header("Location", "/destination")
                self.send_header("Content-Security-Policy", "default-src 'self'")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        module = read_module(ROOT / "modules" / "http_headers")
        for path, status in (("/", 200), ("/redirect", 302)):
            record = Execution(module, {"url": f"http://127.0.0.1:{server.server_port}{path}"}).run()
            self.assertEqual(record["status"], "completed", record)
            self.assertEqual(record["result"]["data"]["status"], status)
        self.assertEqual(requests, ["/", "/redirect"])


if __name__ == "__main__":
    unittest.main()
