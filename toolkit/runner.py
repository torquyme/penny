"""Run trusted local extensions in separate, cancellable worker processes."""
import json
import os
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from toolkit.modules import Module, validate_inputs

ROOT = Path(__file__).resolve().parent.parent


class Execution:
    def __init__(self, module: Module, inputs: dict):
        self.module = module
        self.inputs = validate_inputs(module, inputs)
        self.cancelled = threading.Event()
        self.process = None
        self.lock = threading.Lock()

    def cancel(self) -> None:
        self.cancelled.set()
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                self.process.kill()

    def run(self) -> dict:
        record = {"schema_version": 1, "run_id": str(uuid.uuid4()),
                  "started_at": datetime.now(timezone.utc).isoformat(),
                  "module": {"id": self.module.id, "version": self.module.version},
                  "inputs": self.inputs, "status": "failed", "logs": []}
        try:
            with self.lock:
                if self.cancelled.is_set():
                    record["status"] = "cancelled"
                    return record
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                self.process = subprocess.Popen(
                    [sys.executable, "-m", "toolkit.worker"], cwd=ROOT, env=env,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            request = json.dumps({"run_id": record["run_id"], "entrypoint": str(self.module.entrypoint), "inputs": self.inputs})
            try:
                out, err = self.process.communicate(request, timeout=self.module.timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.communicate()
                record.update(status="timed_out", error=f"Module exceeded {self.module.timeout} seconds")
                return record
            if self.cancelled.is_set():
                record["status"] = "cancelled"
                return record
            if len(out.encode("utf-8")) > 2_000_000:
                raise ValueError("Module response exceeds 2 MB")
            if self.process.returncode != 0:
                raise RuntimeError(f"Worker exited with code {self.process.returncode}: {err[-2000:]}")
            response = json.loads(out)
            record["logs"] = response.get("logs", [])
            if response.get("ok"):
                record.update(status="completed", result=response["result"])
            else:
                record["error"] = response.get("error", "Module failed")
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            record["error"] = str(exc)
        finally:
            record["finished_at"] = datetime.now(timezone.utc).isoformat()
        return record
