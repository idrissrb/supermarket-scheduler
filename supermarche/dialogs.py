"""Dialog classes extracted from the monolithic UI file.

Contains:
- RolesDialog
- StartDialog

These are pure PyQt dialog classes and only depend on Qt widgets.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout,
    QPushButton, QDialogButtonBox, QInputDialog, QMessageBox, QLabel,
    QLineEdit
)
from PyQt6.QtCore import Qt

# Attempt to import theme helper (same robust import used previously)
try:
    from theme import apply_dark_theme
except Exception:
    import sys, pathlib
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    try:
        from theme import apply_dark_theme
    except Exception:
        def apply_dark_theme(obj):
            return None


class RolesDialog(QDialog):
    """Dialog to add / remove / edit employee roles.

    Returns a dict: { role_name: {"cost": float, "critical": bool} }
    """
    def __init__(self, parent, roles):
        super().__init__(parent)
        self.setWindowTitle("Gérer les rôles")
        self.resize(420, 340)

        # deep-ish copy to avoid modifying original before OK
        self.roles = {r: dict(v) for r, v in roles.items()}

        layout = QVBoxLayout(self)
        self.listw = QListWidget()
        layout.addWidget(self.listw)

        self._refresh_list()

        btns_layout = QHBoxLayout()
        self.btn_add = QPushButton("Ajouter")
        self.btn_edit = QPushButton("Modifier coût")
        self.btn_toggle_critical = QPushButton("Critique / Non critique")
        self.btn_remove = QPushButton("Supprimer")

        btns_layout.addWidget(self.btn_add)
        btns_layout.addWidget(self.btn_edit)
        btns_layout.addWidget(self.btn_toggle_critical)
        btns_layout.addWidget(self.btn_remove)
        layout.addLayout(btns_layout)

        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(box)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit_cost)
        self.btn_toggle_critical.clicked.connect(self._on_toggle_critical)
        self.btn_remove.clicked.connect(self._on_remove)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)

    def _refresh_list(self):
        self.listw.clear()
        for role, data in sorted(self.roles.items()):
            crit = "✔ Critique" if data["critical"] else "✖ Non critique"
            it = QListWidgetItem(
                f"{role} — {data['cost']:.2f} Dinars/h — {crit}"
            )
            it.setData(Qt.ItemDataRole.UserRole, role)
            self.listw.addItem(it)

    def _on_add(self):
        name, ok = QInputDialog.getText(self, "Nouveau rôle", "Nom du rôle :")
        if not ok or not name.strip():
            return

        name = name.strip()
        if name in self.roles:
            QMessageBox.warning(self, "Erreur", "Rôle déjà existant.")
            return

        cost, ok = QInputDialog.getDouble(
            self, "Coût horaire",
            f"Coût pour '{name}' (Dinars/h) :",
            10.0, 0.0, 100000.0, decimals=2
        )
        if not ok:
            return

        critical = QMessageBox.question(
            self,
            "Rôle critique",
            f"Le rôle '{name}' est-il critique ?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes

        self.roles[name] = {
            "cost": float(cost),
            "critical": critical
        }
        self._refresh_list()

    def _on_edit_cost(self):
        it = self.listw.currentItem()
        if not it:
            return
        role = it.data(Qt.ItemDataRole.UserRole)

        cur = self.roles[role]["cost"]
        cost, ok = QInputDialog.getDouble(
            self,
            "Modifier coût",
            f"Coût horaire pour '{role}' (Dinars/h) :",
            float(cur), 0.0, 100000.0, decimals=2
        )
        if ok:
            self.roles[role]["cost"] = float(cost)
            self._refresh_list()

    def _on_toggle_critical(self):
        it = self.listw.currentItem()
        if not it:
            return
        role = it.data(Qt.ItemDataRole.UserRole)
        self.roles[role]["critical"] = not self.roles[role]["critical"]
        self._refresh_list()

    def _on_remove(self):
        it = self.listw.currentItem()
        if not it:
            return
        role = it.data(Qt.ItemDataRole.UserRole)

        resp = QMessageBox.question(
            self,
            "Supprimer",
            f"Supprimer le rôle '{role}' ?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.roles.pop(role, None)
            self._refresh_list()

    def get_roles(self):
        return {r: dict(v) for r, v in self.roles.items()}


class StartDialog(QDialog):
    """Initial configuration dialog (commerce name + roles).

    Returns (commerce_name, roles) where roles is a dict of role -> {cost, critical}.
    """
    def __init__(self, parent=None, commerce_name="Supermarché", roles=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration initiale")
        self.resize(520, 340)

        try:
            apply_dark_theme(self)
        except Exception:
            pass

        self._commerce_name = commerce_name
        self._roles = roles or {
            "vendeur": {"cost": 10.0, "critical": False},
            "caissier": {"cost": 11.0, "critical": False},
            "securite": {"cost": 9.0, "critical": True},
        }

        layout = QVBoxLayout(self)

        info = QLabel(
            "Définissez le nom du commerce et les rôles.\n"
            "Un rôle critique est requis à chaque heure."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Nom du commerce :"))
        self.name_edit = QLineEdit(self._commerce_name)
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        layout.addWidget(QLabel("Rôles définis :"))
        self.roles_list = QListWidget()
        layout.addWidget(self.roles_list)

        self._refresh_roles_list()

        btns_row = QHBoxLayout()
        self.btn_edit_roles = QPushButton("Gérer rôles...")
        self.btn_edit_roles.clicked.connect(self._open_roles_dialog)
        btns_row.addWidget(self.btn_edit_roles)
        btns_row.addStretch()
        layout.addLayout(btns_row)

        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

    def _refresh_roles_list(self):
        self.roles_list.clear()
        for role, data in sorted(self._roles.items()):
            crit = "✔ Critique" if data["critical"] else "✖ Non critique"
            it = QListWidgetItem(
                f"{role} — {data['cost']:.2f} Dinars/h — {crit}"
            )
            it.setData(Qt.ItemDataRole.UserRole, role)
            self.roles_list.addItem(it)

    def _open_roles_dialog(self):
        dlg = RolesDialog(self, self._roles)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_roles = dlg.get_roles()
            if not new_roles:
                QMessageBox.warning(self, "Rôles", "Il faut au moins un rôle.")
                return
            self._roles = new_roles
            self._refresh_roles_list()

    def accept(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Nom requis", "Entrez un nom pour le commerce.")
            return
        if not self._roles:
            QMessageBox.warning(self, "Rôles requis", "Définissez au moins un rôle.")
            return
        self._commerce_name = name
        super().accept()

    def get_values(self):
        return self._commerce_name, {r: dict(v) for r, v in self._roles.items()}
