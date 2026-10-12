"""Windows-first Tk desktop interface; all module work happens off the UI thread."""
import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from toolkit.modules import discover
from toolkit.runner import Execution, ROOT
from toolkit.runtime import configure_tk

configure_tk()

BG, PANEL, FIELD, TEXT, MUTED, ACCENT = "#111820", "#19232e", "#22303e", "#edf3f9", "#a2b2c3", "#58d6b5"


class App(tk.Tk):
    def __init__(self, module_root: Path = ROOT / "modules"):
        super().__init__()
        self.title("Pentest Toolkit • Module workspace")
        self.geometry("1120x800")
        self.minsize(900, 640)
        self.configure(bg=BG)
        self.module_root = module_root
        self.modules = []
        self.visible = []
        self.selected = None
        self.execution = None
        self.record = None
        self.controls = {}
        self.events = queue.Queue()
        self._style()
        self._layout()
        self.reload()
        self.poll_timer = self.after(100, self._poll)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 23))
        style.configure("TButton", background=FIELD, foreground=TEXT, padding=(14, 8), borderwidth=0, font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#33485b")], foreground=[("disabled", MUTED)])
        style.configure("Run.TButton", background=ACCENT, foreground=BG)
        style.map("Run.TButton", background=[("active", "#7be7cc"), ("disabled", FIELD)], foreground=[("disabled", MUTED)])
        style.configure("TEntry", fieldbackground=FIELD, foreground=TEXT, insertcolor=TEXT, padding=8)
        style.configure("TCheckbutton", background=BG, foreground=TEXT)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(18, 9))
        style.map("TNotebook.Tab", background=[("selected", FIELD)], foreground=[("selected", TEXT)])

    def _layout(self):
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="PENTEST TOOLKIT", foreground=ACCENT, font=("Segoe UI Semibold", 10)).pack(anchor="w")
        ttk.Label(outer, text="Module workspace", style="Title.TLabel").pack(anchor="w", pady=(4, 3))
        ttk.Label(outer, text="Discover tools. Configure inputs. Keep the evidence.", style="Muted.TLabel").pack(anchor="w", pady=(0, 20))
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        sidebar = ttk.Frame(body, width=245)
        sidebar.pack(side="left", fill="y", padx=(0, 24))
        sidebar.pack_propagate(False)
        ttk.Label(sidebar, text="MODULE LIBRARY", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *_: self._filter())
        self.search_entry = ttk.Entry(sidebar, textvariable=self.search)
        self.search_entry.pack(fill="x", pady=(0, 10))
        self.library = tk.Listbox(sidebar, bg=PANEL, fg=TEXT, selectbackground="#315a60", selectforeground=TEXT,
                                  relief="flat", borderwidth=0, highlightthickness=0, font=("Segoe UI", 11),
                                  activestyle="none", exportselection=False)
        self.library.pack(fill="both", expand=True)
        self.library.bind("<<ListboxSelect>>", self._select)
        self.count = ttk.Label(sidebar, style="Muted.TLabel")
        self.count.pack(anchor="w", pady=10)
        self.reload_button = ttk.Button(sidebar, text="Reload modules", command=self.reload)
        self.reload_button.pack(fill="x")
        main = ttk.Frame(body)
        main.pack(side="left", fill="both", expand=True)
        self.name = ttk.Label(main, text="Select a module", font=("Segoe UI Semibold", 18))
        self.name.pack(anchor="w")
        self.meta = ttk.Label(main, style="Muted.TLabel")
        self.meta.pack(anchor="w", pady=(3, 8))
        self.description = ttk.Label(main, wraplength=670)
        self.description.pack(anchor="w", fill="x", pady=(0, 12))
        self.form = ttk.Frame(main)
        self.form.pack(fill="x")
        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=12)
        self.run_button = ttk.Button(actions, text="Run module", style="Run.TButton", command=self._run)
        self.run_button.pack(side="left")
        self.cancel_button = ttk.Button(actions, text="Cancel", command=self._cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=8)
        self.export_button = ttk.Button(actions, text="Export JSON", command=self._export, state="disabled")
        self.export_button.pack(side="right")
        self.status = ttk.Label(main, text="Ready", foreground=ACCENT)
        self.status.pack(anchor="w", pady=(0, 8))
        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True)
        self.results = self._text_tab(notebook, "Results")
        self.logs = self._text_tab(notebook, "Run log")
        self.raw = self._text_tab(notebook, "JSON")
        ttk.Label(outer, text="API v1  •  Local modules  •  Separate worker processes", style="Muted.TLabel").pack(anchor="w", pady=(14, 0))

    def _text_tab(self, notebook, label):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=label)
        text = tk.Text(frame, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", wrap="word",
                       padx=14, pady=14, font=("Consolas", 10), state="disabled", height=9)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        return text

    @staticmethod
    def _replace(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.configure(state="disabled")

    def reload(self):
        if self.execution:
            return
        self.modules, errors = discover(self.module_root)
        self._filter()
        if errors:
            self._replace(self.logs, "Module discovery warnings:\n" + "\n".join(errors))

    def _filter(self):
        query = self.search.get().lower()
        self.visible = [m for m in self.modules if query in f"{m.name} {m.category} {m.description}".lower()]
        self.library.delete(0, "end")
        for module in self.visible:
            self.library.insert("end", module.name)
        self.count.configure(text=f"{len(self.visible)} of {len(self.modules)} modules")
        if self.selected in self.visible:
            self.library.selection_set(self.visible.index(self.selected))
        elif self.visible and not self.execution:
            self.library.selection_set(0)
            self._select()
        elif not self.execution:
            self.selected = None
            self.name.configure(text="No matching modules")
            self.meta.configure(text="")
            self.description.configure(text="Add a module folder with module.json, then reload the library.")
            for child in self.form.winfo_children():
                child.destroy()
            self.run_button.configure(state="disabled")

    def _select(self, event=None):
        if self.execution:
            return
        indices = self.library.curselection()
        if not indices:
            return
        self.selected = self.visible[indices[0]]
        module = self.selected
        self.name.configure(text=module.name)
        self.meta.configure(text=f"{module.category}  /  v{module.version}  /  {module.timeout}s timeout")
        self.description.configure(text=module.description)
        for child in self.form.winfo_children():
            child.destroy()
        self.controls = {}
        for spec in module.inputs:
            if spec["type"] == "boolean":
                value = tk.BooleanVar(value=spec.get("default", False))
                widget = ttk.Checkbutton(self.form, text=spec["label"], variable=value)
                getter = value.get
            else:
                ttk.Label(self.form, text=spec["label"]).pack(anchor="w", pady=(6, 4))
                if spec.get("multiline"):
                    widget = tk.Text(self.form, height=4, bg=FIELD, fg=TEXT, insertbackground=TEXT,
                                     relief="flat", padx=8, pady=8, font=("Consolas", 10))
                    widget.insert("1.0", str(spec.get("default", "")))
                    getter = lambda w=widget: w.get("1.0", "end-1c")
                else:
                    value = tk.StringVar(value=str(spec.get("default", "")))
                    widget = ttk.Entry(self.form, textvariable=value)
                    getter = value.get
            widget.pack(fill="x", pady=(0, 4))
            self.controls[spec["key"]] = (spec, getter)
        self.run_button.configure(state="normal")

    def _run(self):
        if not self.selected or self.execution:
            return
        try:
            values = {}
            for key, (spec, getter) in self.controls.items():
                value = getter()
                if spec["type"] == "integer":
                    if not value.strip():
                        continue
                    try:
                        value = int(value)
                    except ValueError:
                        raise ValueError(f"{spec['label']} must be an integer") from None
                values[key] = value
            execution = Execution(self.selected, values)
        except ValueError as exc:
            messagebox.showerror("Check inputs", str(exc), parent=self)
            return
        self.execution = execution
        self.record = None
        self.run_button.configure(state="disabled")
        self.reload_button.configure(state="disabled")
        self.library.configure(state="disabled")
        self.search_entry.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.export_button.configure(state="disabled")
        self.status.configure(text=f"Running {self.selected.name}…")
        self._replace(self.results, "Module is running. Results will appear here when it finishes.")
        self._replace(self.logs, "Worker started. Logs are collected at completion.")
        self._replace(self.raw, "")
        threading.Thread(target=lambda: self.events.put(execution.run()), daemon=True).start()

    def _cancel(self):
        if self.execution:
            self.execution.cancel()
            self.status.configure(text="Cancelling…")
            self.cancel_button.configure(state="disabled")

    def _poll(self):
        try:
            record = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.execution = None
            self.record = record
            self.library.configure(state="normal")
            self.search_entry.configure(state="normal")
            self.reload_button.configure(state="normal")
            self.run_button.configure(state="normal" if self.selected else "disabled")
            self.cancel_button.configure(state="disabled")
            self.export_button.configure(state="normal")
            self.status.configure(text=record["status"].replace("_", " ").capitalize())
            result = record.get("result", {})
            lines = [result.get("summary", record.get("error", record["status"]))]
            for item in result.get("findings", []):
                lines.extend(["", f"[{item['severity'].upper()}] {item['title']}", item["description"]])
            if "data" in result:
                lines.extend(["", "DETAILS", json.dumps(result["data"], indent=2, ensure_ascii=False)])
            self._replace(self.results, "\n".join(lines))
            self._replace(self.logs, "\n".join(record["logs"]) or "No log messages.")
            self._replace(self.raw, json.dumps(record, indent=2, ensure_ascii=False))
        self.poll_timer = self.after(100, self._poll)

    def _export(self):
        if not self.record:
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".json", filetypes=[("JSON", "*.json")],
                                          initialfile=f"{self.record['module']['id']}-{self.record['run_id'][:8]}.json")
        if path:
            try:
                Path(path).write_text(json.dumps(self.record, indent=2, ensure_ascii=False), encoding="utf-8")
                self.status.configure(text="Run exported")
            except OSError as exc:
                messagebox.showerror("Export failed", str(exc), parent=self)

    def _close(self):
        self.destroy()

    def destroy(self):
        if self.execution:
            self.execution.cancel()
        if getattr(self, "poll_timer", None):
            self.after_cancel(self.poll_timer)
            self.poll_timer = None
        super().destroy()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
