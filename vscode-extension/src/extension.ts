import * as vscode from "vscode";

import {
    analyzePlan,
    SparkLensBackendError
} from "./backend";

import {
    renderResults
} from "./results";

export function activate(
    context: vscode.ExtensionContext
): void {
    const output = vscode.window.createOutputChannel(
        "SparkLens"
    );

    context.subscriptions.push(output);

    const analyzeCommand = vscode.commands.registerCommand(
        "sparklens.analyzeCurrentFile",
        async () => {
            const editor = vscode.window.activeTextEditor;

            if (!editor) {
                vscode.window.showWarningMessage(
                    "SparkLens: Open a Spark execution plan before running analysis."
                );

                return;
            }

            const document = editor.document;

            if (document.isClosed) {
                vscode.window.showWarningMessage(
                    "SparkLens: The selected document is no longer available."
                );

                return;
            }

            const plan = document.getText();

            if (!plan.trim()) {
                vscode.window.showWarningMessage(
                    "SparkLens: The current file is empty."
                );

                return;
            }

            let projectRoot: string;

            try {
                const config = vscode.workspace.getConfiguration(
                    "sparklens"
                );

                const configuredPath = config.get<string>(
                    "projectPath",
                    ""
                ).trim();

                if (configuredPath) {
                    projectRoot = configuredPath;
                } else {
                    const workspace =
                        vscode.workspace.workspaceFolders?.[0];

                    if (!workspace) {
                        throw new SparkLensBackendError(
                            "NO_WORKSPACE",
                            "Open the SparkLens repository or configure sparklens.projectPath."
                        );
                    }

                    projectRoot = workspace.uri.fsPath;
                }
            } catch (error) {
                vscode.window.showErrorMessage(
                    error instanceof Error
                        ? error.message
                        : "Could not determine the SparkLens project directory."
                );

                return;
            }

            const progressSource =
                new vscode.CancellationTokenSource();

            try {
                await vscode.window.withProgress(
                    {
                        location: vscode.ProgressLocation.Notification,
                        title: "SparkLens: Analyzing execution plan",
                        cancellable: true
                    },
                    async (
                        _progress,
                        cancellationToken
                    ) => {
                        cancellationToken.onCancellationRequested(
                            () => progressSource.cancel()
                        );

                        const response = await analyzePlan(
                            context.extensionPath,
                            {
                                plan,
                                projectRoot,
                                enableAI: false
                            },
                            cancellationToken
                        );

                        if (cancellationToken.isCancellationRequested) {
                            return;
                        }

                        if (!response.success || !response.data) {
                            throw new SparkLensBackendError(
                                response.error?.code ?? "ANALYSIS_FAILED",
                                response.error?.message ?? "SparkLens analysis failed."
                            );
                        }

                        renderResults(
                            output,
                            response.data.result
                        );

                        vscode.window.showInformationMessage(
                            "SparkLens analysis completed."
                        );
                    }
                );
            } catch (error) {
                const message =
                    error instanceof Error
                        ? error.message
                        : "An unexpected error occurred.";

                output.appendLine("");
                output.appendLine("ANALYSIS ERROR");
                output.appendLine("----------------------------------------");
                output.appendLine(message);

                output.show(true);

                vscode.window.showErrorMessage(
                    `SparkLens: ${message}`
                );
            } finally {
                progressSource.dispose();
            }
        }
    );

    context.subscriptions.push(analyzeCommand);
}

export function deactivate(): void {
    // No persistent processes or background services are maintained.
}