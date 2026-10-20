"""
Tenant dashboard view
Implements the profile-style experience requested by the product team.
"""
import flet as ft
from typing import Any, Dict, Optional, cast

from storage.db import (
    get_user_info,
    get_user_address,
    update_user_info,
    update_user_address,
    get_user_settings,
    update_user_settings,
    update_user_password,
)
from state.session_state import SessionState
from services.reservation_service import ReservationService
from components.navbar import RegisteredUserNavBar


class DatabaseManager:
    """Simple wrapper that combines SQL helpers with client storage for tenant metadata."""

    METADATA_KEY = "tenant_profile_meta"

    def __init__(self, page: ft.Page):
        self.page = page
        self.metadata = {}
        self._load_metadata()

    def _load_metadata(self):
        if self.page.client_storage.contains_key(self.METADATA_KEY):
            raw = self.page.client_storage.get(self.METADATA_KEY)
            if isinstance(raw, dict):
                self.metadata = raw
            else:
                self.metadata = {}
        else:
            self.metadata = {}
        self.metadata.setdefault("gender", "Unspecified")
        self.metadata.setdefault("avatar_url", "")

    def _persist_metadata(self):
        self.page.client_storage.set(self.METADATA_KEY, self.metadata)

    def _split_name(self, full_name: str) -> Dict[str, str]:
        parts = (full_name or "").strip().split()
        if not parts:
            return {"first": "", "last": ""}
        if len(parts) == 1:
            return {"first": parts[0], "last": ""}
        return {"first": parts[0], "last": parts[-1]}

    def _default_avatar(self, first_name: str, last_name: str) -> str:
        seed = "+".join(filter(None, [first_name, last_name])) or "CampusKubo"
        return f"https://ui-avatars.com/api/?name={seed}&background=0D8ABC&color=fff"

    def get_user_by_id(self, user_id: int) -> Dict[str, str]:
        user = get_user_info(user_id) or get_user_info(1) or {}
        names = self._split_name(user.get("full_name", ""))
        avatar = self.metadata.get("avatar_url") or self._default_avatar(names["first"], names["last"])

        return {
            "user_id": str(user.get("id") or user_id),
            "first_name": names["first"],
            "last_name": names["last"],
            "gender": self.metadata.get("gender", "Unspecified"),
            "email": user.get("email", ""),
            "phone": user.get("phone", ""),
            "avatar_url": avatar,
        }

    def update_user_profile(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        gender: str,
        email: str,
        phone: str,
        avatar_url: str,
    ) -> bool:
        full_name = " ".join(filter(None, [first_name.strip(), last_name.strip()])).strip()
        if not full_name:
            full_name = email or ""
        success = update_user_info(user_id, full_name, email, phone or None)
        self.metadata["gender"] = gender or self.metadata.get("gender", "Unspecified")
        if avatar_url:
            self.metadata["avatar_url"] = avatar_url
        self._persist_metadata()
        return success

    def update_avatar(self, user_id: int, avatar_url: str) -> bool:
        if not avatar_url:
            return False
        self.metadata["avatar_url"] = avatar_url
        self._persist_metadata()
        return True

    def get_user_address(self, user_id: int) -> Optional[Dict[str, str]]:
        return get_user_address(user_id)

    def get_saved_listings(self, user_id: int) -> list:
        try:
            from storage.db import get_saved_listings
            return get_saved_listings(user_id)
        except Exception:
            return []

    def update_user_address(self, user_id: int, house: str, street: str, barangay: str, city: str) -> bool:
        return update_user_address(user_id, house, street, barangay, city)

    def toggle_saved_listing(self, user_id: int, listing_id: int) -> bool:
        try:
            from storage.db import toggle_saved_listing
            return toggle_saved_listing(user_id, listing_id)
        except Exception:
            return False

    def get_user_settings(self, user_id: int) -> Optional[Dict[str, str]]:
        return get_user_settings(user_id)

    def update_user_settings(self, user_id: int, payload: Dict[str, object]) -> bool:
        return update_user_settings(user_id, payload)

    def update_user_password(self, user_id: int, new_password: str, current_password: Optional[str] = None) -> bool:
        return update_user_password(user_id, new_password, current_password)


