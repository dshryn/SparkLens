# SparkLens VS Code Extension

SparkLens analyzes Apache Spark physical execution plans inside VS Code.

The extension uses TypeScript for the user interface and delegates
analysis to the existing Python SparkLens backend.

## Architecture

VS Code Extension
-> Python Bridge
-> Existing SparkLens Backend
-> Structured JSON
-> VS Code Output Channel

The extension does not implement a separate analysis engine.

## Requirements

- Visual Studio Code.
- Node.js and npm.
- Python 3.12 or later, according to the repository's current
  Python requirement.
- The existing SparkLens backend source checkout or a compatible
  installed backend.

Apache Spark itself is not required merely to analyze a saved
formatted physical execution plan.

## Configuration

Open VS Code Settings and search for `SparkLens`.

### sparklens.pythonPath

Optional Python executable used to launch the bridge.

If left empty, the extension automatically uses the local
`<extension>/\.venv` interpreter when present and otherwise falls back
to the system `python` command.

Examples:

- `python`
- `python3`
- `D:\\SparkLens\\vscode-extension\\.venv\\Scripts\\python.exe`

The selected environment must also have the dependencies required by
the SparkLens backend installed.

### sparklens.projectPath

Optional absolute path to the SparkLens repository root.

Example:

`D:\Projects\SparkLens`

If left empty, the extension automatically resolves the backend root
from the repository root one level above the development extension
directory, or from the active workspace when it contains
`services/pipeline.py` and `analyzer/analyzer.py`. This also supports
opening a plan-only folder such as `demo_plans` while running the
development extension.

If analysis fails, the SparkLens Output channel includes the resolved
Python interpreter, backend root, working directory, and bridge path.
Backend import errors include the underlying Python import exception.

### sparklens.analysisTimeoutSeconds

The maximum time permitted for an analysis.

The default is 120 seconds.

## Development

Open a terminal in this directory.

Install development dependencies:

`npm install`

Compile the extension:

`npm run compile`

Check TypeScript types:

`npm run check-types`

Run the Python bridge contract tests:

`npm run test:python`

## Launch the Extension Development Host

1. Open the `vscode-extension` directory itself in VS Code.
2. Run `npm install` if dependencies have not already been installed.
3. Press F5 and select **Run SparkLens Extension** if prompted.
   The launch configuration runs `npm: compile` before starting
   the Extension Development Host.
4. In the new host, set `sparklens.projectPath` to the SparkLens
   repository root if its workspace is not that root, and set
   `sparklens.pythonPath` to a Python 3.12+ environment with the
   backend dependencies installed.
5. Open a Spark physical execution plan.
6. Run `SparkLens: Analyze Current File`.

The result appears in the SparkLens Output Channel.

## Backend integration

The Python bridge currently imports:

`services.pipeline.AnalysisPipeline`

It expects the pipeline to expose:

`AnalysisPipeline.run(plan, enable_ai=True)`

The extension explicitly calls this method with `enable_ai=False`, so
SparkLens extension analysis remains deterministic and does not invoke
AI explanations by default.

Verify the constructor and method signature against the actual
SparkLens source before relying on this integration.

The adapter must be updated if the actual API differs.

## Troubleshooting

### Python cannot be found

Check `sparklens.pythonPath`.

### Backend cannot be imported

Check `sparklens.projectPath` and verify that the selected Python
environment can import the SparkLens dependencies.

### Unsupported Python version

Select Python 3.12 or later.

### Analysis fails

Confirm that the input is a formatted Spark physical execution
plan supported by the existing parser.

### JSON serialization fails

Inspect the Python bridge diagnostics and the actual backend
result models. The bridge must serialize the existing result
rather than invent replacement analysis fields.

## Scope

The initial implementation provides:

- A native VS Code command.
- Python subprocess integration.
- JSON request and response handling.
- Timeout and cancellation handling.
- Findings and recommendations presentation.
- Dependency diagnostics.

Gemini explanations and DAG visualization are follow-up features.

The extension does not modify the existing CLI, Streamlit dashboard,
Python package version, or published PyPI package.
