import sys
from supermarche.dialogs import RolesDialog, StartDialog
from supermarche.solver import solve_schedule
from supermarche.utils import _make_results_html, _empty_result_html, TH_STYLE, TD_STYLE, format_hour_range

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QTextEdit,
    QHBoxLayout, QSpinBox, QGroupBox, QFormLayout, QGridLayout, QSizePolicy,
    QSpacerItem, QInputDialog, QMessageBox, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox
)
from PyQt6.QtWidgets import QFileDialog
import csv
from datetime import datetime
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt

# Matplotlib QtAgg for PyQt6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mtick
import numpy as np
 
# Theme helper import (try to be robust about module path)
try:
    from theme import apply_dark_theme
except Exception:
    import sys, pathlib
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    from theme import apply_dark_theme

"""
Use refactored dialogs and helpers from the `supermarche` package.
"""

        


class FenetrePrincipale(QWidget):
    def __init__(self, commerce_name=None, roles=None):
        super().__init__()

        # commerce name and roles (start with provided or defaults)
        self.commerce_name = commerce_name or "Supermarché"
        self.roles = dict(roles or {"vendeur": 10.0, "caissier": 11.0, "securite": 9.0})

        # base demand used to prefill the demand table (kept for sensible defaults)
        self.base_demande = {
            7:  {"vendeur": 3, "caissier": 2, "securite": 1},
            8:  {"vendeur": 4, "caissier": 3, "securite": 1},
            9:  {"vendeur": 5, "caissier": 4, "securite": 1},
            10: {"vendeur": 6, "caissier": 5, "securite": 1},
            11: {"vendeur": 6, "caissier": 5, "securite": 1},
            12: {"vendeur": 7, "caissier": 6, "securite": 2},
            13: {"vendeur": 7, "caissier": 6, "securite": 2},
            14: {"vendeur": 6, "caissier": 5, "securite": 2},
            15: {"vendeur": 6, "caissier": 5, "securite": 2},
            16: {"vendeur": 7, "caissier": 6, "securite": 2},
            17: {"vendeur": 8, "caissier": 7, "securite": 2},
            18: {"vendeur": 9, "caissier": 8, "securite": 2},
            19: {"vendeur": 8, "caissier": 7, "securite": 2},
            20: {"vendeur": 6, "caissier": 5, "securite": 2},
            21: {"vendeur": 4, "caissier": 3, "securite": 1},
        }
        
        self.setWindowTitle(f"Planification du personnel - {self.commerce_name}")
        self.setMinimumSize(980, 640)

        # store scenarios in-memory
        self.scenarios = {}  # name -> scenario dict
        self.last_results = None  # populated after resoudre()

        # Hover/annotation state
        self._hover_cid = None
        self._annot = None
        self._hover_ax = None
        self._hover_data = None  # (heures_arr, totals, per_hour_role)

        # apply shared theme
        try:
            apply_dark_theme(self)
        except Exception:
            pass

        # Title area
        title_layout = QVBoxLayout()
        self.title_label = QLabel(f"{self.commerce_name} — Planification des quarts")
        self.title_label.setObjectName("mainTitle")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Optimisez le nombre d'employés et visualisez clairement l'effectif horaire")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(subtitle)

        # Left: inputs (costs + actions)
        grp_couts = QGroupBox("Coûts horaires")
        # keep form as attribute so we can rebuild rows when roles change
        self.form_couts = QFormLayout()
        self.form_couts.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        grp_couts.setLayout(self.form_couts)
        # constrain left column width so it's visually smaller than right
        grp_couts.setMaximumWidth(520)

        # role spin widgets map
        self.role_spins = {}
        self._build_roles_ui()  # populate with initial roles

        # Constraints group (demand table, shift length, min security, opening/closing)
        grp_constraints = QGroupBox("Contraintes")
        c_layout = QVBoxLayout()

        # opening / closing controls
        hours_row = QHBoxLayout()
        hours_row.addWidget(QLabel("Heure d'ouverture :"))
        self.opening_spin = QSpinBox()
        self.opening_spin.setRange(0, 23)
        self.opening_spin.setValue(7)
        hours_row.addWidget(self.opening_spin)

        hours_row.addSpacing(12)
        hours_row.addWidget(QLabel("Heure de fermeture :"))
        self.closing_spin = QSpinBox()
        self.closing_spin.setRange(1, 24)
        self.closing_spin.setValue(22)
        hours_row.addWidget(self.closing_spin)
        hours_row.addStretch()
        c_layout.addLayout(hours_row)

        # heures list derived from opening/closing (rows are opening..closing-1)
        self.heures = list(range(self.opening_spin.value(), self.closing_spin.value()))

        # demand table: rows = opening..closing-1, cols = current roles
        self.table_demande = QTableWidget(len(self.heures), len(self.roles))
        self.table_demande.setHorizontalHeaderLabels([r.capitalize() for r in self.roles.keys()])
        self._fill_demande_table_with_defaults()
        c_layout.addWidget(QLabel("Demande par heure (double‑clic pour éditer) :"))
        c_layout.addWidget(self.table_demande)

        # Make table expand horizontally but fixed vertically to show all rows without scroll
        # Allow the table to expand vertically and show a vertical scrollbar when content exceeds available space.
        self.table_demande.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table_demande.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table_demande.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # keep row/column sizes updated, but don't force a fixed maximum height so scrollbar can appear
        self.table_demande.resizeColumnsToContents()
        self.table_demande.resizeRowsToContents()
        self._adjust_demande_table_height()

        # connect opening/closing changes
        self.opening_spin.valueChanged.connect(self._on_hours_changed)
        self.closing_spin.valueChanged.connect(self._on_hours_changed)

        # shift length selector
        shift_row = QHBoxLayout()
        shift_row.addWidget(QLabel("Longueur de shift :"))
        self.shift_combo = QComboBox()
        for v in ("6", "8", "10"):
            self.shift_combo.addItem(f"{v}h", int(v))
        self.shift_combo.setCurrentIndex(1)  # default 8h
        shift_row.addWidget(self.shift_combo)
        shift_row.addStretch()
        c_layout.addLayout(shift_row)

        # Temps minimum de repos
        # Temps minimum de repos
        self.spin_repos = QSpinBox()
        self.spin_repos.setRange(0, 24)
        self.spin_repos.setValue(8)
        self.spin_repos.setSuffix(" h")

        repos_layout = QHBoxLayout()
        repos_layout.addWidget(QLabel("Temps minimum de repos :"))
        repos_layout.addWidget(self.spin_repos)

        c_layout.addLayout(repos_layout)


        # minimum security spinbox
        sec_row = QHBoxLayout()
        sec_row.addWidget(QLabel("Nombre minimum d’employés critiques : "))
        self.min_security_spin = QSpinBox()
        self.min_security_spin.setRange(0, 100)
        self.min_security_spin.setValue(1)
        sec_row.addWidget(self.min_security_spin)
        sec_row.addStretch()
        c_layout.addLayout(sec_row)

        # update demand table automatically when minimum critical staff changes
        self.min_security_spin.valueChanged.connect(self._on_min_security_changed)

        grp_constraints.setLayout(c_layout)
        grp_constraints.setMaximumWidth(520)  # make constraints area visibly larger

        # Actions group
        grp_actions = QGroupBox("Actions")
        # Use a compact grid (2 columns) so buttons wrap naturally and do not overlap
        actions_grid = QGridLayout()
        actions_grid.setHorizontalSpacing(8)
        actions_grid.setVerticalSpacing(8)
        actions_grid.setContentsMargins(6, 6, 6, 6)

        self.bouton = QPushButton("Résoudre")
        self.bouton.setObjectName("primary")
        self.bouton.clicked.connect(self.resoudre)

        self.bouton_clear = QPushButton("Effacer")
        self.bouton_clear.setObjectName("secondary")
        self.bouton_clear.clicked.connect(self.zone_resultat_clear)

        self.bouton_save = QPushButton("Sauvegarder scénario")
        self.bouton_save.clicked.connect(self.save_scenario)
        self.bouton_compare = QPushButton("Comparer scénarios")
        self.bouton_compare.clicked.connect(self.compare_scenarios)

        # place buttons in a 2x2 grid (management buttons removed from page 2)
        actions_grid.addWidget(self.bouton, 0, 0)
        actions_grid.addWidget(self.bouton_clear, 0, 1)
        actions_grid.addWidget(self.bouton_save, 1, 0)
        actions_grid.addWidget(self.bouton_compare, 1, 1)

        # Make buttons expand to fill their grid cell but avoid huge minimum widths.
        all_buttons = [self.bouton, self.bouton_clear, self.bouton_save, self.bouton_compare]
        for b in all_buttons:
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setMinimumHeight(36)
            # allow horizontal shrinking but keep readable text; avoid large fixed min widths
            b.setMinimumWidth(100)

        grp_actions.setLayout(actions_grid)
        # keep left column visibly smaller than the graph area
        grp_actions.setMaximumWidth(520)

        left_col = QVBoxLayout()
        left_col.addWidget(grp_couts)
        left_col.addWidget(grp_constraints)
        left_col.addWidget(grp_actions)
        left_col.addStretch()

        # Make left groups expand vertically so the left column's bottom aligns
        # with the right column (graph + résultats). Set proportional stretches:
        # costs (small), contraintes (dominant), actions (secondary).
        # Indices: 0 = grp_couts, 1 = grp_constraints, 2 = grp_actions, 3 = stretch
        left_col.setStretch(0, 1)
        left_col.setStretch(1, 3)
        left_col.setStretch(2, 2)

        # Allow the constraints and actions group boxes to expand vertically
        grp_constraints.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grp_actions.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Right: graph + results (no table)
        grp_graph = QGroupBox("Graphique - Effectif total par heure")
        vbox_graph = QVBoxLayout()
        self.figure = Figure(figsize=(6, 3), dpi=100, facecolor="#0f1720")
        self.canvas = FigureCanvas(self.figure)
        vbox_graph.addWidget(self.canvas)
        grp_graph.setLayout(vbox_graph)

        # Results display: improved, HTML-styled
        grp_resultats = QGroupBox("Détails - Résultats")
        vbox_result = QVBoxLayout()
        self.zone_resultat = QTextEdit()
        self.zone_resultat.setReadOnly(True)
        # Use HTML to make the results clearer and more attractive
        self.zone_resultat.setAcceptRichText(True)
        vbox_result.addWidget(self.zone_resultat)
        # Add export CSV button below results
        self.btn_export_csv = QPushButton("Exporter CSV")
        self.btn_export_csv.clicked.connect(self._export_results_csv)
        vbox_result.addWidget(self.btn_export_csv)
        grp_resultats.setLayout(vbox_result)

        right_col = QVBoxLayout()
        right_col.addWidget(grp_graph, stretch=3)
        right_col.addWidget(grp_resultats, stretch=2)

        # Assemble main grid
        main_grid = QGridLayout()
        main_grid.addLayout(left_col, 0, 0)
        main_grid.addLayout(right_col, 0, 1)
        # make right column larger than left (left small, right dominant)
        main_grid.setColumnStretch(0, 2)
        main_grid.setColumnStretch(1, 5)
        main_grid.setHorizontalSpacing(20)
        main_grid.setVerticalSpacing(10)

        # Footer / status
        self.status = QLabel("Prêt")
        self.status.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status.setStyleSheet("color: #9fb6c6; font-size: 11px; padding: 6px;")

        # Compose final layout
        layout = QVBoxLayout()
        layout.addLayout(title_layout)
        layout.addSpacing(8)
        layout.addLayout(main_grid)
        layout.addWidget(self.status)
        layout.setContentsMargins(12, 12, 12, 12)
        self.setLayout(layout)

        # Prepare empty plot and empty text
        self._init_empty_plot()
        self.zone_resultat.setHtml(_empty_result_html())

    def _fill_demande_table_with_defaults(self):
        """Populate the demande table using current self.heures and self.roles with base_demande defaults."""
        self.table_demande.setRowCount(len(self.heures))
        self.table_demande.setColumnCount(len(self.roles))
        self.table_demande.setHorizontalHeaderLabels([r.capitalize() for r in self.roles.keys()])
        self.table_demande.setVerticalHeaderLabels([format_hour_range(h) for h in self.heures])
        for ri, h in enumerate(self.heures):
            for ci, role in enumerate(self.roles.keys()):
                val = int(self.base_demande.get(h, {}).get(role, 0))
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_demande.setItem(ri, ci, item)
        self.table_demande.resizeColumnsToContents()
        self.table_demande.resizeRowsToContents()

    def _adjust_demande_table_height(self):
        """Adjust the table minimum height so the header and a few rows are visible; allow scrolling for the rest."""
        self.table_demande.resizeRowsToContents()
        header_h = self.table_demande.horizontalHeader().height()
        rows_h = sum(self.table_demande.rowHeight(i) for i in range(self.table_demande.rowCount()))
        frame = 2 * self.table_demande.frameWidth()
        margin = 12
        total_h = header_h + rows_h + frame + margin
        # set a reasonable minimum so header + a few rows are visible,
        # but do NOT set a strict maximum: let the widget expand and show a scrollbar when needed.
        min_visible = min(total_h, 320)
        self.table_demande.setMinimumHeight(min_visible)
        # ensure the widget can still grow with layout (no maximum enforced)
        try:
            self.table_demande.setMaximumHeight(16777215)  # Qt default "no limit"
        except Exception:
            pass

    def _on_hours_changed(self):
        """Handle opening/closing hour updates and rebuild the demande table rows."""
        opening = int(self.opening_spin.value())
        closing = int(self.closing_spin.value())
        if closing <= opening:
            QMessageBox.warning(self, "Heures invalides", "L'heure de fermeture doit être strictement supérieure à l'heure d'ouverture.")
            # revert to previous sensible values
            self.opening_spin.blockSignals(True)
            self.closing_spin.blockSignals(True)
            self.opening_spin.setValue(7)
            self.closing_spin.setValue(22)
            self.opening_spin.blockSignals(False)
            self.closing_spin.blockSignals(False)
            opening = 7
            closing = 22

        # update heures and preserve existing table values where possible
        old_values = {}
        for ri in range(self.table_demande.rowCount()):
            for ci in range(self.table_demande.columnCount()):
                item = self.table_demande.item(ri, ci)
                if item:
                    old_values[(ri, ci)] = item.text()

        self.heures = list(range(opening, closing))
        # rebuild table with same number of columns (roles) and new rows
        cols = list(self.roles.keys())
        prev_row_count = len(old_values) and self.table_demande.rowCount() or 0
        self.table_demande.setRowCount(len(self.heures))
        self.table_demande.setVerticalHeaderLabels([format_hour_range(h) for h in self.heures])
        for ri, h in enumerate(self.heures):
            for ci, role in enumerate(cols):
                # try to keep value from old_values if same row index existed; else use base_demande
                prev = None
                if (ri, ci) in old_values:
                    try:
                        prev = int(old_values[(ri, ci)])
                    except Exception:
                        prev = None
                if prev is None:
                    prev = int(self.base_demande.get(h, {}).get(role, 0))
                itm = QTableWidgetItem(str(prev))
                itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_demande.setItem(ri, ci, itm)

        self.table_demande.resizeColumnsToContents()
        self.table_demande.resizeRowsToContents()
        self._adjust_demande_table_height()

    def _on_min_security_changed(self, value: int):
        """Ensure the demande table has at least `value` entries for every critical role each hour.

        This updates the table cells in-place (increasing values when needed). It does not
        decrease any existing user-set values.
        """
        try:
            min_sec = int(value)
        except Exception:
            return

        if min_sec <= 0:
            return

        # find critical role column indices
        cols = list(self.roles.keys())
        critical_cols = [i for i, r in enumerate(cols) if self.roles.get(r, {}).get("critical", False)]
        if not critical_cols:
            return

        # for each row(hour) and each critical role column, set value = max(existing, min_sec)
        for ri in range(self.table_demande.rowCount()):
            for ci in critical_cols:
                it = self.table_demande.item(ri, ci)
                cur = 0
                if it:
                    try:
                        cur = int(float(it.text()))
                    except Exception:
                        cur = 0
                if cur < min_sec:
                    new_it = QTableWidgetItem(str(min_sec))
                    new_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_demande.setItem(ri, ci, new_it)
        # keep visuals updated
        self.table_demande.resizeRowsToContents()
        self._adjust_demande_table_height()

    def _rebuild_demande_table_columns(self):
        """Rebuild demand table columns when roles change."""
        cols = list(self.roles.keys())
        # keep current values where possible
        current = {}
        for ri in range(self.table_demande.rowCount()):
            for ci in range(self.table_demande.columnCount()):
                it = self.table_demande.item(ri, ci)
                if it:
                    current[(ri, ci)] = it.text()

        self.table_demande.clear()
        self.table_demande.setColumnCount(len(cols))
        self.table_demande.setHorizontalHeaderLabels([r.capitalize() for r in cols])
        # ensure row count matches heures
        self.table_demande.setRowCount(len(self.heures))
        self.table_demande.setVerticalHeaderLabels([format_hour_range(h) for h in self.heures])
        for ri, h in enumerate(self.heures):
            for ci, role in enumerate(cols):
                prev = None
                if (ri, ci) in current:
                    try:
                        prev = int(current[(ri, ci)])
                    except Exception:
                        prev = None
                if prev is None:
                    prev = int(self.base_demande.get(h, {}).get(role, 0))
                itm = QTableWidgetItem(str(prev))
                itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_demande.setItem(ri, ci, itm)
        self.table_demande.resizeColumnsToContents()
        self.table_demande.resizeRowsToContents()
        self._adjust_demande_table_height()

    def _read_demande_from_table(self):
        """Return demande dict[h][role] from the table (integers)."""
        types = list(self.roles.keys())
        demande = {}
        for ri, h in enumerate(self.heures):
            demande[h] = {}
            for ci, role in enumerate(types):
                item = self.table_demande.item(ri, ci)
                val = 0
                if item:
                    try:
                        val = int(float(item.text()))
                    except Exception:
                        val = 0
                demande[h][role] = max(0, val)
        return demande

    def _build_roles_ui(self):
        # clear existing rows
        # remove widgets from form layout
        while self.form_couts.count():
            item = self.form_couts.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.role_spins = {}
        for role, data in self.roles.items():
            cost = data["cost"]              
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 100000.0)
            spin.setDecimals(2)
            spin.setValue(float(cost))
            spin.setSuffix(" Dinars/h")

            # keep spin values synced to self.roles (float)
            spin.valueChanged.connect(lambda val, r=role: self._role_cost_changed(r, val))
            label = QLabel(role.capitalize())
            self.form_couts.addRow(label, spin)
            self.role_spins[role] = spin

        # if constraints table exists, rebuild its columns to match new roles
        if hasattr(self, "table_demande"):
            self._rebuild_demande_table_columns()

    def _role_cost_changed(self, role, value):
        # update roles dict when spin changes
        self.roles[role] = float(value)

    def edit_commerce_name(self):
        name, ok = QInputDialog.getText(self, "Modifier nom du commerce", "Nom du commerce:", text=self.commerce_name)
        if not ok or not name.strip():
            return
        self.commerce_name = name.strip()
        self.title_label.setText(f"{self.commerce_name} — Planification des quarts")
        self.setWindowTitle(f"Planification du personnel - {self.commerce_name}")

    def manage_roles(self):
        dlg = RolesDialog(self, self.roles)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_roles = dlg.get_roles()
            # ensure at least one role remains
            if not new_roles:
                QMessageBox.warning(self, "Rôles", "Il faut au moins un rôle.")
                return
            self.roles = new_roles
            self._build_roles_ui()
            self.status.setText("Rôles mis à jour")

    # empty result HTML moved to supermarche.utils._empty_result_html

    def _init_empty_plot(self):
        # disconnect any hover handler when clearing
        self._disconnect_hover()
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor="#0f1720")
        ax.text(0.5, 0.5, "Aucun résultat\ncliquez sur 'Résoudre'", ha='center', va='center',
                fontsize=12, color="#7f9da6", alpha=0.9)
        ax.set_xticks([])
        ax.set_yticks([])
        self.figure.tight_layout()
        self.canvas.draw()

    def zone_resultat_clear(self):
        self.zone_resultat.clear()
        self.zone_resultat.setHtml(_empty_result_html())
        self._init_empty_plot()
        self.status.setText("Effacé - prêt")
        # don't remove saved scenarios


    def resoudre(self):
        self.zone_resultat.clear()
        self.status.setText("Résolution en cours...")
        QApplication.processEvents()

        # read dynamic inputs
        types = list(self.roles.keys())
        heures = list(self.heures)  # dynamic opening..closing-1
        # read shift length from selector and compute possible start times
        L = int(self.shift_combo.currentData() or 8)
        last_start = (self.closing_spin.value()) - L  # inclusive start hour max such that shift covers up to closing-1
        if last_start < self.opening_spin.value():
            QMessageBox.warning(self, "Contraintes incompatibles", "La longueur de shift est trop grande pour les heures d'ouverture.")
            self.status.setText("Contraintes invalides")
            return
        debut_shifts = list(range(self.opening_spin.value(), last_start + 1))

        # demande read from demand table (user editable)
        demande = self._read_demande_from_table()

        # costs
        cout = {r: float(self.role_spins[r].value()) if r in self.role_spins else float(self.roles[r]) for r in types}

        # Delegate to the solver module which encapsulates Gurobi model building
        min_sec = int(self.min_security_spin.value())
        try:
            results = solve_schedule(debut_shifts, heures, types, demande, cout, L, self.roles, min_sec)
        except RuntimeError as e:
            # model infeasible
            self.status.setText("Modèle infaisable")
            QMessageBox.warning(self, "Infaisable", str(e))
            return

        # unpack solver results
        total_par_heure = results.get("total_par_heure", [])
        shift_list = results.get("shift_list", [])
        total_cost = results.get("total_cost", 0.0)
        per_hour_role = results.get("per_hour_role", {})
        total_staff = results.get("total_staff", 0)
        peak_overload = results.get("peak_overload", 0)

        # total_cost is provided by solver results
        # total_cost = float(getattr(model, "objVal", 0.0))

        # compute comparison metrics
        demand_total = [sum(demande[h].values()) for h in heures]
        total_staff = int(sum(total_par_heure))  # staff-hours
        peak_overload = int(max(0, max((tp - dt) for tp, dt in zip(total_par_heure, demand_total))))

        # store last results for saving
        self.last_results = {
            "total_par_heure": total_par_heure,
            "shift_list": shift_list,
            "total_cost": total_cost,
            "total_staff": total_staff,
            "peak_overload": peak_overload,
            "per_hour_role": per_hour_role,
            "params": {"cout": cout, "L": L, "roles": dict(self.roles), "commerce_name": self.commerce_name,
                       "demande": demande, "min_security": min_sec}
        }

        # Update results text with styled HTML
        self.zone_resultat.setHtml(_make_results_html(shift_list, total_cost, total_staff, peak_overload))

        # Update embedded plot - annotate exact counts above each point
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor="#0f1720")
        heures_arr = np.array(heures)
        totals = np.array(total_par_heure)

        # nicer line + markers + filled area
        ax.plot(heures_arr, totals, marker='o', color='#16a085', linewidth=2.2, markersize=8)
        ax.fill_between(heures_arr, totals, color='#145b4f', alpha=0.25)

        # annotate each point with the exact integer count (static small labels)
        for xpt, ypt in zip(heures_arr, totals):
            ax.annotate(str(int(ypt)),
                        xy=(xpt, ypt),
                        xytext=(0, 8),
                        textcoords='offset points',
                        ha='center',
                        va='bottom',
                        fontsize=9,
                        fontweight='700',
                        color='#eafaf6',
                        bbox=dict(boxstyle="round,pad=0.2", fc="#0a2421", ec="#123233", alpha=0.9))

        ax.set_xlabel("Heure", fontsize=10, color="#cfeff6")
        ax.set_ylabel("Total employés", fontsize=10, color="#cfeff6")
        ax.set_xticks(heures_arr)
        ax.set_xticklabels([f"{h}h" for h in heures_arr], rotation=0, fontsize=9, color="#9fb6c6")
        ax.yaxis.set_major_locator(mtick.MaxNLocator(integer=True))
        ax.tick_params(colors="#9fb6c6")
        ax.grid(axis='y', linestyle='--', alpha=0.25, color="#122226")
        ax.set_title(f"{self.commerce_name} — Effectif total par heure (valeurs exactes affichées)", fontsize=11, weight='700', color="#9fe9ff")
        self.figure.tight_layout()
        self.canvas.draw()

        # connect hover - show per-role breakdown on mouse hover
        self._disconnect_hover()
        self._connect_hover(ax, heures_arr, totals, per_hour_role)

        self.status.setText("Résolution terminée")

    # Scenario feature methods
    def save_scenario(self):
        if not self.last_results:
            QMessageBox.warning(self, "Pas de résultat", "Aucun résultat à sauvegarder. Lancez 'Résoudre' d'abord.")
            return
        name, ok = QInputDialog.getText(self, "Nom du scénario", "Entrez un nom pour le scénario :")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self.scenarios:
            resp = QMessageBox.question(self, "Remplacer ?", f"Le scénario '{name}' existe déjà. Remplacer ?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp != QMessageBox.StandardButton.Yes:
                return
        # store a lightweight snapshot
        snap = {
            "params": self.last_results.get("params", {}),
            "total_cost": self.last_results["total_cost"],
            "total_staff": self.last_results["total_staff"],
            "peak_overload": self.last_results["peak_overload"],
            "total_par_heure": self.last_results["total_par_heure"],
            "shift_list": self.last_results["shift_list"],
            "per_hour_role": self.last_results.get("per_hour_role", {}),
            "roles": dict(self.roles),
            "commerce_name": self.commerce_name
        }
        self.scenarios[name] = snap
        QMessageBox.information(self, "Scénario sauvegardé", f"Scénario '{name}' enregistré.")

    def _export_results_csv(self):
        """Export the last_results to a CSV file chosen by the user."""
        if not self.last_results:
            QMessageBox.warning(self, "Pas de résultat", "Aucun résultat à exporter. Lancez 'Résoudre' d'abord.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer résultats", filter="CSV files (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # en-tête résumé avec horodatage d'export
                writer.writerow([f"Date d'exportation : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([f"Commerce : {self.last_results.get('params', {}).get('commerce_name', self.commerce_name)}"])
                writer.writerow([f"Longueur du shift (L) : {self.last_results.get('params', {}).get('L', '')}"])
                writer.writerow([f"Coût total : {self.last_results.get('total_cost', 0.0):.2f}"])
                writer.writerow([f"Total heures-personnel : {self.last_results.get('total_staff', 0)}"])
                writer.writerow([f"Pic de surcharge : {self.last_results.get('peak_overload', 0)}"])
                writer.writerow([])

                # section quarts
                writer.writerow(["Quarts (heure_de_début, rôle, nombre)"])
                writer.writerow(["heure_de_début", "rôle", "nombre"])
                for d, r, cnt in sorted(self.last_results.get('shift_list', [])):
                    writer.writerow([d, r, cnt])
                writer.writerow([])

                # répartition par heure
                writer.writerow(["Répartition par heure"])
                types = list(self.roles.keys())
                header = ["heure", "total"] + types
                writer.writerow(header)
                total_par_heure = self.last_results.get('total_par_heure', [])
                per_hour_role = self.last_results.get('per_hour_role', {})
                heures = list(per_hour_role.keys())
                for i, h in enumerate(sorted(heures)):
                    row = [h]
                    row.append(total_par_heure[i] if i < len(total_par_heure) else "")
                    for t in types:
                        row.append(per_hour_role.get(h, {}).get(t, 0))
                    writer.writerow(row)

            QMessageBox.information(self, "Exporté", f"Résultats exportés vers {path}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible d'écrire le fichier : {e}")

    def compare_scenarios(self):
        if len(self.scenarios) < 2:
            QMessageBox.information(self, "Comparer scénarios", "Sauvegardez au moins 2 scénarios pour comparer.")
            return
        # Build comparison table (HTML)
        names = list(self.scenarios.keys())
        rows = ""
        costs = []
        staffs = []
        overloads = []
        for n in names:
            s = self.scenarios[n]
            costs.append(s["total_cost"])
            staffs.append(s["total_staff"])
            overloads.append(s["peak_overload"])

        # determine best (min) for cost, staff, overload
        best_cost = min(costs)
        best_staff = min(staffs)
        best_overload = min(overloads)

        for n in names:
            s = self.scenarios[n]
            cost = s["total_cost"]
            staff = s["total_staff"]
            over = s["peak_overload"]
            cost_cell = f"<td style='padding:6px 12px;{'background:#163c36;' if cost==best_cost else ''}'> {cost:.2f} € </td>"
            staff_cell = f"<td style='padding:6px 12px;{'background:#163c36;' if staff==best_staff else ''}'> {staff} </td>"
            over_cell = f"<td style='padding:6px 12px;{'background:#163c36;' if over==best_overload else ''}'> {over} </td>"
            rows += f"<tr><td style='padding:6px 12px;border-bottom:1px solid #122224;'>{n}</td>{cost_cell}{staff_cell}{over_cell}</tr>"

        summary_html = f"""
        <div style="font-family:Segoe UI, Roboto, Arial; color:#dff6f2;">
          <h3 style="color:#7be0ff;margin:4px 0;">Comparaison des scénarios</h3>
          <p style="color:#9fb6c6;margin:4px 0 10px 0;">Métriques : coût total (Dinars), total staff-hours, peak overload (max surplus)</p>
          <table style="width:100%; border-collapse:collapse; margin-bottom:12px;">
            <thead>
              <tr>
                <th style="text-align:left;padding:6px 12px;color:#bfefff;border-bottom:2px solid #123233;">Scénario</th>
                <th style="text-align:left;padding:6px 12px;color:#bfefff;border-bottom:2px solid #123233;">Coût total</th>
                <th style="text-align:left;padding:6px 12px;color:#bfefff;border-bottom:2px solid #123233;">Total staff-hours</th>
                <th style="text-align:left;padding:6px 12px;color:#bfefff;border-bottom:2px solid #123233;">Peak overload</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
          <p style="color:#9fb6c6;margin:0;">Les cellules sombres indiquent la meilleure valeur (min).</p>
        </div>
        """

        # show in dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Comparaison des scénarios")
        dlg_layout = QVBoxLayout(dlg)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setAcceptRichText(True)
        te.setHtml(summary_html)
        dlg_layout.addWidget(te)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dlg.accept)
        dlg_layout.addWidget(buttons)
        dlg.resize(700, 400)
        dlg.exec()

    # Hover support methods
    def _connect_hover(self, ax, heures_arr, totals, per_hour_role):
        """
        Connect a motion_notify_event handler to show breakdown when hovering near a point.
        """
        self._hover_ax = ax
        self._hover_data = (np.asarray(heures_arr), np.asarray(totals), per_hour_role)

        # create annotation if not exists
        if self._annot is None:
            self._annot = ax.annotate(
                "",
                xy=(0,0),
                xytext=(20,20),
                textcoords="offset points",
                bbox=dict(boxstyle="round", fc="#021414", ec="#145b4f", alpha=0.95),
                fontsize=9,
                color="#eafaf6",
                visible=False
            )

        # connect if not already
        if self._hover_cid is None:
            self._hover_cid = self.canvas.mpl_connect("motion_notify_event", self._on_motion)

    def _disconnect_hover(self):
        if self._hover_cid is not None:
            try:
                self.canvas.mpl_disconnect(self._hover_cid)
            except Exception:
                pass
        self._hover_cid = None
        # hide annotation
        if self._annot is not None:
            try:
                self._annot.set_visible(False)
            except Exception:
                pass
        self._hover_ax = None
        self._hover_data = None
        # redraw to remove leftover annotation
        try:
            self.canvas.draw_idle()
        except Exception:
            pass

    def _on_motion(self, event):
        # event.x, event.y are display coords; event.inaxes indicates current axes
        if event.inaxes is None or self._hover_data is None:
            if self._annot is not None and self._annot.get_visible():
                self._annot.set_visible(False)
                self.canvas.draw_idle()
            return

        ax = event.inaxes
        if ax != self._hover_ax:
            return

        heures_arr, totals, per_hour_role = self._hover_data
        # compute display coords for data points
        trans = ax.transData.transform
        data_xy = np.column_stack((heures_arr, totals))
        disp_xy = trans(data_xy)  # Nx2 array of pixel coords
        ex, ey = event.x, event.y
        # compute distances in pixels
        dists = np.hypot(disp_xy[:,0] - ex, disp_xy[:,1] - ey)
        idx = int(np.argmin(dists))
        # threshold in pixels for hover activation
        if dists[idx] < 12:
            hour = int(heures_arr[idx])
            total = int(totals[idx])
            role_counts = per_hour_role.get(hour, {})
            # build plain-text tooltip (no HTML) with dynamic roles
            lines = [f"{hour}h — total: {total}"]
            for r in sorted(self.roles.keys()):
                cnt = role_counts.get(r, 0)
                lines.append(f"{r.capitalize():10}: {cnt}")
            txt = "\n".join(lines)
            # show annotation at the data point
            self._annot.xy = (heures_arr[idx], totals[idx])
            self._annot.set_text(txt)
            # style bbox / text for better readability
            bbox = self._annot.get_bbox_patch()
            bbox.set_alpha(0.95)
            bbox.set_facecolor("#021414")
            bbox.set_edgecolor("#145b4f")
            self._annot.set_visible(True)
            self.canvas.draw_idle()
        else:
            if self._annot is not None and self._annot.get_visible():
                self._annot.set_visible(False)
                self.canvas.draw_idle()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply global theme to the application so the very first dialog uses it
    try:
        apply_dark_theme(app)
    except Exception:
        # fall back silently if theme application fails
        pass

    # show initial configuration dialog (commerce name + roles)
    start = StartDialog()
    if start.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    commerce_name, roles = start.get_values()

    fenetre = FenetrePrincipale(commerce_name=commerce_name, roles=roles)
    fenetre.show()
    sys.exit(app.exec())
