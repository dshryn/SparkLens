from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG
from models.physical_operator import PhysicalOperator

from .base import Rule


class ExecutionQualityRule(Rule):
    """
    Detects GOOD / EXPECTED execution patterns rather than only problems.

    Findings produced by this rule are explanatory in nature and are used by
    RecommendationEngine to suppress generic optimization advice when the
    plan is already behaving correctly.

    Positive / explanatory findings carry metadata:
        - "positive": True
        - "category": one of
              "required_shuffle_aggregation"
              "required_shuffle_join"
              "two_phase_aggregation"
              "filter_pushdown"
              "efficient_pipeline"
              "aqe_enabled"

    Required Exchange operators are additionally marked with:
        - "required": True
        - "required_operator_id": <exchange operator id>

    NOTE on DAG direction: `dag.children(op)` returns the operators whose
    output FEEDS `op` (i.e. upstream / input side, matching the nesting of
    the printed physical plan). `parents` (built below) returns the
    operator(s) that CONSUME `op`'s output (i.e. downstream side). This
    matters for Exchange: the operator that produced the data flowing
    INTO the Exchange is one of its `children`; the operator that
    CONSUMES the Exchange's output (e.g. the final/merge aggregation, or
    a shuffle join) is one of its `parents`.
    """

    _AGG_TYPES = (
        OperatorType.HASH_AGGREGATE,
        OperatorType.SORT_AGGREGATE,
    )

    _SHUFFLE_JOIN_TYPES = (
        OperatorType.SORT_MERGE_JOIN,
        OperatorType.SHUFFLE_HASH_JOIN,
    )

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        parents = self._build_parent_map(dag)

        findings.extend(self._detect_required_shuffles(dag, parents))
        findings.extend(self._detect_two_phase_aggregation(dag))
        findings.extend(self._detect_filter_pushdown(dag, parents))
        findings.extend(self._detect_aqe(dag))

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_parent_map(
        dag: ExecutionDAG,
    ) -> dict[int, list[int]]:

        parents: dict[int, list[int]] = {
            operator_id: [] for operator_id in dag.operators
        }

        for operator in dag.operators.values():
            for child in dag.children(operator.operator_id):
                parents.setdefault(child.operator_id, []).append(
                    operator.operator_id
                )

        return parents

    def _detect_required_shuffles(
        self,
        dag: ExecutionDAG,
        parents: dict[int, list[int]],
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.EXCHANGE:
                continue

            # Upstream input(s) feeding the Exchange.
            children = dag.children(operator.operator_id)

            # Downstream consumer(s) of the Exchange's output.
            parent_ids = parents.get(operator.operator_id, [])

            parent_ops: list[PhysicalOperator] = [
                parent_op
                for parent_id in parent_ids
                if (parent_op := dag.get_operator(parent_id)) is not None
            ]

            # Exchange whose output is consumed by a final/merge
            # aggregation, and whose input comes from a partial
            # aggregation => required shuffle for two-phase agg.
            if self._feeds_merge_aggregation(
                parent_ops
            ) and self._preceded_by_partial_aggregation(children):
                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Required Shuffle (Aggregation)",
                        description=(
                            "Spark inserts this shuffle to redistribute "
                            "partially aggregated data so the final "
                            "aggregation can combine results across "
                            "partitions. This exchange is required by the "
                            "two-phase aggregation strategy and is not an "
                            "optimization target."
                        ),
                        severity=Severity.LOW,
                        operator_id=operator.operator_id,
                        metadata={
                            "positive": True,
                            "category": "required_shuffle_aggregation",
                            "required": True,
                            "required_operator_id": operator.operator_id,
                        },
                    )
                )
                continue

            # Exchange whose output is consumed by a shuffle-based join
            # (Sort Merge / Shuffle Hash Join) => required shuffle for the
            # join strategy.
            if self._feeds_shuffle_join(parent_ops):
                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Required Shuffle (Join)",
                        description=(
                            "Spark inserts this shuffle to co-locate join "
                            "keys on the same partition, which is required "
                            "by the selected join strategy. This exchange "
                            "is not an optimization target."
                        ),
                        severity=Severity.LOW,
                        operator_id=operator.operator_id,
                        metadata={
                            "positive": True,
                            "category": "required_shuffle_join",
                            "required": True,
                            "required_operator_id": operator.operator_id,
                        },
                    )
                )

        return findings

    @staticmethod
    def _feeds_merge_aggregation(
        parent_ops: list[PhysicalOperator],
    ) -> bool:
        """True if one of the downstream consumers is a final/merge agg."""

        for parent in parent_ops:

            if parent.operator_type not in ExecutionQualityRule._AGG_TYPES:
                continue

            arguments = " ".join(parent.arguments).lower()

            if "finalmerge_" in arguments or "merge_" in arguments:
                return True

        return False

    @staticmethod
    def _preceded_by_partial_aggregation(
        children: list[PhysicalOperator],
    ) -> bool:
        """True if one of the upstream inputs is a partial aggregation."""

        for child in children:

            if child.operator_type not in ExecutionQualityRule._AGG_TYPES:
                continue

            arguments = " ".join(child.arguments).lower()

            if "partial_" in arguments:
                return True

        return False

    @staticmethod
    def _feeds_shuffle_join(
        parent_ops: list[PhysicalOperator],
    ) -> bool:
        """True if one of the downstream consumers is a shuffle join."""

        return any(
            parent.operator_type in ExecutionQualityRule._SHUFFLE_JOIN_TYPES
            for parent in parent_ops
        )

    def _detect_two_phase_aggregation(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        partial_ops: list[PhysicalOperator] = []
        merge_ops: list[PhysicalOperator] = []

        for operator in dag.operators.values():

            if operator.operator_type not in self._AGG_TYPES:
                continue

            arguments = " ".join(operator.arguments).lower()

            if "partial_" in arguments:
                partial_ops.append(operator)

            elif "finalmerge_" in arguments or "merge_" in arguments:
                merge_ops.append(operator)

        if partial_ops and merge_ops:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Two-Phase Aggregation",
                    description=(
                        "Spark performs a partial (map-side) aggregation "
                        "followed by a final merge aggregation. This "
                        "reduces the volume of data shuffled and is the "
                        "expected, efficient strategy for this aggregation."
                    ),
                    severity=Severity.LOW,
                    operator_id=partial_ops[0].operator_id,
                    metadata={
                        "positive": True,
                        "category": "two_phase_aggregation",
                    },
                )
            )

        return findings

    def _detect_filter_pushdown(
        self,
        dag: ExecutionDAG,
        parents: dict[int, list[int]],
    ) -> list[AnalysisFinding]:

        # Types that count as a "data source" for the purpose of detecting
        # a filter placed immediately after a scan/source (filter
        # pushdown / early filtering). FILE_SCAN covers table/file
        # sources; RANGE covers Range(...) sources (e.g. spark.range(...)).
        source_types = {OperatorType.FILE_SCAN}

        range_type = getattr(OperatorType, "RANGE", None)
        if range_type is not None:
            source_types.add(range_type)

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.FILTER:
                continue

            # The scan/source that feeds the filter is an upstream input,
            # i.e. one of the filter's `children`, not its `parents`.
            children = dag.children(operator.operator_id)

            has_source_child = any(
                child.operator_type in source_types for child in children
            )

            if not has_source_child:
                continue

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Early Filter / Filter Pushdown",
                    description=(
                        "The filter is applied immediately after the scan, "
                        "before any shuffle or join. This reduces the "
                        "volume of data carried through the rest of the "
                        "plan and is the expected, efficient placement for "
                        "this predicate."
                    ),
                    severity=Severity.LOW,
                    operator_id=operator.operator_id,
                    metadata={
                        "positive": True,
                        "category": "filter_pushdown",
                    },
                )
            )

        return findings

    def _detect_aqe(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.name != "AdaptiveSparkPlan":
                continue

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="AQE Enabled",
                    description=(
                        "Adaptive Query Execution is enabled, allowing "
                        "Spark to adjust shuffle partitions, join "
                        "strategies, and skew handling at runtime based on "
                        "observed data statistics."
                    ),
                    severity=Severity.LOW,
                    operator_id=operator.operator_id,
                    metadata={
                        "positive": True,
                        "category": "aqe_enabled",
                    },
                )
            )

        return findings