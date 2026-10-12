import ipaddress
import re
from urllib.parse import urlsplit

from toolkit.sdk import finding


def run(context, inputs):
    targets, rejected, seen = [], [], set()
    for line in inputs["targets"].splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        try:
            if "://" in value:
                parsed = urlsplit(value)
                if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError("Expected an HTTP(S) URL without credentials")
                target = {"type": "url", "value": value, "host": parsed.hostname,
                          "port": parsed.port or (443 if parsed.scheme == "https" else 80)}
            elif "/" in value:
                network = ipaddress.ip_network(value, strict=False)
                target = {"type": "network", "value": str(network), "addresses": network.num_addresses}
            else:
                try:
                    address = ipaddress.ip_address(value)
                    target = {"type": "ip", "value": str(address)}
                except ValueError:
                    hostname = value.rstrip(".").encode("idna").decode("ascii").lower()
                    if len(hostname) > 253 or not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part) for part in hostname.split(".")):
                        raise ValueError("Invalid hostname")
                    if re.fullmatch(r"[0-9.]+", hostname):
                        raise ValueError("Invalid IP address")
                    target = {"type": "hostname", "value": hostname}
            if target["value"] not in seen:
                seen.add(target["value"])
                targets.append(target)
        except (ValueError, UnicodeError) as exc:
            rejected.append({"value": value, "reason": str(exc)})
    context.log(f"Parsed {len(targets)} unique targets; rejected {len(rejected)} entries. No network requests sent.")
    return {"summary": f"{len(targets)} targets ready for assessment",
            "data": {"targets": targets, "rejected": rejected},
            "findings": [finding("Invalid target", f"{item['value']}: {item['reason']}") for item in rejected]}
