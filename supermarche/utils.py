"""Utility helpers and HTML builders used by the UI.

This module holds small pure helpers (HTML snippets, helper functions)
that are safe to import from multiple places.
"""
TH_STYLE = "text-align:left;padding:6px 12px;color:#bfefff;border-bottom:2px solid #123233;"
TD_STYLE = "padding:6px 12px;border-bottom:1px solid #122224;"

RESULT_WRAPPER_START = '<div style="font-family:Segoe UI, Roboto, Arial; color:#dff6f2;">'
RESULT_WRAPPER_END = '</div>'


def format_hour_range(start: int, length: int = 1) -> str:
    """Return an hour range string like '00h - 01h'.

    start: starting hour (0-23)
    length: number of hours covered by the range (default 1)
    """
    end = (start + length) % 24
    return f"{start:02d}h - {end:02d}h"

def _empty_result_html():
    return (
        '<div style="color:#9fb6c6;">'
        '<h3 style="color:#7be0ff;margin:6px 0;">Aucun résultat</h3>'
        '<p style="margin:0;">Cliquez sur <b>Résoudre</b> pour générer la planification et le graphique.</p>'
        '</div>'
    )


def _make_results_html(shift_list, total_cost, total_staff, peak_overload):
    """Return an HTML string summarizing the results (same structure as original file used)."""
    rows_html = ""
    grouped = {}
    for d, role, cnt in shift_list:
        grouped.setdefault(d, []).append((role, cnt))
    for d in sorted(grouped):
        parts = ", ".join(f"<b style='color:#eaf8ff'>{cnt}</b> {role}" for role, cnt in grouped[d])
        rows_html += f"<tr><td style='{TD_STYLE}'> {format_hour_range(d)} </td><td style='{TD_STYLE}'>{parts}</td></tr>"

    html = f"""
    <div style="font-family:Segoe UI, Roboto, Arial; color:#dff6f2;">
      <h3 style="color:#7be0ff;margin:4px 0;">Résultats optimaux</h3>
      <p style="color:#9fb6c6;margin:4px 0 10px 0;">Liste des shifts (début) et répartition par rôle :</p>
      <table style="width:100%; border-collapse:collapse; margin-bottom:12px;">
        <thead>
          <tr>
            <th style="{TH_STYLE}">Heure</th>
            <th style="{TH_STYLE}">Répartition</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
        <div style="color:#9fb6c6;">
          <div>Total staff-hours: <b style='color:#eaf8ff'>{total_staff}</b></div>
          <div>Peak overload (max surplus employees): <b style='color:#eaf8ff'>{peak_overload}</b></div>
        </div>
        <div style="background:linear-gradient(90deg,#16a085,#7be0ff); color:#FFFFFF; padding:8px 14px; border-radius:10px; font-weight:800; font-size:16px;">
          {total_cost:.2f} Dinars
        </div>
      </div>
    </div>
    """
    return html
