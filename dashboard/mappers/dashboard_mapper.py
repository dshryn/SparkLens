from dashboard.models.dashboard_model import *


def to_dashboard_model(result):

    return DashboardModel(
        summary_cards=[],
        findings=[],
        recommendations=[],
        ai_summary=""
    )