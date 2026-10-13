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

The Python executable used to launch the bridge.

Examples:

- `python`
- `python3`
- An absolute path to a Python executable.

### sparklens.projectPath

The absolute path to the SparkLens repository root.

Example:

`D:\Projects\SparkLens`

Leave this empty when the active workspace is the SparkLens
repository and its root contains `services/pipeline.py`.

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

1. Open the `vscode-extension` directory in VS Code.
2. Open the Run and Debug panel.
3. Create or select an Extension Development Host launch
   configuration that starts the extension from this directory.
4. Start the Extension Development Host.
5. Open a Spark physical execution plan.
6. Run `SparkLens: Analyze Current File`.

The result appears in the SparkLens Output Channel.

## Backend integration

The Python bridge currently imports:

`services.pipeline.AnalysisPipeline`

It expects the pipeline to expose:

`AnalysisPipeline.run(plan, enable_ai=False)`

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
