"""
app/views/admin_settings_view.py

Admin Settings View - Manage system configuration and settings
"""

import flet as ft
from services.settings_service import SettingsService
from services.refresh_service import RefreshService
from models.settings import (
    AppSettings,
    SecuritySettings,
    PaymentSettings,
    ListingSettings,
    NotificationSettings,
    AdminSettings,
    FeatureFlags
)
from state.session_state import SessionState


class AdminSettingsView(ft.Column):
    """Admin view for managing system settings"""

    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

        # Initialize settings
        SettingsService.initialize()

        # UI State
        self.current_category = "app"
        self.unsaved_changes = {}
        self.settings_controls = {}

        # Register for refresh events
        RefreshService.register(self.name, self._on_global_refresh)

    def build(self):
        """Build the settings view"""
        return ft.Column([
            # Header
            ft.Container(
                content=ft.Text("⚙️ System Settings", size=24, weight="bold"),
                padding=20,
                bgcolor="#f0f0f0",
                border_radius=10,
            ),

            # Category tabs
            ft.Row([
                ft.ElevatedButton(
                    "App Settings",
                    on_click=lambda e: self._switch_category("app"),
                ),
                ft.ElevatedButton(
                    "Security",
                    on_click=lambda e: self._switch_category("security"),
                ),
                ft.ElevatedButton(
                    "Payments",
                    on_click=lambda e: self._switch_category("payment"),
                ),
                ft.ElevatedButton(
                    "Listings",
                    on_click=lambda e: self._switch_category("listing"),
                ),
                ft.ElevatedButton(
                    "Notifications",
                    on_click=lambda e: self._switch_category("notification"),
                ),
                ft.ElevatedButton(
                    "Admin",
                    on_click=lambda e: self._switch_category("admin"),
                ),
                ft.ElevatedButton(
                    "Features",
                    on_click=lambda e: self._switch_category("features"),
                ),
            ], scroll=ft.ScrollMode.AUTO),

            # Settings content area
            ft.Column([
                ft.Container(
                    content=ft.Column([], key="settings_content"),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, key="content_area"),

            # Action buttons
            ft.Row([
                ft.ElevatedButton(
                    "Save Changes",
                    icon=ft.icons.SAVE,
                    on_click=self._save_settings,
                    bgcolor="#4CAF50",
                    color="white",
                ),
                ft.ElevatedButton(
                    "Reset to Defaults",
                    icon=ft.icons.REFRESH,
                    on_click=self._reset_settings,
                    bgcolor="#FF9800",
                    color="white",
                ),
                ft.ElevatedButton(
                    "Export Settings",
                    icon=ft.icons.DOWNLOAD,
                    on_click=self._export_settings,
                    bgcolor="#2196F3",
                    color="white",
                ),
                ft.ElevatedButton(
                    "Import Settings",
                    icon=ft.icons.UPLOAD,
                    on_click=self._import_settings,
                    bgcolor="#2196F3",
                    color="white",
                ),
            ], spacing=10, padding=20),
        ], expand=True)

    def _switch_category(self, category: str) -> None:
        """Switch to a different settings category"""
        self.current_category = category
        self._render_category()

    def _render_category(self) -> None:
        """Render the current category's settings"""
        settings = SettingsService.get_settings()
        category_obj = getattr(settings, self.current_category, None)

        if not category_obj:
            self._show_snackbar("Invalid category", "error")
            return

        # Build form fields for this category
        fields = []
        category_dict = category_obj.to_dict()

        for key, value in category_dict.items():
            fields.append(self._build_setting_field(key, value))

        # Update the content area
        content_area = self.find_by_key("settings_content")
        if content_area:
            content_area.content = ft.Column(fields, spacing=10, scroll=ft.ScrollMode.AUTO)
            self.update()

    def _build_setting_field(self, key: str, value) -> ft.Control:
        """Build an input field for a setting"""
        control_key = f"{self.current_category}_{key}"

        # Determine field type based on value
        if isinstance(value, bool):
            # Checkbox for boolean
            control = ft.Checkbox(
                label=key.replace('_', ' ').title(),
                value=value,
                on_change=lambda e: self._track_change(control_key, e.control.value),
            )
        elif isinstance(value, int):
            # Number field for integers
            control = ft.TextField(
                label=key.replace('_', ' ').title(),
                value=str(value),
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e: self._track_change(control_key, e.control.value),
            )
        elif isinstance(value, float):
            # Number field for floats
            control = ft.TextField(
                label=key.replace('_', ' ').title(),
                value=str(value),
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e: self._track_change(control_key, e.control.value),
            )
        elif isinstance(value, list):
            # Text area for lists (JSON)
            control = ft.TextField(
                label=key.replace('_', ' ').title(),
                value=str(value),
                multiline=True,
                on_change=lambda e: self._track_change(control_key, e.control.value),
            )
        else:
            # Text field for strings
            control = ft.TextField(
                label=key.replace('_', ' ').title(),
                value=str(value),
                on_change=lambda e: self._track_change(control_key, e.control.value),
            )

        self.settings_controls[control_key] = (control, key, type(value))
        return control

    def _track_change(self, control_key: str, value) -> None:
        """Track a setting change"""
        self.unsaved_changes[control_key] = value

    def _save_settings(self, e) -> None:
        """Save all unsaved changes"""
        if not self.unsaved_changes:
            self._show_snackbar("No changes to save", "info")
            return

        # Build updates dictionary
        updates = {}
        for control_key, value in self.unsaved_changes.items():
            category, key = control_key.rsplit('_', 1)
            if category not in updates:
                updates[category] = {}

            # Convert value to correct type
            if control_key in self.settings_controls:
                _, _, original_type = self.settings_controls[control_key]
                try:
                    if original_type == bool:
                        updates[category][key] = value if isinstance(value, bool) else value == "True"
                    elif original_type == int:
                        updates[category][key] = int(value)
                    elif original_type == float:
                        updates[category][key] = float(value)
                    elif original_type == list:
                        import json
                        updates[category][key] = json.loads(value)
                    else:
                        updates[category][key] = value
                except (ValueError, TypeError) as ex:
                    self._show_snackbar(f"Error converting {key}: {str(ex)}", "error")
                    return

        # Save to service
        success, message = SettingsService.update_settings(updates)

        if success:
            self._show_snackbar(message, "success")
            self.unsaved_changes = {}
            RefreshService.notify_refresh()
        else:
            self._show_snackbar(message, "error")

    def _reset_settings(self, e) -> None:
        """Reset all settings to defaults"""
        def confirm_reset(dialog_result):
            if dialog_result:
                success, message = SettingsService.reset_to_defaults()
                if success:
                    self._show_snackbar(message, "success")
                    self.unsaved_changes = {}
                    self._render_category()
                    RefreshService.notify_refresh()
                else:
                    self._show_snackbar(message, "error")

        # Show confirmation dialog
        dialog = ft.AlertDialog(
            title=ft.Text("Reset to Defaults?"),
            content=ft.Text("This will reset all settings to their default values. This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda d: (d.close(), confirm_reset(False))),
                ft.TextButton("Reset", on_click=lambda d: (d.close(), confirm_reset(True))),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _export_settings(self, e) -> None:
        """Export settings to JSON file"""
        import json
        from datetime import datetime

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campuskubo_settings_{timestamp}.json"
        filepath = f"app/storage/data/{filename}"

        success, message = SettingsService.export_settings(filepath)
        if success:
            self._show_snackbar(f"Settings exported to {filename}", "success")
        else:
            self._show_snackbar(message, "error")

    def _import_settings(self, e) -> None:
        """Import settings from JSON file"""
        # This would typically open a file picker dialog
        # For now, show a message about how to import
        self._show_snackbar(
            "Place JSON file in app/storage/data/ and use CLI to import",
            "info"
        )

    def _show_snackbar(self, message: str, message_type: str = "info") -> None:
        """Show a snackbar message"""
        colors = {
            "success": "#4CAF50",
            "error": "#F44336",
            "info": "#2196F3",
            "warning": "#FF9800",
        }

        snackbar = ft.SnackBar(
            ft.Text(message),
            bgcolor=colors.get(message_type, "#2196F3"),
        )
        self.page.open(snackbar)
        self.page.update()

    def _on_global_refresh(self) -> None:
        """Handle global refresh event"""
        SettingsService.reload_from_database()
        self._render_category()
