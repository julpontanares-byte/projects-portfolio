"""Property Manager Profile View"""
import os
import shutil
import flet as ft
from storage.db import get_user_info, update_user_info
from components.profile_section import ProfileSection


class PMProfileView:
    def __init__(self, page: ft.Page):
        self.page = page

    def _setup_avatar(self, profile_image_path):
        """Setup profile avatar and file picker"""
        has_profile_image = os.path.exists(profile_image_path)

        profile_avatar = ft.CircleAvatar(
            radius=40,
            foreground_image_src=profile_image_path if has_profile_image else None,
            bgcolor="#0078FF",
            content=ft.Icon(ft.Icons.PERSON, color="white")
            if not has_profile_image
            else None,
        )

        def handle_profile_upload(e: ft.FilePickerResultEvent):
            if e.files:
                src = e.files[0].path
                try:
                    shutil.copy(src, profile_image_path)
                    profile_avatar.foreground_image_src = profile_image_path
                    profile_avatar.content = None
                    profile_avatar.update()
                except Exception:
                    pass

        profile_file_picker = ft.FilePicker(on_result=handle_profile_upload)
        self.page.overlay.append(profile_file_picker)

        def pick_profile_photo(e):
            profile_file_picker.pick_files(
                allowed_extensions=["jpg", "jpeg", "png"],
                allow_multiple=False,
            )

        camera_overlay = ft.Container(
            width=32,
            height=32,
            bgcolor="#0078FF",
            border_radius=16,
            border=ft.border.all(2, "#FFFFFF"),
            content=ft.Icon(ft.Icons.CAMERA_ALT, size=18, color="#FFFFFF"),
            alignment=ft.alignment.center,
        )

        profile_avatar_with_camera = ft.GestureDetector(
            on_tap=pick_profile_photo,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=90,
                        height=90,
                        padding=3,
                        border=ft.border.all(2, "#000000"),
                        border_radius=45,
                        bgcolor="#FFFFFF",
                        content=profile_avatar,
                    ),
                    ft.Container(
                        width=90,
                        height=90,
                        alignment=ft.alignment.bottom_right,
                        content=camera_overlay,
                        margin=ft.margin.only(right=0, bottom=0),
                    ),
                ],
            ),
        )

        return profile_avatar_with_camera

    def _info_row(self, label: str, value: str, obscure: bool = False):
        """Helper to render read-only info rows"""
        display_value = "••••••••" if obscure and value else (value or "")
        return ft.Row(
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    f"{label}:",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    italic=True,
                    color="#000000",
                    width=70,
                ),
                ft.Container(
                    expand=True,
                    height=38,
                    bgcolor="#FFFFFF",
                    border_radius=10,
                    border=ft.border.all(1, "#E0E0E0"),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(display_value, size=13, color="#000000"),
                            ft.Icon(
                                ft.Icons.CHEVRON_RIGHT,
                                size=16,
                                color="#B0B0B0",
                            ),
                        ],
                    ),
                ),
            ],
        )

    def _edit_row(self, label: str, field_control: ft.Control):
        """Helper to render editable rows"""
        return ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    f"{label}:",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    italic=True,
                    color="#000000",
                    width=90,
                ),
                field_control,
            ],
        )

    def build(self):
        page = self.page
        user_id = page.session.get("user_id")
        if not user_id:
            page.go("/login")
            return None

        full_name = page.session.get("full_name") or ""
        email = page.session.get("email") or ""
        role = page.session.get("role") or "pm"

        title_text = "PROPERTY MANAGER PROFILE"

        # ProfileSection component handles avatar, profile info and account settings
        profile_comp = ProfileSection(self.page, on_update=lambda: self.page.update())

        # Role chip
        role_label = "Property Manager"
        role_chip = ft.Container(
            content=ft.Text(
                role_label, size=12, color="#0078FF", weight=ft.FontWeight.BOLD
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            border=ft.border.all(1, "#0078FF"),
        )

        # Get user info from database
        user_info = get_user_info(user_id)
        phone_value = user_info.get("phone", "") if user_info else ""
        status_value = "Verified"

        name_value = full_name or "Not set"
        email_value = email or "Not set"
        phone_display = phone_value or "Not set"

        change_password_btn = ft.ElevatedButton(
            "Change Password",
            icon=ft.Icons.LOCK_RESET,
            width=220,
        )

        two_fa_switch = ft.Switch(label="Enable 2FA", value=False)

        upload_doc_btn = ft.ElevatedButton(
            "Upload New Document",
            icon=ft.Icons.UPLOAD_FILE,
            width=260,
        )

        return ft.View(
            "/pm/profile",
            padding=0,
            scroll=ft.ScrollMode.AUTO,
            bgcolor="#F5F7FA",
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=40, vertical=20),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                title_text,
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color="#1A1A1A",
                            ),
                            ft.TextButton(
                                "Back to Dashboard",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda e: page.go("/pm"),
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=40,
                    alignment=ft.alignment.top_center,
                    content=ft.Container(
                        width=700,
                        padding=30,
                        bgcolor="#FFFFFF",
                        border_radius=16,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=20,
                            color="#00000015",
                            offset=ft.Offset(0, 4),
                        ),
                        content=ft.Column(
                            spacing=20,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                # Use shared ProfileSection for profile + account settings
                                profile_comp.get_profile_info(),
                                ft.Divider(),
                                profile_comp.get_account_settings(),
                                ft.Divider(),
                                # Documents + actions (kept from previous layout)
                                ft.Row(controls=[upload_doc_btn, change_password_btn], spacing=12),
                                ft.Divider(),
                                ft.ElevatedButton(
                                    "Edit Profile",
                                    icon=ft.Icons.EDIT,
                                    width=200,
                                    on_click=lambda e: profile_comp.show_edit_profile_dialog(),
                                ),
                            ],
                        ),
                    ),
                ),
            ],
        )

    def build_edit(self):
        page = self.page
        user_id = page.session.get("user_id")
        if not user_id:
            page.go("/login")
            return None

        user_info = get_user_info(user_id)
        if not user_info:
            page.go("/login")
            return None

        full_name = user_info.get("full_name") or ""
        email = user_info.get("email") or ""
        phone = user_info.get("phone") or ""
        role = user_info.get("role") or "pm"

        # Profile picture setup
        profile_dir = "assets/uploads/profile_photos"
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        profile_image_path = os.path.join(profile_dir, f"profile_{user_id}.png")

        profile_avatar_with_camera = self._setup_avatar(profile_image_path)

        # Role chip
        role_label = "Property Manager"
        role_chip = ft.Container(
            content=ft.Text(
                role_label, size=12, color="#0078FF", weight=ft.FontWeight.BOLD
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            border=ft.border.all(1, "#0078FF"),
        )

        # Editable fields
        name_field = ft.TextField(
            label="Name",
            value=full_name,
            expand=True,
            height=48,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        email_field = ft.TextField(
            label="E-mail",
            value=email,
            expand=True,
            height=48,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        phone_field = ft.TextField(
            label="Phone",
            value=phone,
            expand=True,
            height=48,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

        msg = ft.Text("", size=12, color="red")

        status_value = "Verified"

        change_password_btn = ft.ElevatedButton(
            "Change Password",
            icon=ft.Icons.LOCK_RESET,
            width=220,
        )

        two_fa_switch = ft.Switch(label="Enable 2FA", value=False)

        upload_doc_btn = ft.ElevatedButton(
            "Upload New Document",
            icon=ft.Icons.UPLOAD_FILE,
            width=260,
        )

        def save_profile(e):
            new_name = (name_field.value or "").strip()
            new_email = (email_field.value or "").strip()
            new_phone = (phone_field.value or "").strip()

            if not new_name or not new_email:
                msg.value = "Name and E-mail are required."
                msg.update()
                return

            success = update_user_info(user_id, new_name, new_email, new_phone)
            if success:
                page.session.set("full_name", new_name)
                page.session.set("email", new_email)
                snack = ft.SnackBar(
                    content=ft.Text("Profile updated successfully."),
                    bgcolor="#4CAF50",
                    action="OK",
                    action_color="white",
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
                page.go("/pm/profile")
            else:
                msg.value = "Unable to save changes (email may already be in use)."
                msg.update()

        return ft.View(
            "/pm/profile/edit",
            padding=0,
            scroll=ft.ScrollMode.AUTO,
            bgcolor="#F5F7FA",
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=40, vertical=20),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Edit Profile",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color="#1A1A1A",
                            ),
                            ft.TextButton(
                                "Cancel",
                                icon=ft.Icons.CLOSE,
                                on_click=lambda e: page.go("/pm/profile"),
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=40,
                    alignment=ft.alignment.top_center,
                    content=ft.Container(
                        width=700,
                        padding=30,
                        bgcolor="#FFFFFF",
                        border_radius=16,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=20,
                            color="#00000015",
                            offset=ft.Offset(0, 4),
                        ),
                        content=ft.Column(
                            spacing=20,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                # Avatar and name/role row
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=16,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        profile_avatar_with_camera,
                                        ft.Column(
                                            spacing=8,
                                            controls=[
                                                ft.Text(
                                                    full_name or email,
                                                    size=22,
                                                    weight=ft.FontWeight.BOLD,
                                                    color="#1A1A1A",
                                                ),
                                                role_chip,
                                            ],
                                        ),
                                    ],
                                ),
                                ft.Divider(),
                                # Editable sections
                                ft.Column(
                                    spacing=18,
                                    alignment=ft.MainAxisAlignment.START,
                                    controls=[
                                        ft.Text(
                                            "Basic info",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        self._edit_row("Name", name_field),
                                        self._edit_row("E-mail", email_field),
                                        self._edit_row("Phone", phone_field),
                                        ft.Divider(),
                                        ft.Text(
                                            "Business Verification",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        self._info_row("Status", status_value),
                                        ft.Divider(),
                                        ft.Text(
                                            "Account info",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        self._info_row("Username", email),
                                        self._info_row("Password", "password", obscure=True),
                                        ft.Divider(),
                                        ft.Text(
                                            "Security",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        change_password_btn,
                                        two_fa_switch,
                                        ft.Divider(),
                                        ft.Text(
                                            "Documents",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        upload_doc_btn,
                                    ],
                                ),
                                msg,
                                ft.Row(
                                    spacing=10,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.ElevatedButton(
                                            "Save Changes",
                                            icon=ft.Icons.SAVE,
                                            on_click=save_profile,
                                        ),
                                        ft.OutlinedButton(
                                            "Cancel",
                                            icon=ft.Icons.CANCEL,
                                            on_click=lambda e: page.go("/pm/profile"),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ),
            ],
        )


