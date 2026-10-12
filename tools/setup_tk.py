"""Install matching Tcl/Tk 9.0.4 scripts locally from CPython's dependency archive."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import tempfile
from urllib.request import urlopen
import zipfile

URL = "https://github.com/python/cpython-bin-deps/archive/refs/tags/tcltk-9.0.4.0.zip"
SHA256 = "ff04215b99a16cd7c78951d02d8d1ec1dbd01d35db96389a784125dde024d5f7"
PREFIX = "cpython-bin-deps-tcltk-9.0.4.0/amd64/"
ROOT = Path(__file__).resolve().parent.parent


def install(archive: bytes, root: Path) -> None:
    if hashlib.sha256(archive).hexdigest() != SHA256:
        raise ValueError("Archive SHA256 differs from the pinned CPython dependency archive")
    destination = root / ".runtime"
    if destination.exists():
        raise ValueError(f"Runtime directory already exists: {destination}")
    with tempfile.TemporaryDirectory(prefix=".tk-setup-", dir=root) as temporary:
        stage = Path(temporary) / "runtime"
        stage.mkdir()
        with zipfile.ZipFile(io.BytesIO(archive)) as outer:
            for name in ("tcl", "tk"):
                payload = outer.read(PREFIX + f"lib/lib{name}9.0.4.zip")
                with zipfile.ZipFile(io.BytesIO(payload)) as inner:
                    for item in inner.infolist():
                        if item.is_dir():
                            continue
                        relative = Path(item.filename)
                        if not relative.parts or relative.parts[0] != f"{name}_library":
                            raise ValueError("Unexpected runtime archive layout")
                        target = (stage / f"{name}9.0" / Path(*relative.parts[1:])).resolve()
                        if not target.is_relative_to(stage.resolve()):
                            raise ValueError("Archive path escapes runtime directory")
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(inner.read(item))
                (stage / f"{name}-LICENSE.txt").write_bytes(outer.read(PREFIX + f"{name}license.terms"))
        (stage / "SOURCE.json").write_text(json.dumps({"source": URL, "sha256": SHA256,
                    "version": "9.0.4", "contents": "Tcl/Tk scripts and licenses only; no replacement DLLs"}, indent=2), encoding="utf-8")
        stage.rename(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use an already downloaded archive instead of the network")
    args = parser.parse_args()
    import _tkinter
    if os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}:
        parser.error("This helper supports Windows x64 only")
    if (_tkinter.TCL_VERSION, _tkinter.TK_VERSION) != ("9.0", "9.0"):
        parser.error("This helper requires the existing Tcl/Tk 9.0 DLLs; otherwise repair Python's Tcl/Tk installation")
    try:
        if args.archive:
            archive = args.archive.read_bytes()
        else:
            print(f"Downloading {URL}")
            with urlopen(URL, timeout=30) as response:
                archive = response.read(80_000_001)
            if len(archive) > 80_000_000:
                raise ValueError("Archive exceeds size limit")
        install(archive, ROOT)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"Setup failed: {exc}\n")
    print(f"Project-local runtime installed: {ROOT / '.runtime'}")


if __name__ == "__main__":
    main()
