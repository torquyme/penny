# Contributing

Keep module logic under `modules/<id>/`; keep discovery, execution, UI and protocol logic under `toolkit/`.

For a module contribution:

1. Add a unique manifest and entrypoint following `docs/MODULES.md`.
2. Describe network activity and required dependencies clearly.
3. Return reproducible evidence and avoid claiming vulnerabilities from weak signals.
4. Add tests using local servers or fixtures. Default tests must not require internet access.
5. Run `python -m unittest discover -s tests -v`.

For host changes, preserve API v1 or introduce an explicit new version. Keep Tk operations on the main thread and tool execution in workers. Do not introduce shell command construction from user inputs.

Contributions are licensed under the project's MIT license. The source repository is https://github.com/torquyme/penny. Submit changes through pull requests.
