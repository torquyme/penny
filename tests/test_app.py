import json
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from toolkit.app import App


class DesktopTests(unittest.TestCase):
    def setUp(self):
        try:
            probe = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Desktop display unavailable: {exc}")
        probe.destroy()
        self.app = App()
        self.addCleanup(self.app.destroy)
        self.app.update()

    def test_inventory_run_display_and_export(self):
        index = next(i for i, m in enumerate(self.app.visible) if m.id == "target_inventory")
        self.app.library.selection_clear(0, "end")
        self.app.library.selection_set(index)
        self.app._select()
        self.app._run()
        self.assertIsNotNone(self.app.execution)
        deadline = time.monotonic() + 5
        while self.app.execution and time.monotonic() < deadline:
            self.app.update()
            time.sleep(0.01)
        self.assertIsNone(self.app.execution)
        self.assertEqual(self.app.record["status"], "completed")
        self.assertIn("3 targets ready", self.app.results.get("1.0", "end"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch("toolkit.app.filedialog.asksaveasfilename", return_value=str(output)):
                self.app._export()
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), self.app.record)

    def test_search_empty_state_and_recovery(self):
        self.app.search.set("no-such-module")
        self.app.update()
        self.assertIsNone(self.app.selected)
        self.assertEqual(str(self.app.run_button["state"]), "disabled")
        self.app.search.set("inventory")
        self.app.update()
        self.assertEqual(self.app.selected.id, "target_inventory")
        self.assertEqual(str(self.app.run_button["state"]), "normal")

    def test_dns_module_form_and_execution(self):
        self.app.search.set("DNS address")
        self.app.update()
        self.assertEqual(self.app.selected.id, "dns_analysis")
        self.assertIn("reverse", self.app.controls)
        self.assertFalse(self.app.controls["reverse"][1]())
        self.app._run()
        deadline = time.monotonic() + 5
        while self.app.execution and time.monotonic() < deadline:
            self.app.update()
            time.sleep(0.01)
        self.assertIsNone(self.app.execution)
        self.assertEqual(self.app.record["status"], "completed")
        self.assertIn("entries resolved", self.app.results.get("1.0", "end"))


if __name__ == "__main__":
    unittest.main()
