"""Use optional project-local Tcl/Tk scripts without modifying Python installation."""
import os
from pathlib import Path


def configure_tk() -> None:
    try:
        import _tkinter
    except ImportError:
        return
    root = Path(__file__).resolve().parent.parent / ".runtime"
    for variable, version, name in (("TCL_LIBRARY", _tkinter.TCL_VERSION, "tcl"),
                                    ("TK_LIBRARY", _tkinter.TK_VERSION, "tk")):
        path = root / f"{name}{version}"
        script = "init.tcl" if name == "tcl" else "tk.tcl"
        if (path / script).is_file():
            os.environ.setdefault(variable, str(path))
