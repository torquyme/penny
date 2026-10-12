"""System-resolver profile. This is not an authoritative DNS-record query engine."""
import ipaddress
import re
import socket
from datetime import datetime, timezone

from toolkit.sdk import finding


def normalize(value):
    try:
        return str(ipaddress.ip_address(value)), True
    except ValueError:
        name = value.rstrip(".").encode("idna").decode("ascii").lower()
        labels = name.split(".")
        if len(name) > 253 or not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels):
            raise ValueError("Expected a hostname or IP address, without URL, port or path")
        if re.fullmatch(r"[0-9.]+", name):
            raise ValueError("Invalid IP address")
        return name, False


def run(context, inputs):
    raw = [line.strip() for line in inputs["hosts"].splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not raw:
        raise ValueError("Enter at least one hostname or IP address")
    if len(raw) > 20:
        raise ValueError("At most 20 input entries are supported per run")
    rows, rejected, observations, seen = [], [], [], set()
    for value in raw:
        try:
            name, literal = normalize(value)
        except (ValueError, UnicodeError) as exc:
            rejected.append({"input": value, "error": str(exc)})
            continue
        if name in seen:
            continue
        seen.add(name)
        context.log(f"Resolving {name}" if not literal else f"Recording literal address {name}")
        row = {"host": name, "observed_at": datetime.now(timezone.utc).isoformat(),
               "source": "literal" if literal else "system_resolver", "status": "resolved", "addresses": []}
        try:
            if literal:
                addresses = {name}
            else:
                addresses = {item[4][0] for item in socket.getaddrinfo(name, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
                             if item[0] in {socket.AF_INET, socket.AF_INET6}}
            if not addresses:
                raise ValueError("System resolver returned no IPv4 or IPv6 addresses")
            for address in sorted(addresses):
                entry = {"address": address, "family": "IPv4" if ipaddress.ip_address(address).version == 4 else "IPv6"}
                if inputs.get("reverse", False):
                    try:
                        entry["reverse_name"] = socket.gethostbyaddr(address)[0]
                    except OSError as exc:
                        entry["reverse_error"] = str(exc)
                row["addresses"].append(entry)
        except (OSError, ValueError) as exc:
            row.update(status="unresolved", error=str(exc))
            observations.append(finding("Name could not be resolved", f"{name}: {exc}. This is a resolver observation, not a vulnerability."))
        rows.append(row)
    for entry in rejected:
        observations.append(finding("Invalid lookup input", f"{entry['input']}: {entry['error']}"))
    count = sum(row["status"] == "resolved" for row in rows)
    context.log(f"Resolved {count}/{len(rows)} unique entries; rejected {len(rejected)} inputs")
    return {"summary": f"{count}/{len(rows)} entries resolved",
            "data": {"resolver": "operating_system", "hosts": rows, "rejected": rejected,
                     "limitations": "System resolver may use hosts files/cache. No TTL, authoritative answers, MX, TXT, NS or custom resolver selection. Overall worker timeout is 30 seconds."},
            "findings": observations}
