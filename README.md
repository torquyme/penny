# Pentest Toolkit

Repository: [torquyme/penny](https://github.com/torquyme/penny)

A Windows-first desktop workspace for penetration testing, built around independently developed modules. This is a working foundation, version 0.1.0, with an MIT license.

## Run on Windows

Install Python 3.11 or newer with Tcl/Tk support, then double-click `Launch.cmd`, or run from this folder:

```powershell
python launch.py
```

No third-party Python packages are needed. The application uses Python's native Tk desktop interface. Source execution is supported; a standalone executable and installer are future work.

To check desktop support, run `python -m tkinter`; it should open a demonstration window. If Python reports a missing `init.tcl`, repair or install Python with the Tcl/Tk component enabled. Importing `tkinter` alone does not confirm that its runtime files are present.

## Included

- Searchable module library and reloadable discovery
- Manifest-generated input controls
- Worker process per run, with cancellation and timeouts
- Findings, structured data, logs, and JSON run export
- DNS address analysis: system-resolver IPv4/IPv6 lookup and optional reverse lookup
- Offline target inventory: IP addresses, CIDR ranges, hostnames, HTTP(S) URLs
- HTTP header inspection: one HEAD request, verified TLS, no redirect following

Run the target inventory immediately with its example inputs. HTTP inspection sends a request to the entered target. Missing headers are observations for manual review, not proof of a vulnerability. The HTTP module bypasses environment proxies; proxy configuration is future work.

## Add a module

Create a new directory under `modules/` containing `module.json` and `main.py`. Click **Reload modules**. The core app needs no edits. Copy an included module or follow [the module API guide](docs/MODULES.md).

```text
Desktop UI -> manifest discovery -> input validation -> worker process
                                                       -> module.run(context, inputs)
Desktop UI <- run record <- JSON response <-------------+
```

Each module has an API version, independent version number, category, declared inputs and execution timeout. Invalid modules are skipped with a discovery warning. Duplicate IDs are rejected. Discovery reads metadata without importing extension code.

**Trust model:** installed modules are executable Python code with the current user's permissions. Process separation contains ordinary crashes and enables cancellation; it is not an operating-system security sandbox. Review third-party modules before installing them. The core kills the worker on cancellation; module authors must manage any child processes they launch. The 2 MB response check happens after process output is collected, so it is not a memory quota.

## Development

```powershell
python -m unittest discover -s tests -v
```

Tests exercise discovery, input validation, worker failures, timeout and cancellation, and HTTP inspection against a local server. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution boundaries.

## Next milestones

1. Durable project workspaces, target scope and run history
2. Per-module virtual environments and dependency declarations
3. Wrappers for existing command-line tools, with managed process trees
4. Standalone Windows packaging and CI
5. Versioned distribution registry and module provenance

The current API handles finite runs and JSON results. Streaming output, inter-module orchestration, credentials and dependency installation are intentionally future API work.


## First development increment

Three assessment modules are now available: target inventory, HTTP headers and DNS address analysis. The DNS module uses the operating system resolver and may include hosts-file/cache answers; MX/TXT/NS queries and DNS configuration checks are future profiles. See [DNS module details](docs/DNS.md).

Developer commands, run from the project root:

```powershell
python -m toolkit.dev list
python -m toolkit.dev validate
python -m toolkit.dev new my_module --name "My module"
python -m toolkit.dev run my_module
python -m toolkit.dev run dns_analysis --output dns-run.json
```

Use `--inputs inputs.json` on `run` to provide an input object without shell quoting. All commands accept `--root` for an alternate module library. Static validation checks manifests, source syntax and the entrypoint signature; it does not import module code or certify its behavior. `run` executes the module and validates its result through the normal worker. See [the contributor workflow](docs/DEVELOPER_WORKFLOW.md).

### Project-local desktop runtime

For Windows x64 Python using Tcl/Tk 9.0 DLLs but missing their script libraries, an optional helper installs matching Tcl/Tk 9.0.4 scripts inside `.runtime/`:

```powershell
python tools/setup_tk.py
```

This is an explicit download from Python's official dependency repository with a pinned SHA256. It preserves the upstream licenses and does not replace DLLs or modify the Python installation. Tcl/Tk is third-party runtime content under its own licenses, separate from this project's MIT source. Use `--archive path-to-archive.zip` for an offline copy. For other Python/Tcl versions, repair Python's Tcl/Tk component instead. No network download occurs at app startup.

The runtime has been set up locally for this project. `Launch.cmd` and the desktop tests select it automatically. The unrelated command `python -m tkinter` still tests the system installation; it does not load this project's runtime helper. To check the project's configuration:

```powershell
python -c "from toolkit.runtime import configure_tk; configure_tk(); import tkinter; w=tkinter.Tk(); w.update(); w.destroy(); print('Desktop ready')"
```
