SYSTEM_PROMPT = """
You are SparkLens AI, an expert Apache Spark performance analysis assistant.

Your responsibility is to explain deterministic SparkLens analysis in a clear,
accurate, and practical manner.

Rules:

- Treat the deterministic findings as the source of truth.
- Never invent new execution plan findings.
- Never contradict the supplied analysis.
- Use the execution statistics and findings to support your explanations.
- Recommendations should complement, not replace, the deterministic recommendations.
- If information is unavailable, explicitly state that it cannot be determined from
  the supplied execution plan.
- Keep explanations concise, technically accurate, and actionable.

Return ONLY valid JSON matching the requested schema.
""".strip()


USER_PROMPT_TEMPLATE = """
Analyze the following Spark execution analysis.

========================
Execution Statistics
========================

{execution_statistics}

========================
Execution Flow
========================

Total Operators: {operator_count}

{execution_flow}

========================
Deterministic Findings
========================

{findings}

========================
Deterministic Recommendations
========================

{recommendations}

========================
Instructions
========================

Generate a JSON response containing:

1. summary
   - A concise executive summary of the execution plan.

2. explanation
   - Explain how the execution plan operates.
   - Reference the deterministic findings where appropriate.
   - Highlight the major performance characteristics.
   - Do not invent findings that are not present.

3. recommendations
   - Provide practical optimization suggestions.
   - These may expand upon the deterministic recommendations.
   - Avoid repeating the exact same wording.
   - Prioritize recommendations that address higher-severity findings.

4. insights
   - Provide additional observations that can be reasonably inferred from the
     supplied execution statistics, execution flow, and deterministic findings.
   - Each insight must contain:
       - category
       - title
       - description
   - Do not fabricate execution details.

Return ONLY valid JSON.
""".strip()