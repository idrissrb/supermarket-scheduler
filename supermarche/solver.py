"""Solver helper that builds and solves the Gurobi model.

This module contains a single function `solve_schedule` which encapsulates the
Gurobi model creation and returns a results dict similar to what the UI expects.
"""
import gurobipy as gp
from gurobipy import GRB

def solve_schedule(debut_shifts, heures, types, demande, cout, L, roles, min_security):
    """Build and solve the schedule model.

    Parameters:
      debut_shifts: list of possible shift start hours
      heures: list of hours to cover
      types: list of role names
      demande: dict[h][role] -> int demand
      cout: dict role -> hourly cost (float)
      L: shift length (int)
      roles: dict role -> {.., 'critical': bool}
      min_security: int minimum critical staff per hour

    Returns:
      dict with keys: total_par_heure (list), shift_list (list of (d,role,count)),
      total_cost (float), per_hour_role (dict), total_staff (int), peak_overload (int)

    Raises:
      Exception on solver errors.
    """
    model = gp.Model("Planification_Supermarche")
    x = model.addVars(debut_shifts, types, vtype=GRB.INTEGER, lb=0)

    model.setObjective(
        gp.quicksum(L * cout[t] * x[d, t] for d in debut_shifts for t in types),
        GRB.MINIMIZE
    )

    # demand constraints
    for h in heures:
        for t in types:
            model.addConstr(
                gp.quicksum(
                    x[d, t]
                    for d in debut_shifts
                    if d <= h < d + L
                ) >= demande.get(h, {}).get(t, 0)
            )

    # critical roles
    # Enforce the minimum number of critical employees PER CRITICAL ROLE per hour.
    # For each critical role r and each hour h, ensure the staff of role r covering h >= min_security.
    critical_roles = [r for r, data in roles.items() if data.get("critical", False)]
    # If user asked for a minimum number of critical employees, ensure
    # that at each hour the TOTAL number of critical-role employees >= min_security.
    if critical_roles and min_security > 0:
        for h in heures:
            model.addConstr(
                gp.quicksum(
                    x[d, r]
                    for d in debut_shifts
                    for r in critical_roles
                    if d <= h < d + L
                ) >= min_security
            )

    model.optimize()

    if model.status == GRB.Status.INFEASIBLE:
        raise RuntimeError("Model infeasible")

    total_par_heure = []
    per_hour_role = {h: {t: 0 for t in types} for h in heures}

    for h in heures:
        total = 0
        for d in debut_shifts:
            for t in types:
                val = int(getattr(x[d, t], 'x', 0) or 0)
                if d <= h < d + L:
                    total += val
                    per_hour_role[h][t] += val
        total_par_heure.append(total)

    shift_list = []
    for d in debut_shifts:
        for t in types:
            val = int(getattr(x[d, t], 'x', 0) or 0)
            if val > 0:
                shift_list.append((d, t, val))

    total_cost = float(getattr(model, 'objVal', 0.0) or 0.0)
    demand_total = [sum(demande[h].values()) for h in heures]
    total_staff = int(sum(total_par_heure))
    peak_overload = int(max(0, max((tp - dt) for tp, dt in zip(total_par_heure, demand_total))))

    return {
        'total_par_heure': total_par_heure,
        'shift_list': shift_list,
        'total_cost': total_cost,
        'per_hour_role': per_hour_role,
        'total_staff': total_staff,
        'peak_overload': peak_overload,
    }
