import importlib.util
import json
import sys
import types
import unittest
from unittest.mock import Mock, call, patch

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ai.models import AIExplanation, AIInsight


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

    def test_pipeline_import_error_includes_underlying_cause(self):
        original_import = __import__

        def fail_pipeline_import(name, *args, **kwargs):
            if name == "services.pipeline":
                raise ImportError("No module named 'backend_dependency'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fail_pipeline_import):
            with self.assertRaises(bridge.BridgeError) as context:
                bridge.run_existing_pipeline("plan", enable_ai=False)

        self.assertEqual(
            context.exception.code,
            "BACKEND_UNAVAILABLE",
        )
        self.assertIn(
            "No module named 'backend_dependency'",
            context.exception.message,
        )

    def test_pipeline_receives_ai_enabled_and_disabled_flags(self):
        pipeline = Mock()
        module = types.ModuleType("services.pipeline")
        module.AnalysisPipeline = Mock(
            return_value=types.SimpleNamespace(run=pipeline)
        )
        pipeline.return_value = {"result": "test"}

        with patch.dict(sys.modules, {"services.pipeline": module}):
            bridge.run_existing_pipeline("plan", enable_ai=False)
            bridge.run_existing_pipeline("plan", enable_ai=True)

        self.assertEqual(
            pipeline.call_args_list,
            [
                call("plan", enable_ai=False),
                call("plan", enable_ai=True),
            ],
        )

    def test_missing_gemini_key_keeps_pipeline_analysis(self):
        import services.pipeline as pipeline_module

        plan = (
            REPOSITORY_ROOT / "demo_plans" / "01_simple_scan.txt"
        ).read_text(
            encoding="utf-8"
        )

        with patch.object(pipeline_module.os, "getenv", return_value=None):
            response = bridge.handle_request(
                {
                    "action": "analyze",
                    "plan": plan,
                    "enable_ai": True,
                    "project_root": str(REPOSITORY_ROOT),
                }
            )

        result = response["data"]["result"]
        self.assertTrue(response["success"])
        self.assertIsNone(response["data"]["ai_error"])
        self.assertEqual(
            result["explanation"]["summary"],
            "Gemini API key not configured.",
        )
        self.assertGreater(
            len(result["analysis"]["report"]["findings"]),
            0,
        )

    def test_ai_failure_returns_deterministic_findings(self):
        def fail_ai_then_return_rules(plan, enable_ai):
            if enable_ai:
                try:
                    raise RuntimeError("sensitive provider detail")
                except RuntimeError as cause:
                    raise bridge.BridgeError(
                        "ANALYSIS_FAILED",
                        "The AI step failed.",
                    ) from cause

            return {
                "analysis": {
                    "report": {
                        "findings": [{"title": "Preserved rule finding"}],
                    }
                },
                "explanation": {
                    "summary": "AI explanation disabled.",
                    "explanation": "Deterministic analysis only.",
                    "recommendations": [],
                    "insights": [],
                    "model": "none",
                },
            }

        with (
            patch.object(bridge, "configure_project_root"),
            patch.object(
                bridge,
                "run_existing_pipeline",
                side_effect=fail_ai_then_return_rules,
            ),
        ):
            response = bridge.handle_request(
                {
                    "action": "analyze",
                    "plan": "test plan",
                    "enable_ai": True,
                }
            )

        self.assertTrue(response["success"])
        self.assertEqual(
            response["data"]["result"]["analysis"]["report"]["findings"][0][
                "title"
            ],
            "Preserved rule finding",
        )
        self.assertEqual(
            response["data"]["ai_error"]["code"],
            "AI_EXPLANATION_FAILED",
        )
        self.assertIn(
            "RuntimeError",
            response["data"]["ai_error"]["message"],
        )
        self.assertNotIn(
            "sensitive provider detail",
            response["data"]["ai_error"]["message"],
        )

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

    def test_serializes_ai_explanation_fields(self):
        explanation = AIExplanation(
            summary="AI summary",
            explanation="AI explanation",
            recommendations=["Recommendation"],
            insights=[
                AIInsight(
                    category="performance",
                    title="AI insight",
                    description="AI detail",
                )
            ],
            model="gemini-2.5-flash",
        )

        result = bridge.normalize_json_value(explanation)
        serialized = json.loads(json.dumps(result, allow_nan=False))

        self.assertEqual(serialized["summary"], "AI summary")
        self.assertEqual(
            serialized["recommendations"],
            ["Recommendation"],
        )
        self.assertEqual(
            serialized["insights"][0]["title"],
            "AI insight",
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