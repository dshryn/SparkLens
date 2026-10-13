import * as vscode from "vscode";
import { spawn } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";

export interface BridgeError {
    code: string;
    message: string;
}

export interface BridgeResponse {
    success: boolean;
    data: {
        result: unknown;
        aiError: BridgeError | null;
    } | null;
    error: BridgeError | null;
}

export interface AnalyzeOptions {
    plan: string;
    projectRoot: string;
    enableAI?: boolean;
}

export class SparkLensBackendError extends Error {
    constructor(
        public readonly code: string,
        message: string
    ) {
        super(message);
        this.name = "SparkLensBackendError";
    }
}

function getConfiguration() {
    return vscode.workspace.getConfiguration("sparklens");
}

function hasSparkLensBackendRoot(root: string): boolean {
    return (
        fs.existsSync(path.join(root, "services", "pipeline.py")) &&
        fs.existsSync(path.join(root, "analyzer", "analyzer.py"))
    );
}

export function resolveProjectRoot(extensionPath?: string): string {
    const configured = getConfiguration().get<string>(
        "projectPath",
        ""
    ).trim();

    if (configured) {
        const resolved = path.resolve(configured);

        if (!fs.existsSync(resolved)) {
            throw new SparkLensBackendError(
                "BACKEND_NOT_FOUND",
                `The configured SparkLens project directory does not exist:\n${resolved}`
            );
        }

        return resolved;
    }

    const candidates: string[] = [];

    if (extensionPath) {
        candidates.push(
            path.resolve(extensionPath, ".."),
            extensionPath
        );
    }

    const workspace = vscode.workspace.workspaceFolders?.[0];

    if (workspace) {
        candidates.push(workspace.uri.fsPath);
    }

    for (const candidate of candidates) {
        if (hasSparkLensBackendRoot(candidate)) {
            return candidate;
        }
    }

    throw new SparkLensBackendError(
        "NO_WORKSPACE",
        "Open the SparkLens repository or configure sparklens.projectPath."
    );
}

function getPythonExecutable(extensionPath?: string): string {
    const configured = getConfiguration().get<string>(
        "pythonPath",
        ""
    ).trim();

    if (configured) {
        return configured;
    }

    if (extensionPath) {
        const bundledPython = path.join(
            extensionPath,
            ".venv",
            process.platform === "win32"
                ? path.join("Scripts", "python.exe")
                : "bin/python"
        );

        if (fs.existsSync(bundledPython)) {
            return bundledPython;
        }
    }

    return "python";
}

export function getAnalysisRuntimeDetails(
    extensionPath: string,
    projectRoot: string
): string[] {
    const configuredProjectPath = getConfiguration()
        .get<string>("projectPath", "")
        .trim();

    return [
        `Python interpreter: ${getPythonExecutable(extensionPath)}`,
        `Project root: ${projectRoot}`,
        `sparklens.projectPath: ${configuredProjectPath || "(unset; auto-resolved)"}`,
        `Working directory: ${projectRoot}`,
        `Bridge script: ${path.join(
            extensionPath,
            "python",
            "sparklens_vscode_bridge.py"
        )}`
    ];
}

function getTimeoutMs(): number {
    const seconds = getConfiguration().get<number>(
        "analysisTimeoutSeconds",
        120
    );

    const bounded = Math.min(
        600,
        Math.max(5, seconds)
    );

    return bounded * 1000;
}

function resolveBridgePath(
    extensionPath: string
): string {
    const bridgePath = path.join(
        extensionPath,
        "python",
        "sparklens_vscode_bridge.py"
    );

    if (!fs.existsSync(bridgePath)) {
        throw new SparkLensBackendError(
            "BRIDGE_NOT_FOUND",
            `The SparkLens Python bridge could not be found:\n${bridgePath}`
        );
    }

    return bridgePath;
}

function validateResponse(
    value: unknown
): BridgeResponse {
    if (
        typeof value !== "object" ||
        value === null
    ) {
        throw new SparkLensBackendError(
            "INVALID_RESPONSE",
            "The Python bridge returned a response that is not a JSON object."
        );
    }

    const candidate = value as Record<string, unknown>;

    if (typeof candidate.success !== "boolean") {
        throw new SparkLensBackendError(
            "INVALID_RESPONSE",
            "The Python bridge response is missing the success field."
        );
    }

    if (candidate.success) {
        if (
            typeof candidate.data !== "object" ||
            candidate.data === null
        ) {
            throw new SparkLensBackendError(
                "INVALID_RESPONSE",
                "The successful bridge response is missing its data object."
            );
        }

        const data = candidate.data as Record<string, unknown>;

        if (!("result" in data)) {
            throw new SparkLensBackendError(
                "INVALID_RESPONSE",
                "The bridge response does not contain the analysis result."
            );
        }

        return {
            success: true,
            data: {
                result: data.result,
                aiError: parseBridgeError(data.ai_error)
            },
            error: null
        };
    }

    const rawError = candidate.error;

    if (
        typeof rawError !== "object" ||
        rawError === null
    ) {
        throw new SparkLensBackendError(
            "INVALID_RESPONSE",
            "The failed bridge response does not contain structured error information."
        );
    }

    return {
        success: false,
        data: null,
        error: parseBridgeError(rawError) ?? {
            code: "UNKNOWN_ERROR",
            message: "The SparkLens bridge reported an unspecified error."
        }
    };
}

