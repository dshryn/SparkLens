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

    DAG direction:
        dag.children(op) returns upstream/input operators that feed op.
        dag.parents(op) returns downstream operators that consume op.
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

        findings.extend(
            self._detect_required_shuffles(
                dag,
                parents,
            )
        )

        findings.extend(
            self._detect_two_phase_aggregation(dag)
        )

        findings.extend(
            self._detect_filter_pushdown(
                dag,
                parents,
            )
        )

        findings.extend(
            self._detect_aqe(dag)
        )

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_parent_map(
        dag: ExecutionDAG,
    ) -> dict[int, list[int]]:

        parents: dict[int, list[int]] = {
            operator_id: []
            for operator_id in dag.operators
        }

        for operator in dag.operators.values():

            for child in dag.children(
                operator.operator_id
            ):

                parents.setdefault(
                    child.operator_id,
                    [],
                ).append(
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

            children = dag.children(
                operator.operator_id
            )

            parent_ids = parents.get(
                operator.operator_id,
                [],
            )

            parent_ops: list[PhysicalOperator] = [
                parent_op
                for parent_id in parent_ids
                if (
                    parent_op := dag.get_operator(parent_id)
                ) is not None
            ]

            # ----------------------------------------------------------
            # Required shuffle for two-phase aggregation
            #
            # Structural evidence:
            #
            #   Final Aggregate
            #          |
            #       Exchange
            #          |
            #   Partial Aggregate
            #
            # No Photon-specific finalmerge_/merge_ text is required.
            # ----------------------------------------------------------

            if (
                self._feeds_final_aggregation(
                    dag,
                    operator,
                    parent_ops,
                )
                and self._preceded_by_partial_aggregation(
                    children
                )
            ):

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
                            "category": (
                                "required_shuffle_aggregation"
                            ),
                            "required": True,
                            "required_operator_id": (
                                operator.operator_id
                            ),
                        },
                    )
                )

                continue

            # ----------------------------------------------------------
            # Required shuffle for shuffle-based joins
            # ----------------------------------------------------------

            if self._feeds_shuffle_join(dag, operator):

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
                            "required_operator_id": (
                                operator.operator_id
                            ),
                        },
                    )
                )

        return findings

    def _feeds_final_aggregation(
        self,
        dag: ExecutionDAG,
        exchange: PhysicalOperator,
        parent_ops: list[PhysicalOperator],
    ) -> bool:
        """
        Determines whether the Exchange feeds a final/merge aggregation.

        Structural evidence is preferred over textual markers.

        An aggregation is considered the final side of a two-phase pattern
        when the Exchange is one of its upstream children and that Exchange
        is itself fed by a partial aggregation.
        """

        if not parent_ops:
            return False

        if not self._preceded_by_partial_aggregation(
            dag.children(exchange.operator_id)
        ):
            return False

        return any(
            parent.operator_type in self._AGG_TYPES
            for parent in parent_ops
        )

    @staticmethod
    def _preceded_by_partial_aggregation(
        children: list[PhysicalOperator],
    ) -> bool:
        """
        Returns True when an upstream child is an aggregation.

        The aggregation immediately upstream of an Exchange is treated as
        the partial/map-side aggregation in a two-phase aggregation pattern.
        Explicit phase text is used when available, but structural placement
        is sufficient when the parser does not preserve that text.
        """

        for child in children:
            if child.operator_type not in (
                ExecutionQualityRule._AGG_TYPES
            ):
                continue

            arguments = " ".join(
                child.arguments
            ).lower()

            if "partial_" in arguments:
                return True

            # Structural fallback:
            # this aggregation is immediately upstream of the Exchange.
            return True

        return False

    def _feeds_shuffle_join(
        self,
        dag: ExecutionDAG,
        exchange: PhysicalOperator,
    ) -> bool:
        """
        True when the Exchange ultimately feeds a shuffle-based join.
        SortMergeJoin does not consume the Exchange directly: its inputs are
        Sort operators sitting on top of the Exchange (and, in AQE plans,
        shuffle-read wrappers), so walk up through those.
        """

        visited: set[int] = set()
        frontier = list(dag.parents(exchange.operator_id))

        while frontier:

            current = frontier.pop()

            if current.operator_id in visited:
                continue

            visited.add(current.operator_id)

            if current.operator_type in self._SHUFFLE_JOIN_TYPES:
                return True

            if self._is_pass_through(current):
                frontier.extend(
                    dag.parents(current.operator_id)
                )

        return False

    @staticmethod
    def _is_pass_through(operator: PhysicalOperator) -> bool:

        if operator.operator_type == OperatorType.SORT:
            return True

        name = operator.name.lower()

        return operator.operator_type == OperatorType.UNKNOWN and (
            "shuffleread" in name or "shufflequerystage" in name
        )

    def _detect_two_phase_aggregation(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        # Find the pattern structurally through an Exchange.
        #
        # Final Aggregate
        #       |
        #    Exchange
        #       |
        # Partial Aggregate
        #
        # This works for both vanilla Spark and Photon plan text.

        for exchange in dag.operators.values():

            if exchange.operator_type != OperatorType.EXCHANGE:
                continue

            upstream = dag.children(
                exchange.operator_id
            )

            downstream = dag.parents(
                exchange.operator_id
            )

            partial_ops = [
                operator
                for operator in upstream
                if (
                    operator.operator_type
                    in self._AGG_TYPES
                    and self._is_partial_aggregation(operator)
                )
            ]

            final_ops = [
                operator
                for operator in downstream
                if operator.operator_type in self._AGG_TYPES
            ]

            if not partial_ops or not final_ops:
                continue

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Two-Phase Aggregation",
                    description=(
                        "Spark performs a partial (map-side) aggregation "
                        "followed by a final aggregation across the "
                        "shuffle boundary. This reduces the volume of data "
                        "shuffled and is the expected, efficient strategy "
                        "for this aggregation."
                    ),
                    severity=Severity.LOW,
                    operator_id=partial_ops[0].operator_id,
                    metadata={
                        "positive": True,
                        "category": "two_phase_aggregation",
                        "partial_operator_id": (
                            partial_ops[0].operator_id
                        ),
                        "final_operator_id": (
                            final_ops[0].operator_id
                        ),
                        "exchange_operator_id": (
                            exchange.operator_id
                        ),
                    },
                )
            )

            # A single Exchange should produce one two-phase finding.
            break

        return findings

    @staticmethod
    def _is_partial_aggregation(
        operator: PhysicalOperator,
    ) -> bool:
        """
        Determines whether an aggregation is the partial side of a
        two-phase aggregation pattern.

        Explicit phase text is preferred when available. The caller uses
        this helper only for an aggregation immediately upstream of an
        Exchange, so structural placement is the fallback.
        """

        if operator.operator_type not in (
            ExecutionQualityRule._AGG_TYPES
        ):
            return False

        arguments = " ".join(
            operator.arguments
        ).lower()

        if "partial_" in arguments:
            return True

        # Structural fallback. The caller has already established that
        # this aggregation is immediately upstream of an Exchange.
        return True
    
    
    def _detect_filter_pushdown(
        self,
        dag: ExecutionDAG,
        parents: dict[int, list[int]],
    ) -> list[AnalysisFinding]:

        # FILE_SCAN is the normal table/file source.
        source_types = {
            OperatorType.FILE_SCAN
        }

        # RANGE is not currently present in OperatorType in the retrieved
        # repository, but preserve compatibility if it is added later.
        range_type = getattr(
            OperatorType,
            "RANGE",
            None,
        )

        if range_type is not None:
            source_types.add(range_type)

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.FILTER:
                continue

            children = dag.children(
                operator.operator_id
            )

            has_source_child = any(
                child.operator_type in source_types
                for child in children
            )

            # Parser currently classifies Range as UNKNOWN. When that is the
            # case, identify it structurally by the source operator name.
            has_range_source = any(
                child.name.lower().startswith("range")
                for child in children
            )

            if not (
                has_source_child
                or has_range_source
            ):
                continue

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Early Filter / Filter Pushdown",
                    description=(
                        "The filter is applied immediately after the scan "
                        "or source, before any shuffle or join."
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