# Pentest Toolkit — module catalog

Updated: 12 October 2026. Status: proposed product catalog, not a list of implemented features.

## Scope and design

The goal is broad coverage of common penetration-testing engagements through independently maintained task modules. Organize modules into suites for navigation, but keep each module separately versioned and testable. A suite is a grouping, not a monolithic plugin.

A module represents a task and a result contract. An existing tool can be one implementation behind that contract. For example, service discovery may use an external scanner while returning the same normalized service records. Do not create separate overlapping modules solely because different tools perform the same task.

`target_inventory` and `http_headers` are implemented. `dns_analysis` now has an implemented system-resolver address profile; advanced DNS-record/configuration profiles remain planned. Every other catalog entry is proposed. Broad coverage requires automation, imported evidence and guided manual testing; it does not imply complete automatic detection of all vulnerabilities.

### Priority and execution legend

- **P1:** initial general-purpose module release; ten selected modules.
- **P2:** broaden common web, internal-network and infrastructure assessments.
- **P3:** specialist capabilities and later community contributions.
- **N:** local Windows execution is a proposed implementation path.
- **E:** an external executable or runtime is expected.
- **R:** a connected test system, remote collector or emulator/device is required for some functionality.
- **H:** compatible hardware, drivers or capture privileges may be required.
- **I:** accepts existing files or evidence; not all analysis requires a live target.
- **G:** guided manual workflow or interactive session; needs host capabilities beyond current finite-run API v1.

These execution labels describe intended designs, not verified tool compatibility. Windows-first refers to the desktop host. A module may target Linux, cloud services or mobile devices without running all its collectors on Windows. E/R/H/G features need runtime work before they can be delivered.

## Shared host capabilities — not individual assessment modules

| Capability | Purpose | Current state |
| --- | --- | --- |
| Projects, scope and target identity | Define engagements, allowed targets, exclusions and reusable inventory | Per-run inputs exist; durable projects and scope enforcement are planned |
| Module lifecycle and dependencies | Discovery, versions, installation, validation and per-module environments | Local discovery/API version checks exist; installation/environments are planned |
| Execution broker | Cancellation, timeouts, concurrency, output limits and descendant-process cleanup | Single-run workers exist; stronger resource/process management is planned |
| Network/session services | Scope-aware requests, rate limits, proxy configuration, authentication sessions and remote transports | Individual modules make requests; shared services are planned |
| Credential storage and redaction | Protect credentials across inputs, logs, evidence and exports | Not implemented; do not use ordinary API v1 inputs for secrets |
| Evidence and findings store | Normalized assets, evidence provenance, finding review and run history | JSON records/results exist; durable store and review workflow are planned |
| Extension presentation | Standard tables, artifacts, forms and optional interactive views | Basic generated forms and text/JSON views exist; richer views are planned |

## 1. Reconnaissance and asset discovery

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `target_inventory` | Normalize IPs, networks, hostnames and URLs; return inventory and rejected inputs. **Implemented.** | P1 | N |
| `dns_analysis` | System-resolver IPv4/IPv6 and optional reverse lookup with timestamped evidence are implemented. MX/TXT/NS, custom DNS queries and configuration review remain planned. | P1 | N |
| `public_asset_discovery` | Correlate supplied domains with public certificate and asset data; return candidate assets with source provenance, pending scope review. | P2 | N/I |
| `technology_fingerprint` | Infer web/server components from observable evidence; return confidence-rated fingerprints rather than definitive version claims. | P2 | N |
| `exposure_review` | Analyze provided public documents, repository URLs and exposure evidence for unintended disclosures; return evidence references. | P2 | N/I |

## 2. Network and transport

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `host_discovery` | Identify reachable scoped hosts using selected discovery methods; return observations and method limitations. | P2 | N/E |
| `port_service_discovery` | Enumerate selected ports and identify services; return host/port/protocol records and scanner evidence. | P1 | E |
| `tls_assessment` | Review certificate validity, names, chains and negotiated transport properties; return certificate and TLS observations. | P1 | N/E |
| `segmentation_validation` | Compare observed permitted/blocked connections with a supplied reachability policy across test vantage points. | P2 | N/R |
| `packet_capture_analysis` | Analyze supplied captures for protocol inventory, plaintext exposure and communication patterns. | P2 | E/I/H |
| `email_security` | Review mail transport and domain authentication configuration, including SPF, DKIM selectors supplied by the tester and DMARC. | P2 | N |

