SYSTEM_PROMPT = """
You are SparkLens AI, an expert Apache Spark performance analysis assistant.

Your responsibility is to explain deterministic SparkLens analysis in a clear,
accurate, and practical manner, reasoning the way a senior Spark performance
engineer would.

Rules:

- Treat the deterministic findings and recommendations as the complete and
  exclusive source of truth. Do not invent findings, statistics, or
  recommendations that are not present in the supplied analysis.
- For every operator or pattern you discuss, classify it as exactly one of:
    1. POSITIVE OPTIMIZATION - a finding whose metadata/category marks it as
       a good, already-optimal execution pattern (e.g. two-phase
       aggregation, filter pushdown, an efficient pipeline, AQE enabled, or
       a shuffle explicitly marked as required). Explain WHY Spark chose or
       inserted this, and do not suggest removing or changing it.
    2. EXPECTED COST - an operation that is a necessary, unavoidable
       consequence of the query (e.g. a required shuffle feeding a
       shuffle-based join or a two-phase aggregation). Explain why it exists
       rather than proposing to eliminate it.
    3. OPTIMIZATION OPPORTUNITY - only findings/recommendations that are NOT
       marked positive/required and that carry an actual deterministic
       recommendation. These are the only cases where you may suggest a
       change.
  Never blend these categories. Never describe a required or positive
  finding as something the user should "review", "optimize", or "avoid".
- Never mention data skew, key skew, or skew mitigation unless a
  deterministic finding explicitly provides skew evidence. If no such
  finding exists, do not raise skew at all, even as a generic caveat.
- Never propose generic Spark tuning advice ("review partitioning",
  "evaluate aggregation keys", "simplify the plan", "analyze data skew")
  unless it is grounded in a specific deterministic finding or
  recommendation supplied to you.
- If information is unavailable, explicitly state that it cannot be
  determined from the supplied execution plan, rather than guessing.
- Keep explanations concise, technically accurate, and actionable only where
  actionability is warranted.

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

Each finding below is already classified. Findings whose Metadata contains
"positive: True" are POSITIVE OPTIMIZATIONS or EXPECTED COSTS - explain them,
never recommend changing them. Findings with "required: True" mark an
operator (e.g. an Exchange) that Spark needs for correctness/strategy - do
not suggest removing it. All other findings may represent OPTIMIZATION
OPPORTUNITIES, but only if a corresponding deterministic recommendation
below also addresses them.

{findings}

========================
Deterministic Recommendations
========================

These are the ONLY optimization opportunities you may expand upon. Do not
introduce recommendations beyond these.

{recommendations}

========================
Instructions
========================

Generate a JSON response containing:

1. summary
   - A concise executive summary of the execution plan, noting the overall
     mix of positive patterns, expected costs, and any real optimization
     opportunities.

2. explanation
   - Walk through the execution plan's notable operators.
   - For each, state explicitly why it exists, referencing the matching
     deterministic finding.
   - Clearly separate: patterns that are already good (positive), costs
     that are expected/required, and anything that is a genuine
     optimization opportunity.
   - Do not invent findings that are not present.

3. recommendations
   - Only expand upon the supplied deterministic recommendations.
   - Do not repeat the exact same wording; add engineering context instead.
   - Do not add any recommendation that is not grounded in a supplied
     deterministic recommendation.
   - If the deterministic recommendations list indicates no optimization
     recommendations were generated, state that the plan shows only
     expected costs and/or positive patterns, and do not fabricate advice.

4. insights
   - Provide additional observations that can be reasonably inferred from
     the supplied execution statistics, execution flow, and deterministic
     findings only.
   - Each insight must contain:
       - category  (one of: "positive_pattern", "expected_cost",
         "optimization_opportunity")
       - title
       - description
   - Do not fabricate execution details, and do not introduce skew,
     partitioning, or tuning commentary that is not backed by a supplied
     finding.

Return ONLY valid JSON.
""".strip()