# Pentest Toolkit — project context and sprint plan

Last updated: 12 October 2026

This document is the handoff context for future contributors and development sessions. It distinguishes the implemented foundation from proposed work. Sprint lengths, estimates and release targets below are planning assumptions, not committed delivery dates.

## Product goal

Build an open-source desktop toolkit for penetration testing. The host application provides the workspace, execution lifecycle and evidence presentation. Independently developed modules provide assessment capabilities and plug into the host without requiring changes to its interface or core code.

### Requirements confirmed by the owner

- Windows is the first supported desktop platform.
- Modularity is the central requirement: future developers must be able to build and plug in their own modules.
- The project is intended to be open source.

### Implementation decisions in the initial foundation

- Python 3.11+ with a Tk desktop interface.
- Standard library only for the host and bundled modules.
- MIT license; current source version is 0.1.0.
- Local module discovery using JSON manifests.
- Module API v1 and JSON run-record schema v1.
- A separate Python worker process for each run.

These are the initial technical choices, not additional product requirements from the owner. Reconsider them through documented proposals when justified; preserve module compatibility where possible.

## Location and entry points

Project root: `C:\Users\Torquato\PentestToolkit`.

The project was moved from the generated Codex workspace into the owner's home directory. Use this root for subsequent development. The source ZIP in the old workspace is an earlier snapshot and will not reflect future changes automatically.

| Path | Responsibility |
| --- | --- |
| `Launch.cmd`, `launch.py` | Windows launcher and desktop entry point |
| `toolkit/app.py` | Module library, generated forms, results, logs and export |
| `toolkit/modules.py` | Manifest discovery and input validation |
| `toolkit/sdk.py` | Public API for module authors |
| `toolkit/runner.py` | Worker lifecycle, timeout, cancellation and run records |
| `toolkit/worker.py` | Import and execute a module; return its JSON response |
| `modules/target_inventory/` | Offline target parsing and normalization |
| `modules/http_headers/` | Single-request HTTP header inspection |
| `docs/MODULES.md` | Module contract and authoring guide |
| `tests/` | Core integration tests and desktop tests |
| `VALIDATION.md` | Recorded verification and environment limitations |
| `CONTRIBUTING.md`, `LICENSE` | Contribution guidance and MIT license |

## Current architecture

```text
Desktop interface
  -> discover modules/*/module.json without importing module code
  -> build input controls from the selected manifest
  -> validate declared input types and required fields
  -> start worker process
       -> import entrypoint
       -> run(context, inputs)
       -> return JSON result and collected logs
  -> display findings, data and logs
  -> export JSON run record
```

A module declares an ID, independent version, API version, category, entrypoint, inputs and timeout. Its entrypoint exposes `run(context, inputs)` and returns a JSON-compatible object with a string `summary`, optional `data` and optional `findings`. The context provides a run ID and collected logging. Read `docs/MODULES.md` before changing this contract.

Run records include the module identity, validated inputs, UTC timestamps, logs and status: `completed`, `failed`, `cancelled` or `timed_out`. Discovery rejects invalid manifests, unsupported API versions, duplicate IDs and entrypoints outside the module directory.

### Implemented

- Searchable module library and manual reload.
- Manifest-generated string, multiline string, integer and boolean controls.
- Background execution with per-run worker separation, cancellation and timeout.
- Findings, structured results, collected logs and JSON export.
- Offline inventory for hostnames, IP addresses, CIDR ranges and HTTP(S) URLs.
- HTTP HEAD inspection with TLS verification and no redirect following.
- Developer documentation and automated checks.

### Validation and known limits

Latest checks on Windows with Python 3.14.7: **27 tests passed with no skips**, including three desktop tests. Matching Tcl/Tk 9.0.4 script libraries were installed inside the project using the official CPython dependency archive. Desktop creation, module execution, search and JSON export were exercised automatically. Manual review at different display sizes/scaling and comprehensive UI failure-state review remain pending. The system Python installation itself was not modified.

- Installed modules execute with the current user's permissions. Worker separation is not a security sandbox.
- Cancellation terminates the worker, but does not yet manage descendant processes.
- Output is checked against a 2 MB limit after collection; this does not bound memory consumption during execution.
- Module dependencies share the application's interpreter. Per-module environments and package-relative imports are not provided.
- Logs and results appear at completion; live streaming is not implemented.
- Run records are exported on demand; durable project workspaces and history are not implemented.
- Inputs are exported verbatim. The API has no credential or secret input type.
- HTTP inspection bypasses environment proxies. Proxy configuration is not implemented.
- Missing HTTP headers are observations for review, not confirmed vulnerabilities.
- No standalone executable, installer or CI configuration has been created. The source repository is now configured at https://github.com/torquyme/penny.

