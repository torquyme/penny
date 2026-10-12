# Validation — first development increment

Updated: 12 October 2026. Environment: Windows x64, Python 3.14.7.

## Current checks

`python -m unittest discover -s tests -v`: **27 tests passed, no skips** in the staged development tree. Deployment verification in the home-directory project is recorded below after synchronization.

- 11 original core checks: discovery, manifest errors, duplicate IDs, path containment, inputs, Unicode/stdout results, failures, timeouts, cancellation, inventory normalization and loopback HTTP behavior.
- 7 DNS checks: mocked forward/reverse responses, deduplication, literal addresses, invalid inputs, partial failure, bounds/IDNA and localhost worker execution.
- 6 developer-workflow checks: scaffold/discover/validate/execute, overwrite refusal, metadata-only validation, invalid source/signatures, JSON-input CLI export and failure exit status.
- 3 desktop checks: inventory execution/export, search recovery and DNS generated-form/worker execution.

The original missing Tcl/Tk scripts were supplied locally using Python's official `cpython-bin-deps` archive, tag `tcltk-9.0.4.0`. The helper verifies SHA256 `ff04215b99a16cd7c78951d02d8d1ec1dbd01d35db96389a784125dde024d5f7` and preserves the licenses. Existing installed DLLs are used; system Python is unchanged.

## Remaining verification

Automated desktop checks do not establish visual quality at every Windows display size or scaling setting. Manual layout, accessibility and comprehensive UI failure-state review remain pending. No public network scan or external DNS domain was required for tests. Additional DNS record types are not implemented.

No signed executable, installer or CI deployment was created. The source repository is now configured at https://github.com/torquyme/penny. Worker isolation still has the limitations described in README.md.

## Historical baseline

Before this increment, 11 core tests passed and two desktop tests were skipped due to missing Tcl/Tk scripts. The current results supersede that desktop blocker for the configured project on this machine.

## Home-directory deployment verification

The changes were applied to C:\Users\Torquato\PentestToolkit. Static validation passed for dns_analysis, http_headers and target_inventory. All 27 tests passed without skips when run outside the workspace sandbox against the home-directory project. Restricted sandbox runs could not read its locally installed runtime and skipped desktop tests; the final run verified desktop execution with the normal user environment.
