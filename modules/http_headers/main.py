from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from toolkit.sdk import finding


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def run(context, inputs):
    url = inputs["url"].strip()
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Enter an HTTP(S) URL without embedded credentials")
    timeout = inputs.get("timeout", 10)
    if not 1 <= timeout <= 15:
        raise ValueError("Request timeout must be between 1 and 15 seconds")
    context.log(f"Sending HEAD request to {url}")
    request = Request(url, method="HEAD", headers={"User-Agent": "PentestToolkit/0.1"})
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(request, timeout=timeout)
    except HTTPError as exc:
        response = exc
    with response:
        status = response.code
        headers = dict(response.headers.items())
        lower = {key.lower(): value for key, value in headers.items()}
    observations = []
    if parsed.scheme == "http":
        observations.append(finding("Unencrypted HTTP", "This request used HTTP. Check whether HTTPS is available.", "low"))
    for name in ("content-security-policy", "x-content-type-options"):
        if name not in lower:
            observations.append(finding(f"{name} not observed", "Header absent on this HEAD response. Review applicability to the application's content."))
    if parsed.scheme == "https" and "strict-transport-security" not in lower:
        observations.append(finding("HSTS not observed", "Strict-Transport-Security is absent on this response. Review HTTPS deployment policy."))
    context.log(f"Received HTTP {status}; {len(headers)} headers")
    return {"summary": f"HTTP {status} · {len(headers)} response headers",
            "data": {"url": url, "status": status, "headers": headers}, "findings": observations}
