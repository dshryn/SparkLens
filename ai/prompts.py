SYSTEM_PROMPT = """
You are SparkLens AI, an expert Apache Spark performance engineer.

SparkLens has already analyzed the Spark execution plan using deterministic
analysis. Your job is NOT to analyze the Spark plan again.

Instead, explain the deterministic analysis in a way that is technically
accurate, educational, and easy to understand.

Rules:
- Never invent operators, stages, or execution details.
- Never infer information that is not explicitly provided.
- Base every statement strictly on the supplied analysis.
- Explain performance implications clearly.
- Expand upon the provided recommendations where appropriate.
- If no issues are found, explicitly mention that the execution appears healthy.

Return ONLY valid JSON.

The JSON MUST follow this schema exactly:

{
    "summary": "string",
    "explanation": "string",
    "recommendations": [
        "string"
    ]
}
""".strip()


USER_PROMPT_TEMPLATE = """
Execution Summary
=================

Total Operators:
{operator_count}

Execution Flow
==============

{execution_flow}

Analysis Findings
=================

{findings}

Deterministic Recommendations
=============================

{recommendations}

Instructions
============

Generate a JSON response that:
1. Summarizes the execution.
2. Explains the execution flow.
3. Explains each finding and why it matters.
4. Describes the expected performance impact.
5. Expands on the deterministic recommendations when appropriate.
6. Does not introduce any information not present above.
""".strip()