# DNS address analysis — 0.1.0

Module ID: `dns_analysis`. API: v1. Category: Discovery.

This first profile resolves hostnames to IPv4/IPv6 address observations using the operating system resolver, and optionally obtains reverse names. It also accepts literal IP addresses without forward lookup. It does not issue raw DNS protocol requests or select an authoritative server; results may come from DNS, hosts files, resolver cache or operating-system name services.

## Inputs

- `hosts`: required multiline string; one hostname or IP per line, up to 20 nonempty/noncomment lines. Blank lines and lines beginning with `#` are ignored.
- `reverse`: optional boolean, default false. Performs additional reverse lookups for each unique returned address when enabled.

Hostnames are normalized to lowercase ASCII/IDNA and deduplicated after normalization. URLs, ports, paths, malformed IP addresses and invalid hostname labels are rejected with an explanation. The default is `localhost`, so the initial run does not require an external target.

## Output

`data.hosts` contains normalized hostnames, observation timestamps, result source, resolution status and addresses labeled IPv4/IPv6. Optional reverse results or errors appear with each address. Invalid inputs appear in `data.rejected`; lookup failures become informational findings rather than vulnerability claims. A failed reverse lookup does not discard valid forward evidence.

The overall worker timeout is 30 seconds; operating-system resolver calls do not have a separate Python-level timeout. If the worker times out, partial module results are not retained. The host's cancellation terminates the worker.

## Tests and limitations

Tests use mocked resolver responses and `localhost`. No external domain is required. IPv4/IPv6 resolution, literals, deduplication, IDNA, rejection, reverse errors, partial failures, limits and the worker contract are covered.

MX, TXT, NS, SOA, CAA, explicit CNAME chains, TTLs, DNSSEC, authoritative answers, custom resolver selection and DNS configuration findings remain planned profiles. Forward results alone are not proof that a returned address belongs inside an engagement's scope.
