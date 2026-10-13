import * as vscode from "vscode";

function isRecord(
    value: unknown
): value is Record<string, unknown> {
    return (
        typeof value === "object" &&
        value !== null &&
        !Array.isArray(value)
    );
}

function formatValue(value: unknown): string {
    if (value === null || value === undefined) {
        return "Not provided";
    }

    if (typeof value === "string") {
        return value;
    }

    if (
        typeof value === "number" ||
        typeof value === "boolean"
    ) {
        return String(value);
    }

    try {
        return JSON.stringify(value, null, 2);
    } catch {
        return String(value);
    }
}

function findArray(
    value: unknown,
    candidateKeys: string[],
    depth = 0
): unknown[] | undefined {
    if (depth > 8 || !isRecord(value)) {
        return undefined;
    }

    for (const key of candidateKeys) {
        const candidate = value[key];

        if (Array.isArray(candidate)) {
            return candidate;
        }
    }

    for (const key of [
        "report",
        "analysis",
        "analysis_result",
        "analysisResult",
        "result",
        "data"
    ]) {
        const nested = value[key];

        if (isRecord(nested)) {
            const found = findArray(
                nested,
                candidateKeys,
                depth + 1
            );

            if (found) {
                return found;
            }
        }
    }

    return undefined;
}

function findField(
    value: unknown,
    candidateKeys: string[],
    depth = 0
): unknown {
    if (depth > 8 || !isRecord(value)) {
        return undefined;
    }

    for (const key of candidateKeys) {
        if (key in value) {
            return value[key];
        }
    }

    for (const key of [
        "report",
        "analysis",
        "analysis_result",
        "analysisResult",
        "result",
        "data"
    ]) {
        const nested = value[key];

        if (isRecord(nested)) {
            const found = findField(
                nested,
                candidateKeys,
                depth + 1
            );

            if (found !== undefined) {
                return found;
            }
        }
    }

    return undefined;
}

function formatFinding(
    finding: unknown,
    index: number
): string {
    if (!isRecord(finding)) {
        return `${index + 1}. ${formatValue(finding)}`;
    }

    const title =
        finding.title ??
        finding.name ??
        finding.rule_name ??
        finding.rule ??
        `Finding ${index + 1}`;

    const severity =
        finding.severity ??
        finding.level ??
        finding.priority;

    const description =
        finding.description ??
        finding.message ??
        finding.explanation;

    const lines = [
        `${index + 1}. ${formatValue(title)}`
    ];

    if (severity !== undefined) {
        lines.push(
            `   Severity: ${formatValue(severity)}`
        );
    }

    if (description !== undefined) {
        lines.push(
            `   ${formatValue(description)}`
        );
    }

    if (finding.evidence !== undefined) {
        lines.push(
            `   Evidence: ${formatValue(finding.evidence)}`
        );
    }

    if (finding.recommendation !== undefined) {
        lines.push(
            `   Recommendation: ${formatValue(finding.recommendation)}`
        );
    }

    return lines.join("\n");
}

function formatRecommendation(
    recommendation: unknown,
    index: number
): string {
    if (!isRecord(recommendation)) {
        return `${index + 1}. ${formatValue(recommendation)}`;
    }

    const title =
        recommendation.title ??
        recommendation.name ??
        recommendation.recommendation ??
        `Recommendation ${index + 1}`;

    const description =
        recommendation.description ??
        recommendation.message ??
        recommendation.rationale;

    const lines = [
        `${index + 1}. ${formatValue(title)}`
    ];

    if (description !== undefined) {
        lines.push(
            `   ${formatValue(description)}`
        );
    }

    return lines.join("\n");
}

export function renderResults(
    channel: vscode.OutputChannel,
    result: unknown,
    aiError: { code: string; message: string } | null = null
): void {
    channel.clear();

    channel.appendLine("========================================");
    channel.appendLine("             SPARKLENS");
    channel.appendLine("========================================");
    channel.appendLine("");

    const statistics = findField(
        result,
        ["statistics", "stats"]
    );

    if (statistics !== undefined) {
        channel.appendLine("STATISTICS");
        channel.appendLine("----------------------------------------");
        channel.appendLine(formatValue(statistics));
        channel.appendLine("");
    }

    const findings = findArray(
        result,
        ["findings"]
    );

    channel.appendLine("RULE-BASED FINDINGS");
    channel.appendLine("----------------------------------------");

    if (findings && findings.length > 0) {
        findings.forEach((finding, index) => {
            channel.appendLine(
                formatFinding(finding, index)
            );

            channel.appendLine("");
        });
    } else {
        channel.appendLine(
            "No findings array was found in the returned backend result."
        );

        channel.appendLine(
            "Inspect the serialized result below to verify the backend schema."
        );

        channel.appendLine("");
    }

    const explanation =
        isRecord(result) && isRecord(result.explanation)
            ? result.explanation
            : undefined;

    channel.appendLine("GEMINI AI EXPLANATION");
    channel.appendLine("----------------------------------------");

    if (aiError) {
        channel.appendLine(
            "AI explanation failed; rule-based findings are preserved."
        );
        channel.appendLine(aiError.message);
        channel.appendLine("");
    } else if (explanation) {
        channel.appendLine(`Summary: ${formatValue(explanation.summary)}`);
        channel.appendLine("");
        channel.appendLine(formatValue(explanation.explanation));
        channel.appendLine("");

        const recommendations =
            Array.isArray(explanation.recommendations)
                ? explanation.recommendations
                : [];
        if (recommendations.length > 0) {
            channel.appendLine("AI-generated recommendations");
            recommendations.forEach((recommendation, index) => {
                channel.appendLine(
                    formatRecommendation(recommendation, index)
                );
            });
            channel.appendLine("");
        }

        const insights =
            Array.isArray(explanation.insights)
                ? explanation.insights
                : [];
        if (insights.length > 0) {
            channel.appendLine("AI-generated insights");
            insights.forEach((insight, index) => {
                channel.appendLine(formatFinding(insight, index));
                channel.appendLine("");
            });
        }
    } else {
        channel.appendLine(
            "No AI explanation was returned by the backend."
        );

        channel.appendLine("");
    }

    channel.appendLine("RAW BACKEND RESULT");
    channel.appendLine("----------------------------------------");
    channel.appendLine(formatValue(result));

    channel.show(true);
}