class TenantDashboardState:
    """Keeps component state in sync with storage."""

    def __init__(self, page: ft.Page, db: DatabaseManager, user_id: int):
        self.page = page
        self.db = db
        self.user_id = user_id
        self.active_tab = "personal_info"
        self.notification_panel_open = False
        self.password = "••••••••••••••••"
        self.actual_password: Optional[str] = None
        self.password_visible = False
        self.reservation_service = ReservationService()
        self.reservations: list[dict] = []
        self.saved_listings: list[dict] = []
        self._load_user_data()
        self.load_address()
        self.load_settings()
        self.load_reservations()
        self.load_saved_listings()

    def _load_user_data(self):
        user = self.db.get_user_by_id(self.user_id)
        self.user_data = user
        self.first_name = user.get("first_name", "")
        self.last_name = user.get("last_name", "")
        self.gender = user.get("gender", "Unspecified")
        self.email = user.get("email", "")
        self.phone = user.get("phone", "")
        self.avatar_url = user.get("avatar_url")

    def refresh_profile(self):
        self._load_user_data()

    def load_address(self):
        addr = self.db.get_user_address(self.user_id)
        if addr:
            self.house_no = addr.get("house", "") or addr.get("house_no", "")
            self.street = addr.get("street", "")
            self.barangay = addr.get("barangay", "")
            self.city = addr.get("city", "")
        else:
            self.house_no = ""
            self.street = ""
            self.barangay = ""
            self.city = ""

    def load_settings(self):
        settings = self.db.get_user_settings(self.user_id) or {}
        self.popup_notifications = bool(settings.get("popup_notifications", True))
        self.chat_notifications = bool(settings.get("chat_notifications", True))
        self.email_notifications = bool(settings.get("email_notifications", True))
        self.notification_preferences = {
            "reservation_confirmation": bool(settings.get("reservation_confirmation_notif", True)),
            "cancellation": bool(settings.get("cancellation_notif", True)),
            "payment_update": bool(settings.get("payment_update_notif", True)),
            "rent_reminders": bool(settings.get("rent_reminders_notif", True)),
        }

    def load_reservations(self):
        raw = self.reservation_service.get_user_reservations(self.user_id)
        normalized = []
        for item in raw:
            try:
                normalized.append(dict(item))
            except Exception:
                normalized.append(item if isinstance(item, dict) else {})
        self.reservations = normalized

    def load_saved_listings(self):
        try:
            raw = self.db.get_saved_listings(self.user_id)
            self.saved_listings = [dict(item) if isinstance(item, dict) else item for item in raw]
        except Exception:
            self.saved_listings = []