## 3. Web applications

The categories below are informed by the [OWASP WSTG v4.2 test areas](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/), including configuration, authentication, authorization, sessions, input validation, cryptography, business logic and client-side behavior. The module boundaries are project design choices.

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `http_headers` | Inspect a single HEAD response and review header observations. **Implemented.** | P1 | N |
| `http_requests` | Compose, send and replay scoped HTTP requests; compare responses and retain redacted request/response evidence. | P1 | N/G |
| `web_surface_mapping` | Bounded crawling and route/form/link extraction; return an endpoint and parameter inventory. | P1 | N/E |
| `web_configuration` | Review methods, CORS, cookies, caching, error disclosure and deployment exposures; retain reproducible observations. | P2 | N |
| `web_input_validation` | Organize bounded injection, traversal, upload and server-side request handling checks; distinguish suspected from manually confirmed findings. | P2 | N/E/G |
| `web_client_security` | Review browser-side behavior, framing, DOM risks, storage and script dependencies using browser evidence. | P2 | E/G/I |
| `business_logic_testing` | Model workflow invariants, state transitions, multi-step abuse cases and race-condition review; retain tester conclusions. | P2 | G |

## 4. APIs and service interfaces

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `api_schema_inventory` | Import OpenAPI descriptions and API collections; return operations, parameters and declared authentication requirements. | P1 | N/I |
| `api_authorization` | Compare access across tester-provided accounts, object ownership and roles; return permission mismatches with paired evidence. | P2 | N/G |
| `api_validation` | Review schema enforcement, resource limits, error disclosure, version exposure and response data filtering. | P2 | N/G |
| `graphql_rpc_testing` | Inventory and review GraphQL, gRPC and WebSocket interfaces with protocol-specific test profiles. | P3 | N/E/G |

## 5. Authentication, identity and enterprise directories

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `authentication_session` | Review login/reset flows, MFA behavior, session lifetime, logout and account policy with test accounts. | P2 | N/G |
| `token_federation_review` | Inspect JWT, OAuth/OIDC and SAML configurations and supplied tokens; return validation and trust-policy observations. | P2 | N/I/G |
| `directory_inventory` | Collect scoped Active Directory/LDAP structure, users, groups, trusts and policy metadata using a supplied read account. | P2 | E/R/I |
| `directory_permissions` | Analyze directory permissions and relationship data for excessive rights and potential privilege paths. | P2 | E/I |
| `directory_certificate_review` | Review enterprise certificate services templates, enrollment permissions and configuration evidence. | P3 | E/R/I |

## 6. Hosts and infrastructure services

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `service_configuration` | Review SSH, SMB, RDP, FTP, SNMP and related services through separate protocol profiles; return configuration evidence. | P1 | N/E |
| `windows_host_review` | Analyze supplied or collected Windows service, privilege, patch, file-permission and security-policy evidence. | P2 | E/R/I |
| `linux_host_review` | Analyze Linux service, privilege, patch, file-permission and security-policy evidence via a collector or imports. | P2 | R/I |
| `network_device_review` | Review firewall, VPN, router and switch configuration exports and management-plane exposure. | P2 | N/I/R |
| `virtualization_review` | Review hypervisor/management configuration and permissions through supported read APIs or configuration exports. | P3 | N/R/I |

## 7. Databases and data services

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `sql_database_review` | Review SQL Server, PostgreSQL and MySQL transport, roles, grants and configuration through provider profiles. | P2 | N/E/R |
| `nosql_cache_review` | Review MongoDB, Redis and search/data-store authentication, transport and exposed administration configuration. | P2 | N/E/R |
| `message_broker_review` | Review Kafka, RabbitMQ and similar brokers for transport, authentication and topic/queue permissions. | P3 | N/E/R |

