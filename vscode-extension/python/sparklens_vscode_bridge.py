from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


MIN_PYTHON_VERSION = (3, 12)
MAX_REQUEST_BYTES = 20 * 1024 * 1024


class BridgeError(Exception):
    """An expected error that can be returned to the extension."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def success_response(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
    }


def error_response(
    code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


def emit_response(
    response: dict[str, Any],
    exit_code: int,
) -> int:
    """
    Write exactly one JSON response to stdout.

    Diagnostics must be written to stderr instead.
    """

    try:
        sys.stdout.write(
            json.dumps(
                response,
                ensure_ascii=False,
                allow_nan=False,
            )
        )
        sys.stdout.write("\n")
        sys.stdout.flush()

    except (TypeError, ValueError):
        fallback = error_response(
            "SERIALIZATION_ERROR",
            "The bridge could not serialize the analysis result.",
        )

        sys.stdout.write(json.dumps(fallback) + "\n")
        sys.stdout.flush()

        return 1

    return exit_code


def read_request() -> dict[str, Any]:
    """
    Read one JSON request from stdin.

    The bridge handles exactly one request per process.
    """

    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)

    if len(raw) > MAX_REQUEST_BYTES:
        raise BridgeError(
            "REQUEST_TOO_LARGE",
            "The request exceeds the 20 MiB limit.",
        )

    if not raw:
        raise BridgeError(
            "EMPTY_REQUEST",
            "No JSON request was provided.",
        )

    try:
        text = raw.decode("utf-8")

    except UnicodeDecodeError as exc:
        raise BridgeError(
            "INVALID_ENCODING",
            "The request must be valid UTF-8.",
        ) from exc

    try:
        request = json.loads(text)

    except json.JSONDecodeError as exc:
        raise BridgeError(
            "INVALID_JSON",
            "The request is not valid JSON.",
        ) from exc

    if not isinstance(request, dict):
        raise BridgeError(
            "INVALID_REQUEST",
            "The request must be a JSON object.",
        )

    return request


def validate_request(
    request: Any,
) -> tuple[str, str, bool, str | None]:
    if not isinstance(request, dict):
        raise BridgeError(
            "INVALID_REQUEST",
            "The request must be a JSON object.",
        )

    action = request.get("action")

    if action != "analyze":
        raise BridgeError(
            "UNSUPPORTED_ACTION",
            "Supported action: analyze.",
        )

    plan = request.get("plan")

    if not isinstance(plan, str) or not plan.strip():
        raise BridgeError(
            "INVALID_REQUEST",
            "The request must contain a non-empty plan.",
        )

    enable_ai = request.get("enable_ai", False)

    if not isinstance(enable_ai, bool):
        raise BridgeError(
            "INVALID_REQUEST",
            "enable_ai must be a boolean.",
        )

    project_root = request.get("project_root")

    if project_root is not None:
        if not isinstance(project_root, str):
            raise BridgeError(
                "INVALID_REQUEST",
                "project_root must be a string.",
            )

        if not project_root.strip():
            project_root = None

    return action, plan, enable_ai, project_root


def configure_project_root(
    project_root: str | None,
) -> None:
    """
    Make the existing source checkout importable.

    No machine-specific paths are embedded in this bridge.
    """

    if project_root is None:
        return

    root = Path(project_root).expanduser().resolve()

    if not root.is_dir():
        raise BridgeError(
            "BACKEND_NOT_FOUND",
            "The configured SparkLens project directory does not exist.",
        )

    expected_files = (
        root / "services" / "pipeline.py",
        root / "analyzer" / "analyzer.py",
    )

    if not all(path.is_file() for path in expected_files):
        raise BridgeError(
            "BACKEND_NOT_FOUND",
            "The configured directory does not contain the expected "
            "SparkLens backend modules.",
        )

    root_string = str(root)

    if root_string not in sys.path:
        sys.path.insert(0, root_string)


def normalize_json_value(
    value: Any,
    depth: int = 0,
) -> Any:
    """
    Convert common Python model values into JSON-compatible values.

    This function serializes data only. It does not calculate metrics,
    generate findings, or alter analysis results.
    """

    if depth > 80:
        raise ValueError(
            "The backend result exceeds the supported serialization depth."
        )

    if value is None:
        return None

    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        import math

        if not math.isfinite(value):
            return None

        return value

    if isinstance(value, Enum):
        return normalize_json_value(value.value, depth + 1)

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value) and not isinstance(value, type):
        return normalize_json_value(
            asdict(value),
            depth + 1,
        )

    if isinstance(value, dict):
        return {
            str(key): normalize_json_value(item, depth + 1)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            normalize_json_value(item, depth + 1)
            for item in value
        ]

    # Support model classes that expose a standard dictionary serializer.
    # Avoid invoking arbitrary methods on unknown backend objects.
    if hasattr(value, "model_dump"):
        return normalize_json_value(
            value.model_dump(mode="json"),
            depth + 1,
        )

    if hasattr(value, "dict") and callable(value.dict):
        return normalize_json_value(
            value.dict(),
            depth + 1,
        )

    raise TypeError(
        f"Unsupported backend result type: {type(value).__name__}"
    )


def run_existing_pipeline(
    plan: str,
    enable_ai: bool,
) -> Any:
    """
    The single adapter function for the existing SparkLens backend.

    The investigation report identifies:
        AnalysisPipeline.run(plan, enable_ai=True)

    Verify the constructor and method signature against
    services/pipeline.py in the actual repository.
    """

    try:
        from services.pipeline import AnalysisPipeline

    except ImportError as exc:
        raise BridgeError(
            "BACKEND_UNAVAILABLE",
            "The SparkLens analysis pipeline could not be imported. "
            "Configure sparklens.projectPath or install a compatible "
            "SparkLens backend in the selected Python environment.",
        ) from exc

    try:
        pipeline = AnalysisPipeline()

        result = pipeline.run(
            plan,
            enable_ai=enable_ai,
        )

        return result

    except BridgeError:
        raise

    except Exception as exc:
        # Keep full tracebacks out of the ordinary JSON response.
        print(
            f"SparkLens analysis failed: {type(exc).__name__}",
            file=sys.stderr,
        )

        raise BridgeError(
            "ANALYSIS_FAILED",
            "SparkLens could not analyze this execution plan. "
            "Check that the file contains a supported formatted "
            "Spark physical execution plan.",
        ) from exc


def handle_request(
    request: dict[str, Any],
) -> dict[str, Any]:
    _, plan, enable_ai, project_root = validate_request(request)

    if sys.version_info < MIN_PYTHON_VERSION:
        raise BridgeError(
            "UNSUPPORTED_PYTHON",
            "SparkLens requires Python 3.12 or later according to "
            "the repository investigation. Select a compatible "
            "Python interpreter.",
        )

    configure_project_root(project_root)

    result = run_existing_pipeline(
        plan=plan,
        enable_ai=enable_ai,
    )

    try:
        normalized = normalize_json_value(result)

    except (TypeError, ValueError) as exc:
        print(
            f"Result serialization failed: {type(exc).__name__}",
            file=sys.stderr,
        )

        raise BridgeError(
            "SERIALIZATION_ERROR",
            "The backend returned a result that the bridge could "
            "not serialize. Check backend model compatibility.",
        ) from exc

    return success_response(
        {
            "result": normalized,
        }
    )


def main() -> int:
    try:
        request = read_request()
        response = handle_request(request)

        return emit_response(response, 0)

    except BridgeError as exc:
        return emit_response(
            error_response(
                exc.code,
                exc.message,
            ),
            1,
        )

    except Exception as exc:
        print(
            "Unexpected bridge failure: "
            f"{type(exc).__name__}",
            file=sys.stderr,
        )

        # Full tracebacks are intentionally not returned to VS Code.
        if os.environ.get("SPARKLENS_BRIDGE_DEBUG") == "1":
            traceback.print_exc(file=sys.stderr)

        return emit_response(
            error_response(
                "INTERNAL_ERROR",
                "An unexpected error occurred in the SparkLens bridge.",
            ),
            1,
        )


if __name__ == "__main__":
    raise SystemExit(main())