function parseBridgeError(value: unknown): BridgeError | null {
    if (
        typeof value !== "object" ||
        value === null ||
        Array.isArray(value)
    ) {
        return null;
    }

    const error = value as Record<string, unknown>;

    if (typeof error.message !== "string") {
        return null;
    }

    return {
        code:
            typeof error.code === "string"
                ? error.code
                : "UNKNOWN_ERROR",
        message: error.message
    };
}
export async function analyzePlan(
    extensionPath: string,
    options: AnalyzeOptions,
    cancellationToken: vscode.CancellationToken
): Promise<BridgeResponse> {
    const python = getPythonExecutable(extensionPath);
    const bridgePath = resolveBridgePath(extensionPath);
    const timeoutMs = getTimeoutMs();

    if (!options.plan.trim()) {
        throw new SparkLensBackendError(
            "EMPTY_PLAN",
            "The selected file is empty."
        );
    }

    if (
        Buffer.byteLength(options.plan, "utf8") >
        20 * 1024 * 1024
    ) {
        throw new SparkLensBackendError(
            "PLAN_TOO_LARGE",
            "The selected execution plan exceeds the 20 MiB limit."
        );
    }

    const request = {
        action: "analyze",
        plan: options.plan,
        enable_ai: options.enableAI ?? false,
        project_root: options.projectRoot
    };

    return new Promise<BridgeResponse>((resolve, reject) => {
        let child: ReturnType<typeof spawn>;

        try {
            child = spawn(
                python,
                [bridgePath],
                {
                    cwd: options.projectRoot,
                    shell: false,
                    windowsHide: true,
                    stdio: ["pipe", "pipe", "pipe"]
                }
            );
        } catch {
            reject(
                new SparkLensBackendError(
                    "PYTHON_START_FAILED",
                    `Could not start Python using "${python}". Check sparklens.pythonPath.`
                )
            );

            return;
        }

        if (
            !child.stdout ||
            !child.stderr ||
            !child.stdin
        ) {
            child.kill();
            reject(
                new SparkLensBackendError(
                    "PYTHON_START_FAILED",
                    `Could not start Python using "${python}". Check sparklens.pythonPath.`
                )
            );
            return;
        }

        let stdout = "";
        let stderr = "";
        let settled = false;

        const timer = setTimeout(() => {
            child.kill();

            finishReject(
                new SparkLensBackendError(
                    "ANALYSIS_TIMEOUT",
                    `SparkLens analysis exceeded ${Math.round(timeoutMs / 1000)} seconds.`
                )
            );
        }, timeoutMs);

        const cancellationSubscription =
            cancellationToken.onCancellationRequested(() => {
                child.kill();

                finishReject(
                    new SparkLensBackendError(
                        "CANCELLED",
                        "SparkLens analysis was cancelled."
                    )
                );
            });

        function cleanup(): void {
            clearTimeout(timer);
            cancellationSubscription.dispose();
        }

        function finishResolve(value: BridgeResponse): void {
            if (settled) {
                return;
            }

            settled = true;
            cleanup();
            resolve(value);
        }

        function finishReject(error: Error): void {
            if (settled) {
                return;
            }

            settled = true;
            cleanup();
            reject(error);
        }

        child.stdout.setEncoding("utf8");
        child.stderr.setEncoding("utf8");

        child.stdout.on("data", (chunk: string) => {
            stdout += chunk;

            if (stdout.length > 25 * 1024 * 1024) {
                child.kill();

                finishReject(
                    new SparkLensBackendError(
                        "RESPONSE_TOO_LARGE",
                        "The Python bridge produced an unexpectedly large response."
                    )
                );
            }
        });

        child.stderr.on("data", (chunk: string) => {
            if (stderr.length < 16 * 1024) {
                stderr += chunk;
            }
        });

        child.on("error", (error: NodeJS.ErrnoException) => {
            finishReject(
                new SparkLensBackendError(
                    error.code === "ENOENT"
                        ? "PYTHON_NOT_FOUND"
                        : "PYTHON_START_FAILED",
                    error.code === "ENOENT"
                        ? `Python executable "${python}" was not found.`
                        : `Could not launch Python: ${error.message}`
                )
            );
        });

        child.on("close", (code) => {
            if (settled) {
                return;
            }

            const output = stdout.trim();

            if (!output) {
                finishReject(
                    new SparkLensBackendError(
                        "EMPTY_RESPONSE",
                        stderr.trim() ||
                            `The bridge exited without a JSON response. Exit code: ${code}.`
                    )
                );

                return;
            }

            let response: BridgeResponse;

            try {
                response = validateResponse(JSON.parse(output));
            } catch (error) {
                finishReject(
                    error instanceof Error
                        ? error
                        : new SparkLensBackendError(
                            "INVALID_RESPONSE",
                            "The bridge returned invalid JSON."
                        )
                );

                return;
            }

            if (!response.success) {
                finishReject(
                    new SparkLensBackendError(
                        response.error?.code ?? "ANALYSIS_FAILED",
                        response.error?.message ?? "SparkLens analysis failed."
                    )
                );

                return;
            }

            if (code !== 0) {
                finishReject(
                    new SparkLensBackendError(
                        "NONZERO_EXIT",
                        `The Python bridge exited with code ${code}.`
                    )
                );

                return;
            }

            finishResolve(response);
        });

        child.stdin.on("error", (error) => {
            finishReject(
                new SparkLensBackendError(
                    "REQUEST_WRITE_FAILED",
                    `Could not send the request to Python: ${error.message}`
                )
            );
        });

        child.stdin.end(
            JSON.stringify(request),
            "utf8"
        );
    });
}