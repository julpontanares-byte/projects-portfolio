import flet as ft
from types import SimpleNamespace
from services.user_service import UserService
import sys


class ProfileSection:
    """Shared profile UI component wired to `UserService`.

    Usage: instantiate with `page` and it will load current user data from
    session/user service. Methods:
      - get_profile_info() -> ft.Control
      - get_account_settings() -> ft.Control
      - show_edit_profile_dialog() -> opens dialog
      - show_change_avatar_dialog() -> opens dialog
      - show_edit_address_dialog(), show_change_password_dialog()
    """

    def __init__(self, page: ft.Page, on_update=None):
        self.page = page
        self.on_update = on_update
        self.user_service = UserService()
        self.state = self._load_state()

    def _load_state(self):
        user_id = self.page.session.get("user_id")
        full = self.user_service.get_user_full(user_id) or {}
        addr = self.user_service.get_user_address(user_id) or {}
        full_name = (full.get("full_name") or "").strip()
        parts = full_name.split(" ", 1)
        first = parts[0] if parts else ""
        last = parts[1] if len(parts) > 1 else ""
        # Allow session-stored values to override when service hasn't persisted yet
        session_full_name = self.page.session.get("full_name") or ""
        if session_full_name and not full_name:
            parts = session_full_name.split(" ", 1)
            first = parts[0] if parts else ""
            last = parts[1] if len(parts) > 1 else ""

        avatar_from_service = full.get("avatar")
        avatar_from_session = self.page.session.get("avatar")
        avatar_url = avatar_from_service or avatar_from_session or f"https://ui-avatars.com/api/?name={first}+{last}&size=110&background=4A90E2&color=fff&bold=true"

        return SimpleNamespace(
            user_id=user_id,
            first_name=first,
            last_name=last,
            gender=full.get("gender") or self.page.session.get("gender") or "",
            email=full.get("email") or self.page.session.get("email") or "",
            phone=full.get("phone") or "",
            avatar_url=avatar_url,
            house_no=addr.get("house") or "",
            street=addr.get("street") or "",
            barangay=addr.get("barangay") or "",
            city=addr.get("city") or "",
            actual_password=None,
            password_visible=False,
        )

    def create_info_field(self, label: str, value) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=13, color=ft.Colors.GREY_600, italic=True),
                    ft.Text(str(value), size=16, weight=ft.FontWeight.W_400, color=ft.Colors.BLACK),
                ],
                spacing=3,
            ),
            padding=ft.padding.only(bottom=15),
        )

    def get_profile_info(self) -> ft.ResponsiveRow:
        info_grid = ft.ResponsiveRow(
            controls=[
                ft.Container(content=self.create_info_field("First Name", self.state.first_name), col={"xs": 12, "sm": 6, "md": 4}),
                ft.Container(content=self.create_info_field("Last Name", self.state.last_name), col={"xs": 12, "sm": 6, "md": 4}),
                ft.Container(content=self.create_info_field("Gender", self.state.gender), col={"xs": 12, "sm": 6, "md": 4}),
                ft.Container(content=self.create_info_field("Email Address", self.state.email), col={"xs": 12, "sm": 6, "md": 4}),
                ft.Container(content=self.create_info_field("Phone Number", self.state.phone), col={"xs": 12, "sm": 6, "md": 4}),
            ],
            spacing=20,
            run_spacing=20,
        )

        current_avatar = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Stack(
                        controls=[
                            ft.Image(src=self.state.avatar_url, width=110, height=110, fit=ft.ImageFit.COVER, border_radius=10),
                        ]
                    ),
                    width=110,
                    height=110,
                    border=ft.border.all(2, ft.Colors.GREY_400),
                    border_radius=10,
                    alignment=ft.alignment.center,
                    on_click=lambda e: self.show_change_avatar_dialog(),
                    ink=True,
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Text("Edit Profile", size=14),
                    padding=ft.padding.symmetric(horizontal=20, vertical=8),
                    border=ft.border.all(1, ft.Colors.BLACK),
                    border_radius=20,
                    on_click=lambda e: self.show_edit_profile_dialog(),
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

    def get_account_settings(self) -> ft.Column:
        address_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Address", size=16, weight=ft.FontWeight.W_500),
                            ft.IconButton(icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, icon_size=20, on_click=lambda e: self.show_edit_address_dialog(), style=ft.ButtonStyle(padding=0)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                    ft.Container(height=5),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Column(controls=[ft.Text("House No.", size=12, italic=True, color=ft.Colors.GREY_500), ft.Text(self.state.house_no, size=14)], spacing=2, col={"xs": 6, "md": 3}),
                            ft.Column(controls=[ft.Text("Street", size=12, italic=True, color=ft.Colors.GREY_500), ft.Text(self.state.street, size=14)], spacing=2, col={"xs": 6, "md": 3}),
                            ft.Column(controls=[ft.Text("Barangay", size=12, italic=True, color=ft.Colors.GREY_500), ft.Text(self.state.barangay, size=14)], spacing=2, col={"xs": 6, "md": 3}),
                            ft.Column(controls=[ft.Text("City/Municipality", size=12, italic=True, color=ft.Colors.GREY_500), ft.Text(self.state.city, size=14)], spacing=2, col={"xs": 6, "md": 3}),
                        ]
                    ),
                ],
                spacing=5,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
        )

        def toggle_password_visibility(e):
            self.state.password_visible = not getattr(self.state, "password_visible", False)
            if callable(self.on_update):
                self.on_update()
            else:
                self.page.update()

        password_display = getattr(self.state, "actual_password", "") if getattr(self.state, "password_visible", False) and getattr(self.state, "actual_password", None) else "••••••••••••••••"

        password_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[ft.Text("Password", size=16, weight=ft.FontWeight.W_500), ft.IconButton(icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, icon_size=20, on_click=lambda e: self.show_change_password_dialog(), style=ft.ButtonStyle(padding=0))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Row(controls=[ft.Icon(ft.Icons.LOCK, size=18, color=ft.Colors.BLACK), ft.Text(password_display, size=18, weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.Icons.VISIBILITY_OFF_OUTLINED if getattr(self.state, "password_visible", False) else ft.Icons.VISIBILITY_OUTLINED, icon_size=20, on_click=lambda e: toggle_password_visibility(e))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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

        return ft.Column(controls=[address_content, ft.Container(height=10), password_content], spacing=20)

    def get_tabbed_view(self) -> ft.Tabs:
        """Return tabs for profile info and account settings."""
        return ft.Tabs(
            expand=True,
            animation_duration=250,
            tabs=[
                ft.Tab(
                    text="Personal Info",
                    content=ft.Container(
                        content=self.get_profile_info(),
                        padding=ft.padding.only(bottom=10),
                        expand=True,
                    ),
                ),
                ft.Tab(
                    text="Account Settings",
                    content=ft.Container(
                        content=self.get_account_settings(),
                        padding=ft.padding.only(bottom=10),
                        expand=True,
                    ),
                ),
            ],
        )

    def build(self) -> ft.Container:
        """Return a container that wraps the tabbed profile UI"""
        return ft.Container(content=self.get_tabbed_view())

    # --- Dialogs/actions wired to UserService ---
    def show_edit_profile_dialog(self):
        first_name_field = ft.TextField(label="First Name", value=self.state.first_name)
        last_name_field = ft.TextField(label="Last Name", value=self.state.last_name)
        gender_field = ft.Dropdown(label="Gender", value=self.state.gender, options=[ft.dropdown.Option("Male"), ft.dropdown.Option("Female"), ft.dropdown.Option("Other")])
        email_field = ft.TextField(label="Email Address", value=self.state.email)
        phone_field = ft.TextField(label="Phone Number", value=self.state.phone)

        def save_profile(e):
            # Show a confirmation dialog before saving profile changes
            def _perform_save(ev=None):
                try:
                    avatar_url = f"https://ui-avatars.com/api/?name={first_name_field.value}+{last_name_field.value}&size=110&background=4A90E2&color=fff&bold=true"
                    # Debug: log attempted update values
                    try:
                        print(f"[ProfileSection] Saving profile for user_id={self.state.user_id} first={first_name_field.value} last={last_name_field.value} gender={gender_field.value} email={email_field.value} phone={phone_field.value} avatar={avatar_url}", file=sys.stderr)
                    except Exception:
                        pass

                    result = self.user_service.update_user_profile_full(self.state.user_id, first_name_field.value, last_name_field.value, gender_field.value, email_field.value, phone_field.value, avatar_url)
                    try:
                        print(f"[ProfileSection] update_user_profile_full returned: {result}", file=sys.stderr)
                    except Exception:
                        pass

                    # Support both legacy bool return and new (ok,msg) tuple
                    if isinstance(result, tuple):
                        ok, db_msg = result
                    else:
                        ok, db_msg = bool(result), None

                    if ok:
                        # Re-query DB to get canonical stored values and update local state
                        try:
                            fresh = self.user_service.get_user_full(self.state.user_id) or {}
                            try:
                                print(f"[ProfileSection] Refresh after save, DB row: {fresh}", file=sys.stderr)
                            except Exception:
                                pass

                            # Prefer DB values when available, fall back to submitted values
                            full_name_db = (fresh.get('full_name') or f"{first_name_field.value} {last_name_field.value}").strip()
                            parts = full_name_db.split(' ', 1)
                            self.state.first_name = parts[0] if parts else first_name_field.value
                            self.state.last_name = parts[1] if len(parts) > 1 else last_name_field.value
                            self.state.gender = fresh.get('gender') or gender_field.value
                            self.state.email = fresh.get('email') or email_field.value
                            self.state.phone = fresh.get('phone') or phone_field.value
                            self.state.avatar_url = fresh.get('avatar') or avatar_url
                        except Exception:
                            # If re-query fails, fall back to submitted values
                            self.state.first_name = first_name_field.value
                            self.state.last_name = last_name_field.value
                            self.state.gender = gender_field.value
                            self.state.email = email_field.value
                            self.state.phone = phone_field.value
                            self.state.avatar_url = avatar_url

                        # update session so other components (navbar, pages) reflect changes
                        try:
                            self.page.session.set("full_name", f"{self.state.first_name} {self.state.last_name}".strip())
                            self.page.session.set("email", self.state.email)
                        except Exception:
                            try:
                                self.page.session["full_name"] = f"{self.state.first_name} {self.state.last_name}".strip()
                                self.page.session["email"] = self.state.email
                            except Exception:
                                pass

                        # Notify global refresh so other views can update
                        try:
                            from services.refresh_service import notify as _notify
                            _notify()
                        except Exception:
                            pass

                        try:
                            self.page.close(dialog)
                        except Exception:
                            pass

                        # Trigger UI update callbacks
                        if callable(self.on_update):
                            try:
                                self.on_update()
                            except Exception:
                                self.page.update()
                        else:
                            self.page.update()

                        # Show success feedback
                        try:
                            self.page.open(ft.SnackBar(content=ft.Text("Profile updated successfully!"), bgcolor=ft.Colors.GREEN))
                        except Exception:
                            pass

                        try:
                            self.page.update()
                        except Exception:
                            pass
                    else:
                        # Show DB adapter message when available
                        raise Exception(db_msg or "Update failed")
                except Exception as ex:
                    self.page.open(ft.SnackBar(content=ft.Text(f"Error changing password: {ex}"), bgcolor=ft.Colors.RED))
                    self.page.update()
                    self.page.update()

            confirm = ft.AlertDialog(
                title=ft.Text("Confirm Save"),
                content=ft.Text("Save profile changes?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda ev: self.page.close(confirm)),
                    ft.ElevatedButton("Save", on_click=lambda ev: (_perform_save(ev), self.page.close(confirm)))
                ]
            )
            self.page.open(confirm)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Profile"),
            content=ft.Container(content=ft.Column(controls=[first_name_field, last_name_field, gender_field, email_field, phone_field], tight=True, spacing=15), width=400),
            actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)), ft.ElevatedButton("Save", on_click=save_profile)],
        )
        self.page.open(dialog)

    def show_change_avatar_dialog(self):
        file_picker = ft.FilePicker(on_result=lambda e: handle_avatar_upload(e))
        self.page.overlay.append(file_picker)
        self.page.update()
        preview_image = ft.Image(src=self.state.avatar_url, width=150, height=150, fit=ft.ImageFit.COVER, border_radius=10)

        def handle_avatar_upload(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                file = e.files[0]
                self.state.avatar_url = file.path if file.path else self.state.avatar_url
                preview_image.src = self.state.avatar_url
                self.page.update()

        def pick_avatar(e):
            file_picker.pick_files(allowed_extensions=["png", "jpg", "jpeg", "gif"], dialog_title="Choose Profile Picture")

        def save_avatar(e):
            try:
                result = self.user_service.update_user_avatar(self.state.user_id, self.state.avatar_url)
                if result:
                    # result is the stored path (absolute path or external URL)
                    stored_path = result
                    # update local state and session so other components (navbar) can reflect change
                    self.state.avatar_url = stored_path
                    try:
                        self.page.session.set("avatar", stored_path)
                    except Exception:
                        # if session doesn't support set(), fall back to dict-like access
                        try:
                            self.page.session["avatar"] = stored_path
                        except Exception:
                            pass

                    # Notify global refresh and update UI
                    try:
                        from services.refresh_service import notify as _notify
                        _notify()
                    except Exception:
                        pass

                    try:
                        self.page.close(dialog)
                    except Exception:
                        pass
                    if callable(self.on_update):
                        self.on_update()
                    else:
                        self.page.update()
                    self.page.open(ft.SnackBar(content=ft.Text("Avatar updated successfully!"), bgcolor=ft.Colors.GREEN))
                    self.page.update()
                else:
                    raise Exception("Failed to save avatar")
            except Exception as ex:
                self.page.open(ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))
                self.page.update()

        def remove_avatar(e):
            # Confirm before removing avatar
            def _do_remove(ev=None):
                self.state.avatar_url = f"https://ui-avatars.com/api/?name={self.state.first_name}+{self.state.last_name}&size=110&background=4A90E2&color=fff&bold=true"
                preview_image.src = self.state.avatar_url
                self.page.update()

            confirm_remove = ft.AlertDialog(
                title=ft.Text("Remove Photo"),
                content=ft.Text("Are you sure you want to remove your profile photo?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda ev: self.page.close(confirm_remove)),
                    ft.ElevatedButton("Remove", on_click=lambda ev: (_do_remove(ev), self.page.close(confirm_remove)))
                ]
            )
            self.page.open(confirm_remove)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Change Profile Picture"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(content=preview_image, alignment=ft.alignment.center),
                        ft.Container(height=20),
                        ft.ElevatedButton("Choose Photo", icon=ft.Icons.UPLOAD_FILE, on_click=pick_avatar, width=200),
                        ft.OutlinedButton("Remove Photo", icon=ft.Icons.DELETE_OUTLINE, on_click=remove_avatar, width=200),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                    spacing=10,
                ),
                width=400,
            ),
            actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)), ft.ElevatedButton("Save", on_click=save_avatar)],
        )
        self.page.open(dialog)

    def show_edit_address_dialog(self):
        house_field = ft.TextField(label="House No.", value=self.state.house_no)
        street_field = ft.TextField(label="Street", value=self.state.street)
        barangay_field = ft.TextField(label="Barangay", value=self.state.barangay)
        city_field = ft.TextField(label="City/Municipality", value=self.state.city)

        def save_address(e):
            try:
                ok = self.user_service.update_user_address(self.state.user_id, house_field.value, street_field.value, barangay_field.value, city_field.value)
                if ok:
                    self.state.house_no = house_field.value
                    self.state.street = street_field.value
                    self.state.barangay = barangay_field.value
                    self.state.city = city_field.value
                    self.page.close(dialog)
                    # ensure UI updates and session reflects name/email if needed
                    if callable(self.on_update):
                        self.on_update()
                    else:
                        self.page.update()
                    self.page.open(ft.SnackBar(content=ft.Text("Address updated successfully!"), bgcolor=ft.Colors.GREEN))
                    self.page.update()
                else:
                    raise Exception("Failed to update address")
            except Exception as ex:
                self.page.open(ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))
                self.page.update()

        dialog = ft.AlertDialog(modal=True, title=ft.Text("Edit Address"), content=ft.Container(content=ft.Column(controls=[house_field, street_field, barangay_field, city_field], tight=True, spacing=15), width=400), actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)), ft.ElevatedButton("Save", on_click=save_address)])
        self.page.open(dialog)

    def show_change_password_dialog(self):
        def create_req_item(text):
            return ft.Row(controls=[ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=ft.Colors.GREY_500), ft.Text(text, size=12, color=ft.Colors.GREY_500)], spacing=5)

        req_length = create_req_item("At least 8 characters")
        req_upper = create_req_item("One uppercase letter")
        req_number = create_req_item("One number")
        req_special = create_req_item("One special character (!@#$%^&*)")
        requirements_column = ft.Column(controls=[req_length, req_upper, req_number, req_special], spacing=2, visible=False)

        def validate_password_live(e):
            pwd = e.control.value
            requirements_column.visible = True
            required_specials = "!@#$%^&*"

            def update_req(item, condition):
                color = ft.Colors.GREEN if condition else ft.Colors.GREY_500
                icon = ft.Icons.CHECK_CIRCLE if condition else ft.Icons.CHECK_CIRCLE_OUTLINE
                item.controls[0].color = color
                item.controls[0].name = icon
                item.controls[1].color = color

            update_req(req_length, len(pwd) >= 8)
            update_req(req_upper, any(char.isupper() for char in pwd))
            update_req(req_number, any(char.isdigit() for char in pwd))
            update_req(req_special, any(char in required_specials for char in pwd))
            self.page.update()

        def toggle_password_view(e, text_field):
            text_field.password = not text_field.password
            e.control.icon = ft.Icons.VISIBILITY_OFF if not text_field.password else ft.Icons.VISIBILITY
            text_field.update()

        current_password = ft.TextField(label="Current Password", password=True, suffix=ft.IconButton(ft.Icons.VISIBILITY, icon_size=18, on_click=lambda e: toggle_password_view(e, current_password)))
        new_password = ft.TextField(label="New Password", password=True, on_change=validate_password_live, suffix=ft.IconButton(ft.Icons.VISIBILITY, icon_size=18, on_click=lambda e: toggle_password_view(e, new_password)))
        confirm_password = ft.TextField(label="Confirm New Password", password=True, suffix=ft.IconButton(ft.Icons.VISIBILITY, icon_size=18, on_click=lambda e: toggle_password_view(e, confirm_password)))

        def save_password(e):
            if new_password.value != confirm_password.value:
                self.page.open(ft.SnackBar(content=ft.Text("Passwords do not match!"), bgcolor=ft.Colors.RED))
                self.page.update()
                return

            pwd = new_password.value
            required_specials = "!@#$%^&*"
            if (len(pwd) < 8 or not any(c.isupper() for c in pwd) or not any(c.isdigit() for c in pwd) or not any(c in required_specials for c in pwd)):
                self.page.open(ft.SnackBar(content=ft.Text("Please ensure all password requirements are met."), bgcolor=ft.Colors.RED))
                self.page.update()
                return

            # Confirm before applying the password change
            def _perform_change(ev=None):
                try:
                    ok = self.user_service.update_user_password(self.state.user_id, new_password.value)
                    if ok:
                        self.state.actual_password = new_password.value
                        self.state.password_visible = False
                        try:
                            self.page.close(dialog)
                        except Exception:
                            pass
                        if callable(self.on_update):
                            self.on_update()
                        else:
                            self.page.update()
                        self.page.open(ft.SnackBar(content=ft.Text("Password changed successfully!"), bgcolor=ft.Colors.GREEN))
                        self.page.update()
                    else:
                        raise Exception("Failed to update password")
                except Exception as ex:
                    self.page.open(ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))
                    self.page.update()

            confirm = ft.AlertDialog(
                title=ft.Text("Confirm Password Change"),
                content=ft.Text("Are you sure you want to change your password?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda ev: self.page.close(confirm)),
                    ft.ElevatedButton("Change", on_click=lambda ev: (_perform_change(ev), self.page.close(confirm)))
                ]
            )
            self.page.open(confirm)

        dialog = ft.AlertDialog(modal=True, title=ft.Text("Change Password"), content=ft.Container(content=ft.Column(controls=[current_password, new_password, ft.Container(content=requirements_column, padding=ft.padding.only(left=10)), confirm_password], tight=True, spacing=15), width=400), actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)), ft.ElevatedButton("Change Password", on_click=save_password)])
        self.page.open(dialog)
