import json
import sys
import types
import unittest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Stub out the azure.functions module so tests run without the SDK installed.
# ---------------------------------------------------------------------------
_af = types.ModuleType("azure.functions")

class _HttpRequest:
    def __init__(self, body: dict):
        self._body = body

    def get_json(self):
        return self._body


class _HttpResponse:
    def __init__(self, body: str, status_code: int = 200, mimetype: str = "application/json"):
        self.get_body = lambda: body.encode()
        self.status_code = status_code
        self.mimetype = mimetype


_af.HttpRequest = _HttpRequest
_af.HttpResponse = _HttpResponse

azure_stub = types.ModuleType("azure")
azure_stub.functions = _af
sys.modules.setdefault("azure", azure_stub)
sys.modules["azure.functions"] = _af

# ---------------------------------------------------------------------------
# Now import the function under test
# ---------------------------------------------------------------------------
import importlib, pathlib

_func_path = pathlib.Path(__file__).parent.parent / "process_batch"
_spec = importlib.util.spec_from_file_location(
    "process_batch", _func_path / "__init__.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
main = _mod.main


def _make_request(batch_id="b1", rows=100, source="test"):
    return _HttpRequest({"batch_id": batch_id, "rows": rows, "source": source})


class TestProcessBatch(unittest.TestCase):
    def test_small_batch_returns_200(self):
        resp = main(_make_request(rows=1000))
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.get_body())
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["processed_rows"], 1000)

    def test_large_batch_returns_200(self):
        """rows > 50 000 must NOT raise RuntimeError and must return HTTP 200."""
        resp = main(_make_request(batch_id="big", rows=60000, source="scheduled"))
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.get_body())
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["processed_rows"], 60000)

    def test_very_large_batch_returns_200(self):
        """rows = 200 000 (as in data/payload-large.json) must succeed."""
        resp = main(_make_request(batch_id="huge", rows=200000, source="scheduled"))
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.get_body())
        self.assertEqual(body["processed_rows"], 200000)

    def test_response_contains_batch_id(self):
        resp = main(_make_request(batch_id="abc-123"))
        body = json.loads(resp.get_body())
        self.assertEqual(body["batch_id"], "abc-123")

    def test_response_contains_source(self):
        resp = main(_make_request(source="manual"))
        body = json.loads(resp.get_body())
        self.assertEqual(body["source"], "manual")

    def test_default_values(self):
        req = _HttpRequest({})
        resp = main(req)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.get_body())
        self.assertEqual(body["batch_id"], "unknown")
        self.assertEqual(body["processed_rows"], 0)
        self.assertEqual(body["source"], "scheduled")

    def test_no_runtime_error_guard_in_source(self):
        """Regression: ensure the source file contains no large-batch RuntimeError guard."""
        src = (_func_path / "__init__.py").read_text()
        self.assertNotIn(
            'raise RuntimeError',
            src,
            "Source must not contain a RuntimeError guard that blocks large batches",
        )


if __name__ == "__main__":
    unittest.main()
