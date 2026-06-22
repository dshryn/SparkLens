"""Builds visualization models from execution DAGs."""

from visualization.models import GraphEdge, GraphModel, GraphNode
from models.analysis_report import AnalysisReport
from models.enums import Severity
from models.execution_dag import ExecutionDAG


class GraphBuilder:
    """Converts an ExecutionDAG into a GraphModel."""

    def build(
        self,
        dag: ExecutionDAG,
        report: AnalysisReport,
    ) -> GraphModel:

        severities = self._collect_severities(report)

        nodes = []

        for operator in dag.operators.values():
            severity = severities.get(operator.operator_id)

            nodes.append(
                GraphNode(
                    id=operator.operator_id,
                    label=operator.name,
                    operator_type=operator.operator_type,
                    severity=severity,
                    highlighted=severity is not None,
                )
            )

        edges = [
            GraphEdge(
                source=edge.parent_id,
                target=edge.child_id,
            )
            for edge in dag.edges
        ]

        return GraphModel(
            nodes=nodes,
            edges=edges,
        )

    def _collect_severities(
        self,
        report: AnalysisReport,
    ) -> dict[int, Severity]:
        """
        Returns the highest severity for each operator.
        """

        severities = {}

        priority = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }

        for finding in report.findings:

            if finding.operator_id is None:
                continue

            current = severities.get(finding.operator_id)

            if (
                current is None
                or priority[finding.severity] > priority[current]
            ):
                severities[finding.operator_id] = finding.severity

        return severities