## 8. Cloud and SaaS

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `aws_configuration` | Read AWS resource and IAM configuration with supplied least-privilege access; return exposure and permission observations. | P2 | N/E/I |
| `azure_entra_configuration` | Review Azure resources and Entra identity/access configuration through supported APIs or exported evidence. | P2 | N/E/I |
| `gcp_configuration` | Review GCP resource exposure, IAM bindings and service-account policy through supported APIs or exports. | P3 | N/E/I |
| `saas_configuration` | Provider-specific review of tenant access, sharing, federation and administrative configuration. | P3 | N/E/I |

## 9. Containers and orchestration

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `container_image_review` | Analyze image metadata, dependencies, embedded configuration and supply-chain evidence. | P2 | E/I |
| `container_runtime_review` | Review daemon/runtime exposure, mounts, capabilities and privilege configuration from supplied runtime evidence. | P2 | R/I |
| `kubernetes_review` | Review cluster RBAC, workloads, exposure, admission and network policies using scoped read access or manifests. | P2 | N/E/I |

## 10. Source code and software supply chain

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `source_code_review` | Run language-specific static checks and manual review profiles; return file/line evidence and review state. | P2 | E/I |
| `dependency_sbom_review` | Import dependency inventories/SBOMs and correlate advisories with version and applicability evidence. | P2 | N/E/I |
| `secret_exposure_review` | Analyze supplied files/repositories for exposed secrets; redact values and retain minimal evidence. | P2 | E/I |
| `iac_pipeline_review` | Review infrastructure-as-code and CI/CD configuration for permissions, trust boundaries and deployment exposure. | P2 | E/I |

## 11. Mobile applications