class TenantDashboardView:
    """Tenant dashboard view implementation for the tenant-facing experience."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)

    def build(self):
        if not self.session.require_auth():
            return None

        page = self.page
        page_any = cast(Any, page)

        def show_snackbar(message: str, success: bool = True):
            page_any.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.GREEN if success else ft.Colors.RED)
            page_any.snack_bar.open = True
            page.update()
        user_id = self.session.get_user_id() or 1
        db_manager = DatabaseManager(page)
        state = TenantDashboardState(page, db_manager, user_id)

        def create_logo():
            return ft.Row(
                controls=[
                    ft.Text("c", size=24, weight=ft.FontWeight.BOLD, color="#2D2D2D"),
                    ft.Icon(ft.Icons.HOME, size=24, color="#A52A2A"),
                    ft.Text("mpusKubo", size=24, weight=ft.FontWeight.BOLD, color="#2D2D2D"),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        def create_info_field(label: str, value: object):
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(label, size=13, color=ft.Colors.GREY_600, italic=True),
                        ft.Text(str(value or ""), size=16, weight=ft.FontWeight.W_400, color=ft.Colors.BLACK),
                    ],
                    spacing=3,
                ),
                padding=ft.padding.only(bottom=15),
            )

        def refresh_profile_section():
            state.refresh_profile()
            refresh_content()

        def show_edit_profile_dialog(e=None):
            first_name_field = ft.TextField(label="First Name", value=state.first_name)
            last_name_field = ft.TextField(label="Last Name", value=state.last_name)
            gender_field = ft.Dropdown(
                label="Gender",
                value=state.gender,
                options=[
                    ft.dropdown.Option("Female"),
                    ft.dropdown.Option("Male"),
                    ft.dropdown.Option("Other"),
                    ft.dropdown.Option("Unspecified"),
                ],
            )
            email_field = ft.TextField(label="Email Address", value=state.email)
            phone_field = ft.TextField(label="Phone Number", value=state.phone)

            def save_profile(ev):
                updated_avatar = f"https://ui-avatars.com/api/?name={(first_name_field.value or state.first_name)}+{(last_name_field.value or state.last_name)}&size=110&background=4A90E2&color=fff&bold=true"
                success = state.db.update_user_profile(
                    state.user_id,
                    first_name_field.value or "",
                    last_name_field.value or "",
                    gender_field.value or "Unspecified",
                    email_field.value or "",
                    phone_field.value or "",
                    updated_avatar,
                )
                page.close(dialog)
                if success:
                    state.first_name = (first_name_field.value or state.first_name).strip() or state.first_name
                    state.last_name = (last_name_field.value or state.last_name).strip() or state.last_name
                    state.gender = gender_field.value or state.gender
                    state.email = (email_field.value or state.email).strip() or state.email
                    state.phone = (phone_field.value or state.phone).strip() or state.phone
                    state.avatar_url = updated_avatar
                    refresh_profile_section()
                    show_snackbar("Profile updated successfully!", success=True)
                else:
                    show_snackbar("Could not update profile.", success=False)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Edit Profile"),
                content=ft.Container(
                    content=ft.Column(
                        controls=[first_name_field, last_name_field, gender_field, email_field, phone_field],
                        tight=True,
                        spacing=15,
                    ),
                    width=400,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                    ft.ElevatedButton("Save", on_click=save_profile),
                ],
            )
            page.open(dialog)

        def show_change_avatar_dialog(e=None):
            file_picker = ft.FilePicker(on_result=lambda res: handle_avatar_upload(res))
            page.overlay.append(file_picker)
            page.update()
            preview_image = ft.Image(src=state.avatar_url, width=150, height=150, fit=ft.ImageFit.COVER, border_radius=10)

            def handle_avatar_upload(event: ft.FilePickerResultEvent):
                if event.files and len(event.files) > 0:
                    file = event.files[0]
                    state.avatar_url = file.path or state.avatar_url
                    preview_image.src = state.avatar_url
                    page.update()

            def pick_avatar(ev):
                file_picker.pick_files(
                    allowed_extensions=["png", "jpg", "jpeg", "gif"],
                    dialog_title="Choose Profile Picture",
                )

            def save_avatar(ev):
                state.db.update_avatar(state.user_id, state.avatar_url or "")
                page.close(dialog)
                refresh_profile_section()
                show_snackbar("Avatar updated successfully!", success=True)

            def remove_avatar(ev):
                state.avatar_url = state.db._default_avatar(state.first_name, state.last_name)
                preview_image.src = state.avatar_url
                page.update()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Change Profile Picture"),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(content=preview_image, alignment=ft.alignment.center),
                            ft.Container(height=20),
                            ft.ElevatedButton(
                                "Choose Photo",
                                icon=ft.Icons.UPLOAD_FILE,
                                on_click=pick_avatar,
                                width=200,
                            ),
                            ft.OutlinedButton(
                                "Remove Photo",
                                icon=ft.Icons.DELETE_OUTLINE,
                                on_click=remove_avatar,
                                width=200,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                        spacing=10,
                    ),
                    width=400,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                    ft.ElevatedButton("Save", on_click=save_avatar),
                ],
            )
            page.open(dialog)

        def show_edit_address_dialog(e=None):
            house_field = ft.TextField(label="House No.", value=state.house_no)
            street_field = ft.TextField(label="Street", value=state.street)
            barangay_field = ft.TextField(label="Barangay", value=state.barangay)
            city_field = ft.TextField(label="City/Municipality", value=state.city)

            def save_address(ev):
                success = state.db.update_user_address(
                    state.user_id,
                    house_field.value or "",
                    street_field.value or "",
                    barangay_field.value or "",
                    city_field.value or "",
                )
                page.close(dialog)
                if success:
                    state.house_no = (house_field.value or "").strip()
                    state.street = (street_field.value or "").strip()
                    state.barangay = (barangay_field.value or "").strip()
                    state.city = (city_field.value or "").strip()
                    refresh_content()
                    show_snackbar("Address updated successfully!", success=True)
                else:
                    show_snackbar("Could not update address.", success=False)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Edit Address"),
                content=ft.Container(
                    content=ft.Column(
                        controls=[house_field, street_field, barangay_field, city_field],
                        tight=True,
                        spacing=15,
                    ),
                    width=400,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                    ft.ElevatedButton("Save", on_click=save_address),
                ],
            )
            page.open(dialog)

        def show_change_password_dialog(e=None):
            def create_req_item(text: str):
                return ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=ft.Colors.GREY_500),
                        ft.Text(text, size=12, color=ft.Colors.GREY_500),
                    ],
                    spacing=5,
                )

            req_length = create_req_item("At least 8 characters")
            req_upper = create_req_item("One uppercase letter")
            req_number = create_req_item("One number")
            req_special = create_req_item("One special character (!@#$%^&*)")
            requirements_column = ft.Column(controls=[req_length, req_upper, req_number, req_special], spacing=2, visible=False)

            def validate_password_live(event):
                pwd = event.control.value or ""
                requirements_column.visible = True
                required_specials = "!@#$%^&*"

                def update_req(item, condition):
                    color = ft.Colors.GREEN if condition else ft.Colors.GREY_500
                    icon = ft.Icons.CHECK_CIRCLE if condition else ft.Icons.CHECK_CIRCLE_OUTLINED
                    item.controls[0].color = color
                    item.controls[0].name = icon
                    item.controls[1].color = color

                update_req(req_length, len(pwd) >= 8)
                update_req(req_upper, any(char.isupper() for char in pwd))
                update_req(req_number, any(char.isdigit() for char in pwd))
                update_req(req_special, any(char in required_specials for char in pwd))
                page.update()

            def toggle_password_view(event, text_field: ft.TextField):
                text_field.password = not text_field.password
                event.control.icon = ft.Icons.VISIBILITY_OFF if not text_field.password else ft.Icons.VISIBILITY
                text_field.update()

            current_password = ft.TextField(
                label="Current Password",
                password=True,
                suffix=ft.IconButton(ft.Icons.VISIBILITY, icon_size=18, on_click=lambda ev: toggle_password_view(ev, current_password)),
            )
            new_password = ft.TextField(
                label="New Password",
                password=True,
                on_change=validate_password_live,
                suffix=ft.IconButton(ft.Icons.VISIBILITY, icon_size=18, on_click=lambda ev: toggle_password_view(ev, new_password)),
            )
            confirm_password = ft.TextField(
                label="Confirm New Password",
                password=True,
                suffix=ft.IconButton(ft.Icons.VISIBILITY, icon_size=18, on_click=lambda ev: toggle_password_view(ev, confirm_password)),
            )

            def save_password(ev):
                current_pwd = (current_password.value or "").strip()
                new_pwd = (new_password.value or "").strip()
                confirm_pwd = (confirm_password.value or "").strip()

                # Validate current password is provided
                if not current_pwd:
                    show_snackbar("Please enter your current password.", success=False)
                    return

                # Validate passwords match
                if new_pwd != confirm_pwd:
                    show_snackbar("Passwords do not match!", success=False)
                    return

                # Validate password requirements
                required_specials = "!@#$%^&*"
                if (
                    len(new_pwd) < 8
                    or not any(c.isupper() for c in new_pwd)
                    or not any(c.isdigit() for c in new_pwd)
                    or not any(c in required_specials for c in new_pwd)
                ):
                    show_snackbar("Please ensure all password requirements are met.", success=False)
                    return

                # Call update_user_password with current password verification
                success = state.db.update_user_password(state.user_id, new_pwd, current_pwd)
                page.close(dialog)
                if success:
                    state.password = "•" * max(len(new_pwd), 10)
                    state.actual_password = new_pwd
                    state.password_visible = False
                    refresh_content()
                    show_snackbar("Password changed successfully!", success=True)
                else:
                    show_snackbar("Failed to update password. Please check your current password.", success=False)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Change Password"),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            current_password,
                            new_password,
                            ft.Container(content=requirements_column, padding=ft.padding.only(left=10)),
                            confirm_password,
                        ],
                        tight=True,
                        spacing=15,
                    ),
                    width=400,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                    ft.ElevatedButton("Change Password", on_click=save_password),
                ],
            )
            page.open(dialog)

        def get_profile_info():
            info_grid = ft.ResponsiveRow(
                controls=[
                    ft.Container(content=create_info_field("First Name", state.first_name), col={"xs": 12, "sm": 6, "md": 4}),
                    ft.Container(content=create_info_field("Last Name", state.last_name), col={"xs": 12, "sm": 6, "md": 4}),
                    ft.Container(content=create_info_field("Gender", state.gender), col={"xs": 12, "sm": 6, "md": 4}),
                    ft.Container(content=create_info_field("Email Address", state.email), col={"xs": 12, "sm": 6, "md": 4}),
                    ft.Container(content=create_info_field("Phone Number", state.phone), col={"xs": 12, "sm": 6, "md": 4}),
                ],
                spacing=20,
                run_spacing=20,
            )
            current_avatar = ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                ft.Image(src=state.avatar_url, width=110, height=110, fit=ft.ImageFit.COVER, border_radius=10),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CAMERA_ALT, size=30, color=ft.Colors.WHITE),
                                    alignment=ft.alignment.center,
                                    bgcolor="#80000000",
                                    border_radius=10,
                                    opacity=0,
                                ),
                            ]
                        ),
                        width=110,
                        height=110,
                        border=ft.border.all(2, ft.Colors.GREY_400),
                        border_radius=10,
                        alignment=ft.alignment.center,
                        on_click=lambda ev: show_change_avatar_dialog(ev),
                        ink=True,
                    ),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Text("Edit Profile", size=14),
                        padding=ft.padding.symmetric(horizontal=20, vertical=8),
                        border=ft.border.all(1, ft.Colors.BLACK),
                        border_radius=20,
                        on_click=lambda ev: show_edit_profile_dialog(ev),
                        ink=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            return ft.ResponsiveRow(
                controls=[
                    ft.Container(content=current_avatar, col={"xs": 12, "md": 3}, alignment=ft.alignment.top_center),
                    ft.Container(content=info_grid, col={"xs": 12, "md": 9}, padding=ft.padding.only(top=10)),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            )

        def get_account_settings():
            address_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Address", size=16, weight=ft.FontWeight.W_500),
                                ft.IconButton(
                                    icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
                                    icon_size=20,
                                    on_click=show_edit_address_dialog,
                                    style=ft.ButtonStyle(padding=0),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                        ft.Container(height=5),
                        ft.ResponsiveRow(
                            controls=[
                                ft.Column(
                                    controls=[ft.Text("House No.", size=12, italic=True, color=ft.Colors.GREY_500), ft.Text(state.house_no, size=14)],
                                    spacing=2,
                                    col={"xs": 6, "md": 3},
                                ),
                                ft.Column(
                                    controls=[ft.Text("Street", size=12, italic=True, color=ft.Colors.GREY_500), ft.Text(state.street, size=14)],
                                    spacing=2,
                                    col={"xs": 6, "md": 3},
                                ),
                                ft.Column(
                                    controls=[ft.Text("Barangay", size=12, italic=True, color=ft.Colors.GREY_500), ft.Text(state.barangay, size=14)],
                                    spacing=2,
                                    col={"xs": 6, "md": 3},
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("City/Municipality", size=12, italic=True, color=ft.Colors.GREY_500),
                                        ft.Text(state.city, size=14),
                                    ],
                                    spacing=2,
                                    col={"xs": 6, "md": 3},
                                ),
                            ],
                        ),
                    ],
                    spacing=5,
                ),
                padding=20,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=10,
                bgcolor=ft.Colors.WHITE,
            )

            def toggle_password_visibility(ev):
                state.password_visible = not state.password_visible
                refresh_content()

            password_display = (
                state.actual_password if state.password_visible and state.actual_password else state.password
            )
            password_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Password", size=16, weight=ft.FontWeight.W_500),
                                ft.IconButton(
                                    icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
                                    icon_size=20,
                                    on_click=show_change_password_dialog,
                                    style=ft.ButtonStyle(padding=0),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.LOCK, size=18, color=ft.Colors.BLACK),
                                    ft.Text(password_display, size=18, weight=ft.FontWeight.BOLD, offset=ft.Offset(0, 0.1)),
                                    ft.IconButton(
                                        icon=ft.Icons.VISIBILITY_OFF_OUTLINED if state.password_visible else ft.Icons.VISIBILITY_OUTLINED,
                                        icon_size=20,
                                        on_click=toggle_password_visibility,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            border=ft.border.all(1, ft.Colors.GREY_500),
                            border_radius=5,
                        ),
                    ],
                    spacing=5,
                ),
                padding=20,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=10,
                bgcolor=ft.Colors.WHITE,
            )

            def toggle_popup(ev):
                state.popup_notifications = ev.control.value
                update_settings()

            def toggle_chat(ev):
                state.chat_notifications = ev.control.value
                update_settings()

            def update_settings():
                payload: Dict[str, object] = {
                    "popup_notifications": state.popup_notifications,
                    "chat_notifications": state.chat_notifications,
                    "email_notifications": state.email_notifications,
                    "reservation_confirmation_notif": state.notification_preferences["reservation_confirmation"],
                    "cancellation_notif": state.notification_preferences["cancellation"],
                    "payment_update_notif": state.notification_preferences["payment_update"],
                    "rent_reminders_notif": state.notification_preferences["rent_reminders"],
                }
                success = state.db.update_user_settings(state.user_id, payload)
                if success:
                    show_snackbar("Notification settings saved.", success=True)
                else:
                    show_snackbar("Failed to save settings.", success=False)

            notifications_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(content=ft.Text("Notifications", size=16, weight=ft.FontWeight.W_500), padding=ft.padding.only(bottom=5)),
                        ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                        ft.Container(height=10),
                        ft.Row(
                            controls=[
                                ft.Text("Pop-up notifications", size=14),
                                ft.Switch(value=state.popup_notifications, active_color=ft.Colors.BLACK, on_change=toggle_popup),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("Turn on chat notifications", size=14),
                                ft.Switch(value=state.chat_notifications, active_color=ft.Colors.BLACK, on_change=toggle_chat),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=5,
                ),
                padding=20,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=10,
                bgcolor=ft.Colors.WHITE,
            )

            return ft.Column(
                controls=[
                    address_content,
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(content=password_content, col={"xs": 12, "md": 6}),
                            ft.Container(content=notifications_content, col={"xs": 12, "md": 6}),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=20,
            )

        STATUS_COLORS = {
            "pending": "#F0AD4E",
            "approved": "#4CAF50",
            "confirmed": "#1E88E5",
            "cancelled": "#E53935",
            "rejected": "#9E9E9E",
        }

        def refresh_reservations(ev=None):
            state.load_reservations()
            if state.active_tab == "reservations":
                refresh_content()

        def refresh_saved_listings(ev=None):
            state.load_saved_listings()
            if state.active_tab == "saved_listings":
                refresh_content()

        def show_reservation_detail_dialog(reservation: dict):
            status_key = (reservation.get("status") or "pending").lower()
            status_color = STATUS_COLORS.get(status_key, "#B0BEC5")

            def update_status(new_status: str):
                if new_status == status_key:
                    return
                success = state.reservation_service.update_reservation_status(reservation.get("id", 0), new_status)
                if success:
                    state.load_reservations()
                    refresh_content()
                    page.close(dialog)
                    message = f"Reservation marked as {new_status.capitalize()}"
                else:
                    message = "Failed to update reservation status."
                show_snackbar(message, success)

            def confirm_delete(ev):
                deleted = state.reservation_service.delete_reservation(reservation.get("id", 0))
                page.close(dialog)
                if deleted:
                    state.load_reservations()
                    refresh_content()
                    show_snackbar("Reservation deleted.")
                else:
                    show_snackbar("Unable to delete reservation.", success=False)

            def show_delete_confirmation(ev):
                confirm_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Delete Reservation"),
                    content=ft.Text("This action cannot be undone. Are you sure?"),
                    actions=[
                        ft.TextButton("Cancel", on_click=lambda _: page.close(confirm_dialog)),
                        ft.ElevatedButton("Delete", on_click=confirm_delete, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
                    ],
                )
                page.open(confirm_dialog)

            action_buttons = []
            if status_key != "confirmed":
                action_buttons.append(ft.ElevatedButton("Mark Confirmed", on_click=lambda ev: update_status("confirmed"), bgcolor=ft.Colors.GREEN))
            if status_key != "pending":
                action_buttons.append(ft.OutlinedButton("Set Pending", on_click=lambda ev: update_status("pending")))
            if status_key != "cancelled":
                action_buttons.append(ft.OutlinedButton("Cancel", on_click=lambda ev: update_status("cancelled"), style=ft.ButtonStyle(color=ft.Colors.RED)))
            action_buttons.append(ft.TextButton("Delete", on_click=show_delete_confirmation, style=ft.ButtonStyle(color=ft.Colors.RED)))

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    controls=[
                        ft.Text(reservation.get("address") or "Reservation Details", size=20, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: page.close(dialog)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color=ft.Colors.GREY_600),
                                    ft.Text(f"{reservation.get('start_date')} → {reservation.get('end_date')}"),
                                    ft.Container(expand=True),
                                    ft.Container(
                                        content=ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.CIRCLE, size=10, color=status_color),
                                                ft.Text(status_key.capitalize(), size=12, color=status_color),
                                            ],
                                            spacing=6,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        border_radius=12,
                                        border=ft.border.all(1, status_color),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Container(height=12),
                            ft.Text(f"Property: {reservation.get('address') or 'Untitled property'}", size=14),
                            ft.Text(f"Reservation ID: {reservation.get('id', '—')}", size=12, color=ft.Colors.GREY_600),
                            ft.Text(f"Created: {reservation.get('created_at', '')}", size=12, color=ft.Colors.GREY_500),
                        ],
                        spacing=10,
                    ),
                    width=500,
                ),
                actions=action_buttons,
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
            page.open(dialog)

        def get_reservations_section():
            header_row = ft.Row(
                controls=[
                    ft.Text("Reservations", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.TextButton("Refresh", on_click=refresh_reservations),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )

            if not state.reservations:
                return ft.Column(
                    controls=[
                        header_row,
                        ft.Container(height=10),
                        ft.Text("You have no reservations yet.", size=14, color=ft.Colors.GREY_600),
                    ],
                    spacing=10,
                )

            def build_card(reservation: dict):
                status_key = (reservation.get("status") or "pending").lower()
                badge_color = STATUS_COLORS.get(status_key, "#B0BEC5")
                price = reservation.get("price")
                price_text = f"₱{price:,.2f}" if isinstance(price, (int, float)) else "—"
                return ft.Container(
                    bgcolor="#FAFAFA",
                    padding=ft.padding.all(16),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(reservation.get("address") or "Untitled property", size=16, weight=ft.FontWeight.BOLD),
                                            ft.Row(
                                                controls=[
                                                    ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color=ft.Colors.GREY_600),
                                                    ft.Text(f"{reservation.get('start_date')} → {reservation.get('end_date')}", size=12, color=ft.Colors.GREY_600),
                                                ],
                                                spacing=6,
                                            ),
                                            ft.Text(f"{price_text}", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Container(
                                        content=ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.CIRCLE, size=10, color=badge_color),
                                                ft.Text(status_key.capitalize(), size=12, color=badge_color),
                                            ],
                                            spacing=6,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        border_radius=12,
                                        border=ft.border.all(1, badge_color),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Container(height=12),
                            ft.Row(
                                controls=[
                                    ft.Text(f"Reservation #{reservation.get('id', '—')}", size=12, color=ft.Colors.GREY_600),
                                    ft.Container(expand=True),
                                    ft.Text(f"Created {reservation.get('created_at', '')}", size=12, color=ft.Colors.GREY_500),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Container(height=10),
                            ft.Row(
                                controls=[
                                    ft.OutlinedButton("View Details", on_click=lambda ev, reservation=reservation: show_reservation_detail_dialog(reservation)),
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        spacing=12,
                    ),
                )

            reservation_cards = [build_card(reservation) for reservation in state.reservations]
            return ft.Column(
                controls=[header_row, ft.Column(controls=reservation_cards, spacing=12)],
                spacing=18,
            )

        def show_reserve_dialog(listing: dict):
            start_field = ft.TextField(label="Start Date (YYYY-MM-DD)")
            end_field = ft.TextField(label="End Date (YYYY-MM-DD)")

            def confirm(ev):
                start = (start_field.value or "").strip()
                end = (end_field.value or "").strip()
                listing_id_raw = listing.get("id") or listing.get("listing_id")
                try:
                    listing_id = int(listing_id_raw or 0)
                except Exception:
                    listing_id = 0
                if listing_id <= 0:
                    show_snackbar("Invalid listing selected.", success=False)
                    return
                ok, msg = state.reservation_service.create_new_reservation(listing_id, state.user_id, start, end)
                page.close(dlg)
                if ok:
                    state.load_reservations()
                    refresh_content()
                    show_snackbar(msg or "Reservation created.")
                else:
                    show_snackbar(msg or "Failed to create reservation", success=False)

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Reserve: {listing.get('address') or listing.get('title') or 'Listing'}"),
                content=ft.Container(content=ft.Column(controls=[start_field, end_field], spacing=8), width=420),
                actions=[ft.TextButton("Cancel", on_click=lambda _: page.close(dlg)), ft.ElevatedButton("Reserve", on_click=confirm)],
            )
            page.open(dlg)

        def get_saved_listings_section():
            header_row = ft.Row(
                controls=[
                    ft.Text("Saved Listings", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.TextButton("Refresh", on_click=refresh_saved_listings),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )

            if not state.saved_listings:
                return ft.Column(controls=[header_row, ft.Container(height=10), ft.Text("You have no saved listings.", size=14, color=ft.Colors.GREY_600)], spacing=10)

            def build_card(listing: dict):
                price = listing.get("price")
                price_text = f"₱{price:,.2f}" if isinstance(price, (int, float)) else "—"
                return ft.Container(
                    bgcolor="#FAFAFA",
                    padding=ft.padding.all(16),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column(controls=[
                                        ft.Text(listing.get("address") or listing.get("title") or "Untitled property", size=16, weight=ft.FontWeight.BOLD),
                                        ft.Text(listing.get("description") or "", size=13, color=ft.Colors.GREY_700),
                                        ft.Text(price_text, size=14, weight=ft.FontWeight.BOLD),
                                    ], spacing=6),
                                    ft.Container(expand=True),
                                    ft.Column(controls=[
                                        ft.ElevatedButton("Reserve", on_click=lambda ev, l=listing: show_reserve_dialog(l)),
                                        ft.OutlinedButton("Unsave", on_click=lambda ev, l=listing: (state.db.toggle_saved_listing(state.user_id, int(l.get('id') or l.get('listing_id') or 0)), refresh_saved_listings())),
                                    ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.END),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=12,
                    ),
                )

            cards = [build_card(l) for l in state.saved_listings]
            return ft.Column(controls=[header_row, ft.Column(controls=cards, spacing=12)], spacing=18)

        # Use the RegisteredUserNavBar component and add a 'Browse Listings' action for tenants
        extra_actions = [
            ft.ElevatedButton("Browse Listings", on_click=lambda e: page.go("/browse"))
        ]
        registered_nav = RegisteredUserNavBar(page, open_sidebar_callback=lambda e: None, brand_controls=[create_logo()], extra_actions=extra_actions, on_logout=lambda e: page.go("/logout"))
        header = ft.Container(
            bgcolor="#FFFFFF",
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#00000008", offset=ft.Offset(0, 2)),
            content=registered_nav.build(),
        )

        def switch_tab(tab_name: str):
            state.active_tab = tab_name
            refresh_content()

        def create_tab_button(label: str, tab_id: str):
            is_active = state.active_tab == tab_id
            return ft.Container(
                content=ft.Text(label, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL, color=ft.Colors.BLACK if is_active else ft.Colors.GREY_600),
                padding=ft.padding.symmetric(horizontal=25, vertical=12),
                border=ft.border.all(2, ft.Colors.BLACK) if is_active else None,
                border_radius=25,
                on_click=lambda ev: switch_tab(tab_id),
                ink=True,
            )

        tab_definitions = [
            ("Personal Info", "personal_info"),
            ("Account Settings", "account_settings"),
            ("Saved Listings", "saved_listings"),
            ("Reservations", "reservations"),
        ]

        tabs = ft.Row(
            controls=[
                *(create_tab_button(label, tab_id) for label, tab_id in tab_definitions),
            ],
            wrap=True,
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )
        content_area = ft.Column(spacing=20)
        main_scroll_area = ft.ListView(
            controls=[
                ft.Text("My Profile", size=40, weight=ft.FontWeight.BOLD),
                ft.Container(height=30),
                tabs,
                ft.Container(height=40),
                content_area,
            ],
            expand=True,
            spacing=0,
        )
        main_container = ft.Container(
            content=main_scroll_area,
            padding=ft.padding.symmetric(horizontal=20, vertical=30),
            bgcolor=ft.Colors.WHITE,
            expand=True,
        )

        def refresh_content():
            content_area.controls.clear()
            if state.active_tab == "personal_info":
                content_area.controls.extend([get_profile_info(), ft.Container(height=40)])
            elif state.active_tab == "account_settings":
                content_area.controls.append(get_account_settings())
            elif state.active_tab == "saved_listings":
                state.load_saved_listings()
                content_area.controls.append(get_saved_listings_section())
            elif state.active_tab == "reservations":
                state.load_reservations()
                content_area.controls.append(get_reservations_section())
            tabs.controls.clear()
            tabs.controls.extend([create_tab_button(label, tab_id) for label, tab_id in tab_definitions])
            page.update()

        def on_resize(event):
            width = page.width or 0
            is_small_screen = width < 800
            # RegisteredUserNavBar handles its own layout; adjust container padding and tabs alignment only
            if is_small_screen:
                main_container.padding = ft.padding.symmetric(horizontal=20, vertical=20)
                tabs.alignment = ft.MainAxisAlignment.CENTER
            else:
                main_container.padding = ft.padding.symmetric(horizontal=50, vertical=30)
                tabs.alignment = ft.MainAxisAlignment.START
            page.update()

        page.on_resized = on_resize
        refresh_content()
        on_resize(None)

        return ft.View(
            "/tenant",
            padding=ft.padding.all(0),
            bgcolor=ft.Colors.WHITE,
            controls=[ft.Column(controls=[header, main_container], spacing=0, expand=True)],
        )
