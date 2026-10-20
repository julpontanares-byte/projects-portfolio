# components/password_requirements.py
"""
Password requirements validation display component
"""
import flet as ft


class PasswordRequirements:
    """Displays password validation requirements with visual feedback"""

    def __init__(self, page_or_password: str | None = None, password: str = ""):
        # Accept either (password) or (page, password) for backward compatibility
        if hasattr(page_or_password, "session"):
            # signature: (page, password)
            self.password = password
        else:
            self.password = page_or_password or password
        self.requirements = [
            {"name": "length", "label": "At least 8 characters", "met": False},
            {"name": "uppercase", "label": "One uppercase letter", "met": False},
            {"name": "digit", "label": "One number", "met": False},
            {"name": "special", "label": "One special character (!@#$%^&*)", "met": False},
        ]
        self.update_requirements(password)

    def update_requirements(self, password: str) -> None:
        """Update requirement status based on password input"""
        self.password = password
        self.requirements[0]["met"] = len(password) >= 8
        self.requirements[1]["met"] = any(c.isupper() for c in password)
        self.requirements[2]["met"] = any(c.isdigit() for c in password)
        self.requirements[3]["met"] = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    def get_all_met(self) -> bool:
        """Check if all requirements are met"""
        return all(req["met"] for req in self.requirements)

    def build(self) -> ft.Container:
        """Build password requirements display"""
        req_controls = []

        for req in self.requirements:
            icon = ft.Icon(
                ft.Icons.CHECK_CIRCLE,
                color="#4CAF50" if req["met"] else "#CCCCCC",
                size=20
            )
            text = ft.Text(
                req["label"],
                color="#4CAF50" if req["met"] else "#CCCCCC",
                size=12,
            )

            req_controls.append(
                ft.Row(
                    spacing=8,
                    controls=[icon, text]
                )
            )

        return ft.Container(
            padding=12,
            bgcolor="#F5F5F5",
            border_radius=8,
            content=ft.Column(
                spacing=6,
                controls=req_controls
            )
        )

    def build_inline(self) -> ft.Row:
        """Build compact inline requirements display (for alerts/snackbars)"""
        req_controls = []

        for req in self.requirements:
            icon_name = ft.Icons.CHECK_CIRCLE if req["met"] else ft.Icons.RADIO_BUTTON_UNCHECKED
            icon = ft.Icon(
                icon_name,
                color="#4CAF50" if req["met"] else "#999999",
                size=16
            )
            req_controls.append(icon)

        return ft.Row(
            spacing=4,
            controls=req_controls
        )
