"""Small package exposing modules for the supermarket planner."""
from .dialogs import RolesDialog, StartDialog
from .solver import solve_schedule
from .utils import _make_results_html, _empty_result_html

__all__ = ["RolesDialog", "StartDialog", "solve_schedule", "_make_results_html", "_empty_result_html"]
