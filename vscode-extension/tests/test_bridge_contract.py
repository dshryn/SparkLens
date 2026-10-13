import importlib.util
import json
import sys
import unittest

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


BRIDGE_PATH = (
    Path(__file__).resolve().parents[1]
    / "python"
    / "sparklens_vscode_bridge.py"
)

SPEC = importlib.util.spec_from_file_location(
    "sparklens_vscode_bridge",
    BRIDGE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load the SparkLens bridge.")

bridge = importlib.util.module_from_spec(SPEC)

sys.modules[SPEC.name] = bridge
SPEC.loader.exec_module(bridge)


class Severity(Enum):
    HIGH = "high"
    LOW = "low"


@dataclass
class ExampleFinding:
    title: str
    severity: Severity
    evidence: list[str]


class BridgeContractTests(unittest.TestCase):

    def test_valid_request(self):
        request = {
            "action": "analyze",
            "plan": "== Physical Plan ==\nScan",
            "enable_ai": False,
        }

        action, plan, enable_ai, project_root = (
            bridge.validate_request(request)
        )

        self.assertEqual(action, "analyze")
        self.assertIn("Physical Plan", plan)
        self.assertFalse(enable_ai)
        self.assertIsNone(project_root)

    def test_rejects_empty_plan(self):
        request = {
            "action": "analyze",
            "plan": "   ",
            "enable_ai": False,
        }

        with self.assertRaises(bridge.BridgeError) as context:
            bridge.validate_request(request)

        self.assertEqual(
            context.exception.code,
            "INVALID_REQUEST",
        )

    def test_rejects_unsupported_action(self):
        request = {
            "action": "unknown",
            "plan": "test plan",
        }

        with self.assertRaises(bridge.BridgeError) as context:
            bridge.validate_request(request)

        self.assertEqual(
            context.exception.code,
            "UNSUPPORTED_ACTION",
        )

    def test_rejects_non_boolean_ai_flag(self):
        request = {
            "action": "analyze",
            "plan": "test plan",
            "enable_ai": "yes",
        }

        with self.assertRaises(bridge.BridgeError):
            bridge.validate_request(request)

    def test_rejects_non_object_request(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.validate_request([])

    def test_serializes_dataclass_and_enum(self):
        finding = ExampleFinding(
            title="Potential shuffle",
            severity=Severity.HIGH,
            evidence=["Exchange", "Sort"],
        )

        result = bridge.normalize_json_value(finding)

        self.assertEqual(
            result["title"],
            "Potential shuffle",
        )

        self.assertEqual(
            result["severity"],
            "high",
        )

        self.assertEqual(
            result["evidence"],
            ["Exchange", "Sort"],
        )

    def test_success_response_contract(self):
        response = bridge.success_response(
            {
                "result": {
                    "findings": [],
                }
            }
        )

        self.assertTrue(response["success"])
        self.assertIsNone(response["error"])
        self.assertIn("result", response["data"])

        # Ensure the contract can be represented as valid JSON.
        json.dumps(response, allow_nan=False)

    def test_error_response_contract(self):
        response = bridge.error_response(
            "INVALID_REQUEST",
            "Invalid plan.",
        )

        self.assertFalse(response["success"])
        self.assertIsNone(response["data"])
        self.assertEqual(
            response["error"]["code"],
            "INVALID_REQUEST",
        )

    def test_non_finite_float_is_normalized(self):
        result = bridge.normalize_json_value(
            float("inf")
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()