import importlib.util
import socket
import unittest
from unittest.mock import patch

from toolkit.modules import read_module
from toolkit.runner import Execution, ROOT
from toolkit.sdk import ModuleContext

spec = importlib.util.spec_from_file_location("dns_module_tests", ROOT / "modules/dns_analysis/main.py")
dns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dns)


class DnsTests(unittest.TestCase):
    def test_forward_resolution_deduplicates_names_and_addresses(self):
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 0)),
                   (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 0)),
                   (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 0, 0, 0))]
        with patch.object(dns.socket, "getaddrinfo", return_value=records) as lookup:
            result = dns.run(ModuleContext("test"), {"hosts": "EXAMPLE.COM\nexample.com.\n", "reverse": False})
        self.assertEqual(lookup.call_count, 1)
        row = result["data"]["hosts"][0]
        self.assertEqual(row["host"], "example.com")
        self.assertEqual(len(row["addresses"]), 2)
        self.assertEqual({item["family"] for item in row["addresses"]}, {"IPv4", "IPv6"})
        self.assertTrue(row["observed_at"].endswith("+00:00"))

    def test_literal_addresses_do_not_trigger_forward_queries(self):
        with patch.object(dns.socket, "getaddrinfo") as lookup:
            result = dns.run(ModuleContext("test"), {"hosts": "127.0.0.1\n::1"})
        lookup.assert_not_called()
        self.assertEqual(len(result["data"]["hosts"]), 2)
        self.assertEqual(result["data"]["hosts"][0]["source"], "literal")

    def test_reverse_lookup_error_keeps_forward_evidence(self):
        with patch.object(dns.socket, "gethostbyaddr", side_effect=socket.herror("no reverse record")):
            result = dns.run(ModuleContext("test"), {"hosts": "192.0.2.1", "reverse": True})
        row = result["data"]["hosts"][0]
        self.assertEqual(row["status"], "resolved")
        self.assertIn("reverse_error", row["addresses"][0])

    def test_partial_resolution_failure(self):
        with patch.object(dns.socket, "getaddrinfo", side_effect=socket.gaierror("not found")):
            result = dns.run(ModuleContext("test"), {"hosts": "missing.example\n127.0.0.1"})
        self.assertEqual(result["summary"], "1/2 entries resolved")
        self.assertEqual(result["data"]["hosts"][0]["status"], "unresolved")
        self.assertEqual(result["findings"][0]["severity"], "info")

    def test_invalid_inputs_rejected_without_queries(self):
        with patch.object(dns.socket, "getaddrinfo") as lookup:
            result = dns.run(ModuleContext("test"), {"hosts": "https://example.com\n999.999.1.1\nexample.com:80"})
        lookup.assert_not_called()
        self.assertEqual(len(result["data"]["rejected"]), 3)

    def test_limits_and_idna(self):
        for hosts in ("# comment only", "\n".join(f"host{i}.example" for i in range(21))):
            with self.assertRaises(ValueError):
                dns.run(ModuleContext("test"), {"hosts": hosts})
        self.assertEqual(dns.normalize("bücher.example"), ("xn--bcher-kva.example", False))

    def test_worker_localhost(self):
        record = Execution(read_module(ROOT / "modules/dns_analysis"), {"hosts": "localhost"}).run()
        self.assertEqual(record["status"], "completed", record)
        row = record["result"]["data"]["hosts"][0]
        self.assertEqual(row["status"], "resolved", row)
        self.assertTrue(row["addresses"])