## Sprint planning assumptions

Use outcome-based sprints. A working assumption is two weeks per numbered sprint, with Sprint 0 as a short readiness phase. Capacity, dates and owners are unassigned. Commit to a sprint only after reviewing contributor availability and its dependencies. Avoid expanding the bundled tool catalog before the extension workflow is reliable.

| Sprint | Outcome | Dependencies | Proposed release |
| --- | --- | --- | --- |
| 0 | Verified Windows desktop baseline | Usable Tcl/Tk runtime | 0.1.1 |
| 1 | A contributor can build a module without core changes | Sprint 0 | 0.2.0 |
| 2 | Assessment projects retain scope, evidence and run history | Sprint 1 | 0.3.0 |
| 3 | Reliable execution and per-module dependencies | Sprint 1; integrate with Sprint 2 | 0.4.0 |
| 4 | One existing tool integrated through the public contract | Sprints 2 and 3 | 0.5.0 |
| 5 | Windows distribution ready for contributors and users | Sprints 0–4 | 0.6.0 |

### Sprint 0 — verify the desktop foundation

Tasks:

- Resolve the local Tcl/Tk runtime requirement and document a reproducible Windows setup.
- Run the existing desktop tests without skipping them.
- Review the UI on Windows at common display sizes and scaling settings; fix clipping, scrolling and keyboard navigation issues found.
- Exercise successful runs, invalid inputs, failures, cancellation, timeout and export through the interface.
- Improve launcher diagnostics for missing Python or Tcl/Tk.
- Update `VALIDATION.md` with actual results and remaining limitations.

Acceptance: `python -m tkinter` opens successfully; all 13 existing tests pass without skips in the Windows validation environment; both bundled modules run through the desktop interface against offline or local fixtures; export round-trips to valid JSON; discovery warnings are visible and understandable.

### Sprint 1 — make module development a first-class workflow

Tasks:

- Add a copyable module template and a scaffold command with a unique module ID.
- Add a module validation command that reports manifest and contract errors without launching the UI.
- Add examples for each supported input type and finding severity.
- Add module contract checks that authors can run independently.
- Define supported import/package layout, semantic input validation and compatibility policy.
- Improve module diagnostics so a broken extension can be identified and corrected quickly.

Acceptance: a contributor follows the guide, creates a new module, validates it and sees it after reload without editing `toolkit/`; invalid manifests and malformed results produce actionable errors; both existing modules remain compatible with API v1.

### Sprint 2 — persistent assessment workspaces

Tasks:

- Add create, open and save operations for assessment projects.
- Store target inventory, module identity, input snapshots, results, logs and evidence references.
- Define a versioned storage schema and recovery behavior for interrupted writes.
- Add run-history navigation and export from saved runs.
- Define explicit target-scope rules and a reusable scope-check API for network modules.
- Keep generated assessment data separate from application source and module packages.

Acceptance: closing and reopening the app preserves a project's targets and run history; an interrupted save does not silently corrupt the previous project; evidence can be traced to its originating run; supported network modules check project scope and reject an out-of-scope target before sending a request.

### Sprint 3 — reliable module execution and dependencies

Tasks:

- Add opt-in module dependency declarations and dedicated virtual environments.
- Make dependency installation an explicit action with visible progress and errors.
- Manage worker process trees on Windows, including timeout and cancellation cleanup.
- Bound output buffering during execution and handle large or malformed responses.
- Design streaming logs with explicit protocol versioning and backwards compatibility.
- Define sensitive-input handling and redaction before supporting credentials.

Acceptance: two modules with conflicting dependency versions run independently; cancelling or timing out an adapter terminates its managed descendants; excessive output fails within a documented memory bound; legacy API v1 modules still work; logs remain responsive during long runs; sensitive values do not enter exported records or logs through host-controlled paths.

### Sprint 4 — prove extensibility with an existing tool

Tasks:

- Select one initial integration; Nmap service discovery is a proposed candidate, pending scope selection.
- Implement executable detection, version reporting and setup guidance within the module.
- Execute with structured argument lists and defined target/option validation.
- Parse machine-readable output into inventory, observations and evidence.
- Handle missing executables, malformed output, partial completion and cancellation.
- Add local fixtures and an optional integration check for an installed executable.

Acceptance: the adapter uses the published module contract without tool-specific core code; missing dependencies are explained in the UI; project scope is checked before execution; parsed evidence is retained in run history; fixture tests do not require internet access or the external executable.

### Sprint 5 — Windows distribution and open-source release readiness

Tasks:

