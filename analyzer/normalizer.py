from __future__ import annotations

import re


class PlanNormalizer:
    """
    Normalizes vendor-specific Spark execution plans into a
    canonical representation understood by SparkLens.
    """

    _PHOTON_PREFIX = re.compile(r"\bPhoton")

    def normalize(self, plan: str) -> str:
        """
        Normalize a formatted Spark execution plan.

        Parameters
        ----------
        plan:
            Raw output from DataFrame.explain(mode="formatted")

        Returns
        -------
        str
            Canonical execution plan.
        """

        lines = []

        for line in plan.splitlines():

            if line.startswith("== Photon Explanation =="):
                break

            line = self._PHOTON_PREFIX.sub("", line)

            lines.append(line.rstrip())

        return "\n".join(lines).strip()