Mobile coverage is informed by [OWASP MASTG](https://mas.owasp.org/MASTG/). Artifact analysis and device testing have different execution requirements.

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `android_static_review` | Analyze APK/manifest/signature, permissions, code and embedded configuration; return artifact evidence. | P3 | E/I |
| `android_runtime_review` | Review storage, networking, platform interactions and authentication on a connected test device/emulator. | P3 | E/R/G |
| `ios_application_review` | Analyze supplied iOS artifacts and import/runtime evidence; device workflows may need a macOS test host. | P3 | E/R/I/G |

## 12. Desktop applications

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `desktop_application_review` | Review installation/update behavior, local data, IPC, permissions and trust boundaries in Windows applications. | P3 | N/E/G/I |
| `binary_artifact_review` | Inspect signatures, imports, hardening properties, strings and supplied binary-analysis evidence. | P3 | E/I/G |

## 13. Wireless and local radio

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `wifi_configuration_review` | Review WLAN authentication/encryption, access-point inventory and provided captures or configuration exports. | P3 | E/H/I |
| `bluetooth_ble_review` | Inventory services and review pairing/access characteristics on test devices with compatible adapters. | P3 | E/H/G |
| `wireless_segmentation` | Verify guest/client isolation and expected reachability from connected wireless test vantage points. | P3 | N/R/H |

## 14. IoT and industrial environments

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `iot_firmware_review` | Inspect supplied firmware/configuration for services, dependencies, permissions and embedded exposure evidence. | P3 | E/I |
| `ot_protocol_review` | Analyze industrial protocol captures/configuration and asset inventory; passive evidence is the initial profile. | P3 | E/I/H |

## 15. Vulnerability validation and control assessment

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `vulnerability_validation` | Run individually selected verification profiles or guide manual confirmation; record prerequisites, observed impact and cleanup notes. | P2 | N/E/G |
| `control_validation` | Correlate defined test actions with supplied telemetry to review prevention/detection coverage; no persistent agent is implied. | P3 | R/I/G |

## 16. Imports, reporting and retesting

| Module ID | Capability and expected output | Priority | Execution |
| --- | --- | --- | --- |
| `results_import` | Import external scanner/tool results into normalized assets, findings and evidence, retaining source attribution. | P1 | N/I |
| `report_generation` | Generate assessment deliverables from reviewed findings, scope, limitations and remediation guidance. | P2 | N/I |
| `retest_comparison` | Compare runs and evidence, track remediation status and highlight changed exposure without equating absence with a confirmed fix. | P2 | N/I |

## Initial module release — ten modules

Deliver these after the required host services are ready, rather than assigning ten implementations to a single sprint:

1. `target_inventory` — existing offline starting point.
2. `dns_analysis` — system-resolver address profile implemented; advanced record profiles planned.
3. `port_service_discovery` — establish network/service exposure.
4. `tls_assessment` — assess transport configuration.
5. `http_headers` — existing basic web inspection.
6. `http_requests` — reusable manual HTTP inspection and replay.
7. `web_surface_mapping` — identify routes and inputs.
8. `api_schema_inventory` — make API testing accessible from supplied specifications.
9. `service_configuration` — review common infrastructure services.
10. `results_import` — gain coverage from existing tools before rebuilding their engines.

Dependencies: scope and persistence for network workflows; secret/session handling before authenticated requests; process-tree management and dependency environments before external adapters; an interactive extension contract before advanced request/session views.

## Engagement coverage matrix

| Engagement | Primary suites | What still requires judgment or environment access |
| --- | --- | --- |
| External infrastructure | Reconnaissance; network; infrastructure; validation; reporting | Exposure applicability, reachability and vulnerability confirmation |
| Internal network / Active Directory | Network; identity; hosts; databases; validation | Authenticated access, multiple vantage points and privilege-path review |
| Web application / API | Web; API; authentication; source when available | Business logic, role/ownership checks and manual verification |
| Cloud / SaaS | Cloud; identity; containers; source/IaC | Provider/tenant permissions and business context |
| Containerized platform | Containers; cloud; network; source | Cluster/runtime evidence and workload context |
| Mobile / desktop software | Mobile or desktop; web/API; binary/source | Test devices, runtime tooling and interactive analysis |
| Wireless | Wireless; network; identity | Compatible adapters, drivers, privileges and test vantage points |
| IoT / OT | Firmware/protocol; network; binary; infrastructure | Device-specific expertise and representative captures/labs |
| Code / supply chain | Source; dependencies; secrets; pipelines | Language-specific review and advisory applicability |
| Retest / control assessment | Comparison; validation; telemetry; reports | Reliable baselines and interpretation of missing evidence |

Physical-access and human/social-engineering engagements can use the evidence/reporting workflow, but need a separate future product decision for specialized modules. Deep exploit development, persistent implants and availability/load testing are not planned capabilities in this catalog. This is a scope choice for the proposed release, not a claim that those domains do not exist.

## Module specification required before implementation

For each proposed module, create a short design issue defining:

- Stable module ID, suite, maintainer and priority.
- Exact test profiles and explicit exclusions.
- Accepted asset/input types, semantic constraints and credential references.
- Evidence/result schemas, finding confidence and manual review states.
- Execution method, dependencies, Windows compatibility and optional collector requirements.
- Network behavior, scope checks, rate/concurrency limits and cancellation behavior.
- Local fixtures, acceptance criteria, licensing and supported tool versions.

Provider/protocol profiles may later become separate plugins when dependencies, maintainers or release cycles justify the split. Keep shared data contracts stable across those implementations.

## Relationship to the sprint plan

- **Sprint 0:** validate the existing desktop and two implemented modules.
- **Sprint 1:** develop the template, validator and contract tests using `dns_analysis` or `api_schema_inventory` as a small proposed pilot.
- **Sprint 2:** establish scope, storage and shared asset/evidence contracts needed by the catalog.
- **Sprint 3:** support dependencies, process cleanup, streaming and credentials; design interactive extensions explicitly.
- **Sprint 4:** prove the external adapter contract through `port_service_discovery`; Nmap remains a candidate, not a selected dependency.
- **Sprint 5:** package the host and a verified module subset. Do not claim the complete catalog is shipped.
- **Subsequent module sprints:** complete remaining P1 entries, then select P2 suites based on real engagements and contributor capacity. P3 remains an extensibility roadmap.

## Reference frameworks

This catalog is an original architecture proposal informed by the following sources; it is not a certified mapping or a completeness claim:

- [NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final): technical assessment planning, tests, findings and mitigation context.
- [OWASP WSTG v4.2](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/): web security testing categories.
- [OWASP MASTG](https://mas.owasp.org/MASTG/): mobile security testing coverage.
- [MITRE ATT&CK Enterprise](https://attack.mitre.org/matrices/enterprise/): threat-technique context when designing identity, infrastructure and control-validation profiles. ATT&CK is not a penetration-test checklist.

Future specifications should map individual test profiles to applicable versioned references, with applicability and coverage gaps recorded explicitly.