- Choose a supported packaging approach that accommodates external modules and their Python workers.
- Build a Windows artifact including the required desktop runtime.
- Define a writable module location and application-data directory outside installed program files.
- Add Windows CI for host tests, module contract checks and packaging smoke checks.
- Document installation, module authoring, troubleshooting, contribution and release procedures.
- Prepare repository metadata and issue templates; obtain the owner's chosen hosting location before publication.

Acceptance: the packaged app starts on a clean Windows environment without a separate Python installation; a newly added external module can execute; both bundled modules and JSON export work; CI produces a reproducible artifact; documentation matches the shipped contract and remaining limitations.

## Definition of done

- The sprint's acceptance criteria are demonstrated with evidence.
- Tests cover meaningful changed behavior and use local fixtures by default.
- Desktop changes receive a Windows UI check, including failure states.
- Documentation reflects the implemented behavior and public API.
- Compatibility changes have an explicit version and migration explanation.
- Runtime limitations are recorded; process separation is never described as sandboxing.
- Release notes distinguish implemented capabilities from planned work.

## Deferred backlog and decisions

Deferred: a module registry and provenance, signing, automatic updates, advanced orchestration, additional desktop platforms, implementation of specialist catalog modules and richer report formats.

Decisions still needed: project branding; repository owner and hosting location; sprint owners and capacity; persistence format; supported Python versions; dependency-installation policy; first external tool; packaging and distribution approach. None of these decisions should block Sprint 0.

## Next session checklist

1. Work from `C:\Users\Torquato\PentestToolkit` and read this document, `README.md`, `VALIDATION.md` and `docs/MODULES.md`.
2. Check for changes since this handoff; do not assume the source tree is unchanged.
3. Run `python -m tkinter` to establish desktop readiness.
4. Run `python -m unittest discover -s tests -v` and record passes, failures and skips separately.
5. Start with Sprint 0; update this document as decisions and milestones are completed.

## Module catalog and delivery scope

The proposed assessment catalog is defined in [MODULE_CATALOG.md](MODULE_CATALOG.md): 61 modules across 16 suites, with shared host capabilities maintained separately. Target inventory and HTTP headers are implemented; DNS analysis now includes the implemented system-resolver address profile. Other modules and advanced DNS-record/configuration profiles remain planned.

The initial general-purpose module release targets ten P1 entries: target inventory, DNS analysis, port/service discovery, TLS assessment, HTTP headers, HTTP request inspection, web surface mapping, API schema inventory, infrastructure service configuration and external results import. This is a delivery sequence across module sprints, not a commitment to ship ten modules in one sprint.

Use Sprint 1 to prove the authoring contract with a small DNS or API-schema pilot. Sprint 2 establishes common asset/evidence storage and scope; Sprint 3 establishes execution, dependencies and credentials. Sprint 4 demonstrates port/service discovery through an external adapter. Sprint 5 packages a tested subset. Remaining P1 and P2 modules follow in dedicated module sprints based on capacity; P3 modules remain specialist/community roadmap work.

Before implementation, define each module's test profiles, input/result contract, dependencies, Windows execution path and acceptance criteria. Interactive and remote/device workflows require new host capabilities and must not be presented as already supported by API v1. Consult the catalog during subsequent planning and update both documents when scope changes.


## Development progress — first increment

- Sprint 0 **in progress**: local Tcl/Tk startup issue resolved; desktop tests run without skips; launcher explains missing Python/runtime; pending manual layout/scaling and full failure-state review.
- Sprint 1 **in progress**: `toolkit.dev` provides scaffold, static validation, list and headless execution commands; the offline scaffold is discoverable and runnable without core edits; developer workflow and contract tests added; DNS address analysis is the pilot module.
- Validation: 27 tests pass, covering the original core, DNS behavior, developer workflow and desktop execution/export. Network tests use localhost or mocked resolver responses.
- DNS limitations: system-resolver A/AAAA-style address results and optional reverse lookup only; hosts-file/cache answers possible; no record TTL, authoritative answers, MX/TXT/NS query support or custom resolver selection yet.
- Runtime limitations from the original architecture (credential redaction, durable projects, output memory bounds, descendant-process management and interactive extension views) remain unchanged.
- Next module candidates: API schema inventory for an offline module, and TLS assessment after a bounded network profile is specified. Continue the host milestones needed by these modules instead of marking the full catalog complete.

For current setup instructions, use the project-local runtime check in README.md; the standalone `python -m tkinter` command does not automatically select `.runtime/`.

## Git repository setup

Repository: https://github.com/torquyme/penny. Default development branch: main. The supplied SSH origin is retained in configuration; a repository-local HTTPS rewrite uses the existing GitHub CLI login because SSH authentication is unavailable. Runtime libraries, caches and reports are ignored. No Windows ownership changes were made.
