"""Property Manager Add/Edit Listing View"""
import os
import shutil
from datetime import datetime
import calendar as cal_module
import flet as ft
from storage.db import (
    get_listing_by_id,
    get_listing_images,
    get_user_info,
    create_listing,
    update_listing,
)


class PMAddEditView:
    def __init__(self, page: ft.Page):
        self.page = page

    def build(self):
        page = self.page
        user_id_raw = page.session.get("user_id")
        try:
            user_id = int(user_id_raw) if user_id_raw is not None else None
        except (TypeError, ValueError):
            user_id = None

        if not user_id:
            page.go("/login")
            return None

        # Determine if we're editing or creating
        listing_id = None
        if page.route.startswith("/pm/edit/"):
            try:
                listing_id = int(page.route.split("/")[-1])
            except (ValueError, IndexError):
                page.go("/pm")
                return None

        is_edit = listing_id is not None
        listing = None
        existing_images = []
        owner_profile = None

        if is_edit:
            # Retrieve listing from database
            listing = get_listing_by_id(listing_id)
            if not listing or int(listing.get("pm_id", -1)) != user_id:
                snack_bar = ft.SnackBar(ft.Text("Listing not found or access denied"))
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.go("/pm")
                return None

            # Retrieve images from database
            existing_images = get_listing_images(listing_id)

            # Retrieve owner information from database
            owner_profile = get_user_info(listing["pm_id"])

        # Helper function to parse lodging_details and extract saved values
        def parse_lodging_details(lodging_details_str):
            """Parse lodging_details to extract saved field values"""
            parsed = {
                "base_details": "",
                "bedroom_type": "single",
                "deposit": "",
                "cancellation_policy": "",
                "listing_status": "available",
                "available_from": None,
                "amenities": [],
            }

            if not lodging_details_str:
                return parsed

            # Split by " | " to separate base details from extra fields
            parts = lodging_details_str.split(" | ")
            if len(parts) > 1:
                parsed["base_details"] = parts[0].strip()
                # Parse extra fields
                for part in parts[1:]:
                    part = part.strip()
                    if part.startswith("Bedroom type: "):
                        bedroom_val = part.replace("Bedroom type: ", "").strip()
                        bedroom_map = {
                            "Single": "single",
                            "Double deck for 2": "double_deck_2",
                            "Double deck for 4": "double_deck_4",
                            "Studio type": "studio",
                        }
                        parsed["bedroom_type"] = bedroom_map.get(bedroom_val, "single")
                    elif part.startswith("Deposit: "):
                        parsed["deposit"] = part.replace("Deposit: ", "").strip()
                    elif part.startswith("Cancellation policy: "):
                        parsed["cancellation_policy"] = (
                            part.replace("Cancellation policy: ", "").strip()
                        )
                    elif part.startswith("Listing status: "):
                        status_val = (
                            part.replace("Listing status: ", "").strip().lower()
                        )
                        parsed["listing_status"] = (
                            status_val
                            if status_val in ["available", "reserved", "occupied"]
                            else "available"
                        )
                    elif part.startswith("Available from: "):
                        date_str = part.replace("Available from: ", "").strip()
                        parsed["available_from"] = date_str
                    elif part.startswith("Amenities: "):
                        amenities_str = part.replace("Amenities: ", "").strip()
                        if amenities_str:
                            parsed["amenities"] = [
                                a.strip() for a in amenities_str.split(",") if a.strip()
                            ]
            else:
                parsed["base_details"] = lodging_details_str.strip()

            return parsed

        # Parse lodging details if editing
        parsed_details = {}
        if is_edit and listing:
            try:
                lodging_details_str = listing["lodging_details"] or ""
                parsed_details = parse_lodging_details(lodging_details_str)
            except Exception:
                parsed_details = {}

            # Initialize calendar state from parsed available_from date
            if parsed_details.get("available_from"):
                try:
                    date_parts = parsed_details["available_from"].split("-")
                    if len(date_parts) == 3:
                        setattr(page, 'calendar_state', {
                            "month": int(date_parts[1]),
                            "year": int(date_parts[0]),
                            "selected_date": int(date_parts[2]),
                        })
                except Exception:
                    pass

        # Helper function to safely get field value from listing
        def get_listing_value(field_name, default=""):
            """Safely retrieve a field value from the listing database row"""
            if not listing:
                return default
            try:
                value = listing[field_name]
                return str(value) if value is not None else default
            except (KeyError, IndexError, TypeError):
                return default

        # Helper function to safely get field value from owner_profile
        def get_owner_value(field_name, default=""):
            """Safely retrieve a field value from the owner_profile dictionary"""
            if not owner_profile:
                return default
            try:
                value = owner_profile[field_name]
                return str(value) if value is not None else default
            except (KeyError, IndexError, TypeError):
                return default

        # Form fields - populate from database when editing
        property_name_field = ft.TextField(
            expand=True,
            height=48,
            value=get_listing_value("property_name", ""),
            autofocus=True,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        address_field = ft.TextField(
            expand=True,
            height=48,
            value=get_listing_value("address", ""),
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        price_field = ft.TextField(
            width=700,
            height=50,
            value=get_listing_value("price", ""),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )
        description_field = ft.TextField(
            width=700,
            multiline=True,
            min_lines=4,
            max_lines=8,
            value=get_listing_value("description", ""),
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )
        lodging_details_field = ft.TextField(
            width=700,
            multiline=True,
            min_lines=3,
            max_lines=6,
            value=get_listing_value("lodging_details", ""),
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )
        phone_number_field = ft.TextField(
            expand=True,
            height=48,
            value=get_owner_value("phone", ""),
            keyboard_type=ft.KeyboardType.PHONE,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        email_field = ft.TextField(
            expand=True,
            height=48,
            value=get_owner_value("email", ""),
            keyboard_type=ft.KeyboardType.EMAIL,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

        # Step 3 fields
        monthly_rent_field = ft.TextField(
            expand=True,
            height=48,
            hint_text="Monthly Rent",
            value=get_listing_value("price", ""),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        deposit_field = ft.TextField(
            expand=True,
            height=48,
            hint_text="Deposit",
            value=parsed_details.get("deposit", "") if parsed_details else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        cancellation_policy_field = ft.TextField(
            expand=True,
            multiline=True,
            min_lines=5,
            max_lines=10,
            value=parsed_details.get("cancellation_policy", "")
            if parsed_details
            else "",
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.all(16),
        )

        # Bedroom type
        bedroom_type = ft.RadioGroup(
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Radio(value="single", label="Single"),
                    ft.Radio(value="double_deck_2", label="Double deck for 2"),
                    ft.Radio(value="double_deck_4", label="Double deck for 4"),
                    ft.Radio(value="studio", label="Studio type"),
                ],
            ),
            value=parsed_details.get("bedroom_type", "single")
            if parsed_details
            else "single",
        )

        # Listing status
        listing_status = ft.RadioGroup(
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Radio(value="available", label="Available"),
                    ft.Radio(value="reserved", label="Reserved"),
                    ft.Radio(value="occupied", label="Occupied"),
                ],
            ),
            value=parsed_details.get("listing_status", "available")
            if parsed_details
            else "available",
        )
        status_toggle = ft.Switch(value=True, label="", label_position=ft.LabelPosition.LEFT)

        # Step management
        current_step_num = [1]

        # Images - use existing images if editing, empty list if new
        uploaded_files = existing_images.copy() if existing_images else []
        image_previews = ft.Row(wrap=True, spacing=10)

        # Amenities with icons
        default_amenities = ["Free-WiFi", "In-unit Laundry", "Aircondition", "Kitchen"]
        amenity_icons = {
            "Free-WiFi": ft.Icons.WIFI,
            "In-unit Laundry": ft.Icons.LOCAL_LAUNDRY_SERVICE,
            "Aircondition": ft.Icons.AC_UNIT,
            "Kitchen": ft.Icons.KITCHEN,
        }

        # Initialize amenities - check if they were saved when editing
        saved_amenities = parsed_details.get("amenities", []) if parsed_details else []
        amenity_checkboxes = {}
        for amenity in default_amenities:
            is_checked = amenity in saved_amenities if saved_amenities else False
            amenity_checkboxes[amenity] = ft.Checkbox(label=amenity, value=is_checked)

        # Also add any custom amenities that were saved
        if saved_amenities:
            for amenity in saved_amenities:
                if amenity not in amenity_checkboxes:
                    amenity_checkboxes[amenity] = ft.Checkbox(label=amenity, value=True)

        # Container to hold amenities list
        amenities_list_container = ft.Column(spacing=12)

        # Input field for adding new amenity
        new_amenity_input = ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
            controls=[
                ft.Icon(ft.Icons.CHECK_BOX_OUTLINE_BLANK, size=20, color=ft.Colors.BLACK),
                ft.TextField(
                    hint_text="Type amenity name...",
                    expand=True,
                    height=40,
                    border_radius=8,
                    bgcolor="#FAFAFA",
                    border_color="#E0E0E0",
                    focused_border_color="#0078FF",
                    content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    on_submit=lambda e: save_new_amenity_from_input(e),
                ),
            ],
        )

        # File picker for images
        def handle_file_picker_result(e: ft.FilePickerResultEvent):
            if e.files:
                for file in e.files:
                    # Create uploads directory if it doesn't exist
                    upload_dir = "assets/uploads"
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)

                    # Save file
                    file_path = os.path.join(upload_dir, file.name)
                    shutil.copy(file.path, file_path)
                    uploaded_files.append(file_path)

                    # Add preview
                    image_previews.controls.append(
                        ft.Container(
                            width=120,
                            height=120,
                            border_radius=8,
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            content=ft.Stack(
                                controls=[
                                    ft.Image(
                                        src=file_path,
                                        width=120,
                                        height=120,
                                        fit=ft.ImageFit.COVER,
                                    ),
                                    ft.Container(
                                        content=ft.IconButton(
                                            icon=ft.Icons.CLOSE,
                                            icon_color="white",
                                            bgcolor="#00000080",
                                            on_click=lambda e, path=file_path: remove_image(
                                                path
                                            ),
                                        ),
                                        alignment=ft.alignment.top_right,
                                    ),
                                ]
                            ),
                        )
                    )
                page.update()

        def remove_image(path):
            if path in uploaded_files:
                uploaded_files.remove(path)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
            # Rebuild previews
            image_previews.controls.clear()
            for file_path in uploaded_files:
                image_previews.controls.append(
                    ft.Container(
                        width=120,
                        height=120,
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Stack(
                            controls=[
                                ft.Image(
                                    src=file_path,
                                    width=120,
                                    height=120,
                                    fit=ft.ImageFit.COVER,
                                ),
                                ft.Container(
                                    content=ft.IconButton(
                                        icon=ft.Icons.CLOSE,
                                        icon_color="white",
                                        bgcolor="#00000080",
                                        on_click=lambda e, p=file_path: remove_image(p),
                                    ),
                                    alignment=ft.alignment.top_right,
                                ),
                            ]
                        ),
                    )
                )
            page.update()

        # Load existing images
        for img_path in existing_images:
            if os.path.exists(img_path):
                image_previews.controls.append(
                    ft.Container(
                        width=120,
                        height=120,
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Stack(
                            controls=[
                                ft.Image(
                                    src=img_path,
                                    width=120,
                                    height=120,
                                    fit=ft.ImageFit.COVER,
                                ),
                                ft.Container(
                                    content=ft.IconButton(
                                        icon=ft.Icons.CLOSE,
                                        icon_color="white",
                                        bgcolor="#00000080",
                                        on_click=lambda e, p=img_path: remove_image(p),
                                    ),
                                    alignment=ft.alignment.top_right,
                                ),
                            ]
                        ),
                    )
                )
                if img_path not in uploaded_files:
                    uploaded_files.append(img_path)

        file_picker = ft.FilePicker(on_result=handle_file_picker_result)
        page.overlay.append(file_picker)

        msg = ft.Text(" ", size=12)

        # Helper to render labeled form rows
        def form_row(label: str, field_control: ft.Control, trailing_control=None):
            row_fields = [ft.Container(expand=True, content=field_control)]
            if trailing_control:
                row_fields.append(trailing_control)

            return ft.Container(
                padding=ft.padding.only(bottom=20),
                content=ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=140,
                            content=ft.Text(
                                label,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#333333",
                            ),
                        ),
                        ft.Row(
                            spacing=8,
                            expand=True,
                            controls=row_fields,
                        ),
                    ],
                ),
            )

        # Step content containers
        step_content = ft.Ref()
        step_indicator_text = ft.Ref()
        step_circles = ft.Ref()

        # Step navigation functions
        def update_step_indicator(step_num):
            step_circles.current.controls.clear()
            for i in range(1, 4):
                if i == step_num:
                    step_circles.current.controls.append(
                        ft.Container(
                            width=28,
                            height=28,
                            border_radius=14,
                            bgcolor="#333333",
                            border=ft.border.all(2, "#333333"),
                            content=ft.Text(
                                str(i),
                                color="white",
                                size=14,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                        )
                    )
                else:
                    step_circles.current.controls.append(
                        ft.Container(
                            width=28,
                            height=28,
                            border_radius=14,
                            bgcolor="transparent",
                            border=ft.border.all(2, "#E0E0E0"),
                            content=ft.Text(
                                str(i),
                                color="#999",
                                size=14,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                        )
                    )
            step_indicator_text.current.value = f"Step {step_num} of 3"
            step_circles.current.update()
            step_indicator_text.current.update()

        # Function to build amenities list
        def build_amenities_list():
            """Rebuilds the amenities list with icons and remove buttons."""
            amenities_list_container.controls.clear()

            def create_remove_amenity_handler(name: str):
                def handler(e):
                    if name in default_amenities:
                        snack = ft.SnackBar(
                            content=ft.Text("Default amenities cannot be removed."),
                            bgcolor="#F44336",
                            action="OK",
                            action_color="white",
                        )
                        setattr(page, 'snack_bar', snack)
                        try:
                            getattr(page, 'snack_bar').open = True
                        except Exception:
                            try:
                                page.open(getattr(page, 'snack_bar'))
                            except Exception:
                                pass
                        page.update()
                        return

                    if name in amenity_checkboxes:
                        del amenity_checkboxes[name]
                        build_amenities_list()
                        page.update()

                return handler

            for amenity, checkbox in amenity_checkboxes.items():
                icon = amenity_icons.get(amenity, ft.Icons.CHECK_CIRCLE)
                row_controls = [
                    ft.Icon(icon, size=20, color="#333333"),
                    checkbox,
                ]

                if amenity not in default_amenities:
                    row_controls.append(
                        ft.IconButton(
                            icon=ft.Icons.REMOVE_CIRCLE,
                            icon_size=20,
                            icon_color="#E53935",
                            tooltip="Remove amenity",
                            on_click=create_remove_amenity_handler(amenity),
                        )
                    )

                amenities_list_container.controls.append(
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=row_controls,
                    )
                )

            try:
                amenities_list_container.update()
            except Exception:
                pass

        # Function to add new amenity
        def add_amenity(amenity_name):
            if (
                amenity_name
                and amenity_name.strip()
                and amenity_name not in amenity_checkboxes
            ):
                amenity_checkboxes[amenity_name] = ft.Checkbox(
                    label=amenity_name,
                    value=False,
                )
                build_amenities_list()
                page.update()
                return True
            return False

        # Function to save amenity from input field
        def save_new_amenity_from_input(e):
            amenity_name = e.control.value.strip()
            if amenity_name:
                if add_amenity(amenity_name):
                    e.control.value = ""
                    new_amenity_input.visible = False
                    page.update()
                else:
                    snack = ft.SnackBar(
                        content=ft.Text("Amenity already exists"),
                        bgcolor="#F44336",
                        action="OK",
                        action_color="white",
                    )
                    setattr(page, 'snack_bar', snack)
                    try:
                        getattr(page, 'snack_bar').open = True
                    except Exception:
                        try:
                            page.open(getattr(page, 'snack_bar'))
                        except Exception:
                            pass
                    page.update()

        # Function to show input field for adding amenity
        def open_add_amenity_input():
            new_amenity_input.visible = True
            for control in new_amenity_input.controls:
                if isinstance(control, ft.TextField):
                    control.focus()
                    break
            page.update()

        # Initialize amenities list
        build_amenities_list()

        def show_step(step_num):
            current_step_num[0] = step_num
            step_content.current.content = get_step_content(step_num)
            update_step_indicator(step_num)
            step_content.current.update()
            page.update()

        def get_step_content(step_num):
            if step_num == 1:
                # Step 1: core property information
                return ft.Column(
                    spacing=25,
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        ft.Container(
                            padding=ft.padding.only(bottom=15),
                            content=ft.Text(
                                "Property Information",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="#1A1A1A",
                            ),
                        ),
                        form_row("Property Name", property_name_field),
                        form_row(
                            "Location",
                            address_field,
                            ft.IconButton(
                                icon=ft.Icons.PLACE,
                                icon_color="#0078FF",
                                tooltip="Use map location (coming soon)",
                                style=ft.ButtonStyle(color="#0078FF"),
                            ),
                        ),
                        form_row("Description", description_field),
                        form_row("Phone Number", phone_number_field),
                        form_row("Email", email_field),
                        msg,
                        ft.Container(height=10),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=15,
                            controls=[
                                ft.OutlinedButton(
                                    "Cancel",
                                    width=160,
                                    height=44,
                                    icon=ft.Icons.CANCEL,
                                    style=ft.ButtonStyle(color="#333333"),
                                    on_click=lambda _: page.go("/pm"),
                                ),
                                ft.ElevatedButton(
                                    "Next",
                                    width=160,
                                    height=44,
                                    style=ft.ButtonStyle(
                                        color="white",
                                        bgcolor="#333333",
                                    ),
                                    on_click=lambda _: show_step(2),
                                ),
                            ],
                        ),
                    ],
                )
            elif step_num == 2:
                # Step 2: Images and Amenities
                return ft.Column(
                    spacing=20,
                    controls=[
                        ft.Row(
                            spacing=20,
                            controls=[
                                # Left: Upload Property Images
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=15,
                                        controls=[
                                            ft.Text(
                                                "Upload Property Images",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.GestureDetector(
                                                on_tap=lambda _: file_picker.pick_files(
                                                    allowed_extensions=[
                                                        "jpg",
                                                        "jpeg",
                                                        "png",
                                                        "gif",
                                                    ],
                                                    allow_multiple=True,
                                                ),
                                                content=ft.Container(
                                                    width=400,
                                                    height=300,
                                                    bgcolor="#F5F5F5",
                                                    border_radius=12,
                                                    border=ft.border.all(2, "#E0E0E0"),
                                                    content=ft.Column(
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                        spacing=10,
                                                        controls=[
                                                            ft.Icon(
                                                                ft.Icons.CAMERA_ALT,
                                                                size=48,
                                                                color=ft.Colors.BLACK,
                                                            ),
                                                            ft.Text(
                                                                "Add photos",
                                                                size=14,
                                                                color=ft.Colors.BLACK,
                                                            ),
                                                        ],
                                                    ),
                                                ),
                                            ),
                                            # Thumbnail previews row
                                            ft.Container(
                                                content=image_previews
                                                if image_previews.controls
                                                else ft.Row(
                                                    spacing=10,
                                                    controls=[
                                                        ft.GestureDetector(
                                                            on_tap=lambda e, idx=i: file_picker.pick_files(
                                                                allowed_extensions=[
                                                                    "jpg",
                                                                    "jpeg",
                                                                    "png",
                                                                    "gif",
                                                                ],
                                                                allow_multiple=True,
                                                            ),
                                                            content=ft.Container(
                                                                width=120,
                                                                height=120,
                                                                bgcolor="#F5F5F5",
                                                                border_radius=8,
                                                                border=ft.border.all(
                                                                    1, "#E0E0E0"
                                                                ),
                                                                content=ft.Column(
                                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                    spacing=0,
                                                                    controls=[
                                                                        ft.Icon(
                                                                            ft.Icons.CAMERA_ALT,
                                                                            size=36,
                                                                            color=ft.Colors.BLACK,
                                                                        ),
                                                                    ],
                                                                ),
                                                            ),
                                                        )
                                                        for i in range(3)
                                                    ],
                                                )
                                            ),
                                        ],
                                    ),
                                ),
                                # Divider
                                ft.Container(
                                    width=1,
                                    bgcolor="#E0E0E0",
                                    border=ft.border.symmetric(
                                        vertical=ft.BorderSide(1, "#E0E0E0")
                                    ),
                                ),
                                # Right: Amenities
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=15,
                                        controls=[
                                            ft.Text(
                                                "Bedroom Type",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            bedroom_type,
                                            ft.Container(height=15),
                                            ft.Text(
                                                "Amenities",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            amenities_list_container,
                                            new_amenity_input,
                                            ft.Container(
                                                margin=ft.margin.only(top=10),
                                                content=ft.OutlinedButton(
                                                    "Add more",
                                                    icon=ft.Icons.ADD,
                                                    width=120,
                                                    height=40,
                                                    style=ft.ButtonStyle(
                                                        color="#333333",
                                                    ),
                                                    on_click=lambda _: open_add_amenity_input(),
                                                ),
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        # Navigation buttons
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=15,
                            controls=[
                                ft.OutlinedButton(
                                    "Previous",
                                    width=160,
                                    height=44,
                                    icon=ft.Icons.ARROW_BACK,
                                    style=ft.ButtonStyle(color="#333333"),
                                    on_click=lambda _: show_step(1),
                                ),
                                ft.ElevatedButton(
                                    "Next",
                                    width=160,
                                    height=44,
                                    style=ft.ButtonStyle(
                                        color="white",
                                        bgcolor="#333333",
                                    ),
                                    on_click=lambda _: show_step(3),
                                ),
                            ],
                        ),
                    ],
                )
            else:  # step_num == 3
                # Step 3: Pricing & Terms, Calendar, and Listing Status
                # Calendar state initialization
                if not hasattr(page, "calendar_state"):
                    if parsed_details and parsed_details.get("available_from"):
                        try:
                            date_parts = parsed_details["available_from"].split("-")
                            if len(date_parts) == 3:
                                setattr(page, 'calendar_state', {
                                    "month": int(date_parts[1]),
                                    "year": int(date_parts[0]),
                                    "selected_date": int(date_parts[2]),
                                })
                            else:
                                raise ValueError("Invalid date format")
                        except Exception:
                            setattr(page, 'calendar_state', {
                                "month": datetime.now().month,
                                "year": datetime.now().year,
                                "selected_date": datetime.now().day,
                            })
                    else:
                        setattr(page, 'calendar_state', {
                            "month": datetime.now().month,
                            "year": datetime.now().year,
                            "selected_date": datetime.now().day,
                        })

                cal_state = getattr(page, 'calendar_state', {})
                calendar_month = cal_state.get("month", datetime.now().month)
                calendar_year = cal_state.get("year", datetime.now().year)
                selected_day = cal_state.get("selected_date", datetime.now().day)

                # Get calendar data
                month_names = [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ]
                month_name = month_names[calendar_month - 1]

                first_weekday, days_in_month = cal_module.monthrange(
                    calendar_year, calendar_month
                )

                calendar_days = []
                # Add weekday headers
                weekday_headers = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                for day in weekday_headers:
                    calendar_days.append(
                        ft.Container(
                            width=40,
                            height=30,
                            content=ft.Text(
                                day, size=12, color=ft.Colors.BLACK, text_align=ft.TextAlign.CENTER
                            ),
                            alignment=ft.alignment.center,
                        )
                    )

                # Add empty cells for days before month starts
                for _ in range(first_weekday):
                    calendar_days.append(
                        ft.Container(
                            width=40,
                            height=30,
                            content=ft.Text("", size=12),
                            alignment=ft.alignment.center,
                        )
                    )

                # Add calendar dates
                def create_date_click_handler(day):
                    def handler(e):
                        cal_state = getattr(page, 'calendar_state', {})
                        cal_state["selected_date"] = day
                        setattr(page, 'calendar_state', cal_state)
                        show_step(3)

                    return handler

                for day in range(1, days_in_month + 1):
                    is_selected = (
                        day == selected_day
                        and calendar_month == getattr(page, 'calendar_state', {}).get("month")
                        and calendar_year == getattr(page, 'calendar_state', {}).get("year")
                    )
                    calendar_days.append(
                        ft.GestureDetector(
                            on_tap=create_date_click_handler(day),
                            content=ft.Container(
                                width=40,
                                height=30,
                                bgcolor="#333333" if is_selected else "transparent",
                                border_radius=4,
                                content=ft.Text(
                                    str(day),
                                    size=12,
                                    color="white" if is_selected else "#333333",
                                    text_align=ft.TextAlign.CENTER,
                                    weight=ft.FontWeight.BOLD
                                    if is_selected
                                    else ft.FontWeight.NORMAL,
                                ),
                                alignment=ft.alignment.center,
                            ),
                        )
                    )

                # Add empty cells for days after month ends
                total_cells = len(calendar_days)
                remaining_cells = (6 * 7) - total_cells
                if remaining_cells > 0:
                    for _ in range(remaining_cells):
                        calendar_days.append(
                            ft.Container(
                                width=40,
                                height=30,
                                content=ft.Text("", size=12),
                                alignment=ft.alignment.center,
                            )
                        )

                # Month navigation functions
                def prev_month(e):
                    cal_state = getattr(page, 'calendar_state', None)
                    if cal_state is None:
                        cal_state = {
                            "month": datetime.now().month,
                            "year": datetime.now().year,
                            "selected_date": datetime.now().day,
                        }
                    if cal_state.get("month", datetime.now().month) == 1:
                        cal_state["month"] = 12
                        cal_state["year"] = cal_state.get("year", datetime.now().year) - 1
                    else:
                        cal_state["month"] = cal_state.get("month", datetime.now().month) - 1
                    cal_state["selected_date"] = 1
                    setattr(page, 'calendar_state', cal_state)
                    show_step(3)

                def next_month(e):
                    cal_state = getattr(page, 'calendar_state', None)
                    if cal_state is None:
                        cal_state = {
                            "month": datetime.now().month,
                            "year": datetime.now().year,
                            "selected_date": datetime.now().day,
                        }
                    if cal_state.get("month", datetime.now().month) == 12:
                        cal_state["month"] = 1
                        cal_state["year"] = cal_state.get("year", datetime.now().year) + 1
                    else:
                        cal_state["month"] = cal_state.get("month", datetime.now().month) + 1
                    cal_state["selected_date"] = 1
                    setattr(page, 'calendar_state', cal_state)
                    show_step(3)

                return ft.Column(
                    spacing=20,
                    controls=[
                        ft.Row(
                            spacing=20,
                            controls=[
                                # Left Column: Pricing & Terms
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=20,
                                        alignment=ft.MainAxisAlignment.START,
                                        controls=[
                                            ft.Text(
                                                "Pricing & Terms",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            monthly_rent_field,
                                            deposit_field,
                                            ft.Container(height=10),
                                            ft.Text(
                                                "Cancellation Policy",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            cancellation_policy_field,
                                        ],
                                    ),
                                ),
                                # Right Column: Calendar and Listing Status
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=20,
                                        alignment=ft.MainAxisAlignment.START,
                                        controls=[
                                            # Calendar
                                            ft.Container(
                                                padding=15,
                                                bgcolor="#FAFAFA",
                                                border_radius=8,
                                                content=ft.Column(
                                                    spacing=10,
                                                    controls=[
                                                        ft.Row(
                                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                            controls=[
                                                                ft.Text(
                                                                    f"{month_name} {calendar_year}",
                                                                    size=14,
                                                                    weight=ft.FontWeight.BOLD,
                                                                ),
                                                                ft.Row(
                                                                    spacing=5,
                                                                    controls=[
                                                                        ft.IconButton(
                                                                            icon=ft.Icons.CHEVRON_LEFT,
                                                                            icon_size=16,
                                                                            on_click=prev_month,
                                                                        ),
                                                                        ft.IconButton(
                                                                            icon=ft.Icons.CHEVRON_RIGHT,
                                                                            icon_size=16,
                                                                            on_click=next_month,
                                                                        ),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        # Weekday headers
                                                        ft.Row(
                                                            spacing=5,
                                                            controls=calendar_days[:7],
                                                        ),
                                                        # Week 1
                                                        ft.Row(
                                                            spacing=5,
                                                            controls=calendar_days[7:14],
                                                        ),
                                                        # Week 2
                                                        ft.Row(
                                                            spacing=5,
                                                            controls=calendar_days[14:21],
                                                        ),
                                                        # Week 3
                                                        ft.Row(
                                                            spacing=5,
                                                            controls=calendar_days[21:28],
                                                        ),
                                                        # Week 4
                                                        ft.Row(
                                                            spacing=5,
                                                            controls=calendar_days[28:35],
                                                        ),
                                                        # Week 5-6
                                                        ft.Row(
                                                            spacing=5,
                                                            controls=calendar_days[35:42]
                                                            if len(calendar_days) > 35
                                                            else [],
                                                        ),
                                                    ],
                                                ),
                                            ),
                                            # Listing Status
                                            ft.Text(
                                                "Listing Status",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            listing_status,
                                            ft.Row(
                                                spacing=8,
                                                controls=[
                                                    ft.Text("Occupied", size=14),
                                                    status_toggle,
                                                ],
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        # Navigation buttons
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=15,
                            controls=[
                                ft.OutlinedButton(
                                    "Previous",
                                    width=160,
                                    height=44,
                                    icon=ft.Icons.ARROW_BACK,
                                    style=ft.ButtonStyle(color="#333333"),
                                    on_click=lambda _: show_step(2),
                                ),
                                ft.ElevatedButton(
                                    "Save Changes" if is_edit else "Create Listing",
                                    width=160,
                                    height=44,
                                    style=ft.ButtonStyle(
                                        color="white",
                                        bgcolor="#333333",
                                    ),
                                    on_click=save_listing,
                                ),
                            ],
                        ),
                    ],
                )

        def save_listing(e):
            def fail(message: str):
                msg.value = message
                msg.color = "red"
                snack = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor="#F44336",
                    action="OK",
                    action_color="white",
                )
                setattr(page, 'snack_bar', snack)
                try:
                    getattr(page, 'snack_bar').open = True
                except Exception:
                    try:
                        page.open(getattr(page, 'snack_bar'))
                    except Exception:
                        pass
                page.update()
                return False

            # Quick visual feedback
            snack = ft.SnackBar(
                content=ft.Text("Saving listing..."),
                bgcolor="#333333",
                action_color="white",
            )
            setattr(page, 'snack_bar', snack)
            try:
                getattr(page, 'snack_bar').open = True
            except Exception:
                try:
                    page.open(getattr(page, 'snack_bar'))
                except Exception:
                    pass
            page.update()

            # Validation
            if not property_name_field.value:
                if fail("Missing field: Property Name.") is False:
                    return
            if not address_field.value:
                if fail("Missing field: Address.") is False:
                    return

            def parse_price(raw_value: str | None) -> float | None:
                """Allow currency symbols, commas, and whitespace for user-friendly input."""
                if not raw_value:
                    return None
                cleaned = (
                    raw_value.replace("₱", "")
                    .replace("$", "")
                    .replace(",", "")
                    .strip()
                )
                if not cleaned:
                    return None
                try:
                    return float(cleaned)
                except ValueError:
                    return None

            # Sync Monthly Rent from Step 3 into the main price field
            if monthly_rent_field.value and monthly_rent_field.value.strip():
                price_field.value = monthly_rent_field.value.strip()

            normalized_price = parse_price(price_field.value)
            if normalized_price is None or normalized_price <= 0:
                if fail("Invalid or missing field: Price per month.") is False:
                    return
            if not description_field.value:
                if fail("Missing field: Description.") is False:
                    return

            # Optional numeric deposit validation
            if deposit_field.value and deposit_field.value.strip():
                dep_val = parse_price(deposit_field.value)
                if dep_val is None or dep_val < 0:
                    if fail("Deposit must be a valid number.") is False:
                        return

            # Optional phone number validation (digits and basic length)
            if phone_number_field.value:
                digits_only = "".join(ch for ch in phone_number_field.value if ch.isdigit())
                if len(digits_only) < 7 or len(digits_only) > 15:
                    if fail("Phone number should be 7-15 digits.") is False:
                        return
                phone_number_field.value = digits_only

            effective_uploaded_files = uploaded_files or []

            # Build extended lodging details
            extra_details_parts = []

            # Bedroom type
            bedroom_label_map = {
                "single": "Single",
                "double_deck_2": "Double deck for 2",
                "double_deck_4": "Double deck for 4",
                "studio": "Studio type",
            }
            if bedroom_type.value:
                extra_details_parts.append(
                    f"Bedroom type: {bedroom_label_map.get(bedroom_type.value, bedroom_type.value)}"
                )

            # Deposit
            if deposit_field.value:
                extra_details_parts.append(f"Deposit: {deposit_field.value}")

            # Cancellation policy
            if cancellation_policy_field.value:
                extra_details_parts.append(
                    f"Cancellation policy: {cancellation_policy_field.value}"
                )

            # Listing status
            if listing_status.value:
                extra_details_parts.append(
                    f"Listing status: {listing_status.value.capitalize()}"
                )

            # Availability date from calendar
            available_from = None
            if hasattr(page, "calendar_state"):
                d = page.calendar_state  # type: ignore
                try:
                    available_from = (
                        f"{d['year']}-{d['month']:02d}-{d['selected_date']:02d}"
                    )
                except Exception:
                    available_from = None
            if available_from:
                extra_details_parts.append(f"Available from: {available_from}")

            # Amenities
            checked_amenities = [
                name
                for name, checkbox in amenity_checkboxes.items()
                if checkbox.value
            ]
            if checked_amenities:
                extra_details_parts.append(
                    f"Amenities: {', '.join(checked_amenities)}"
                )

            # Append extra details into lodging_details_field
            if extra_details_parts:
                extra_details = " | ".join(extra_details_parts)
                current_value = lodging_details_field.value or ""
                if is_edit and current_value and " | " in current_value:
                    existing_parts = current_value.split(" | ")
                    base_details = existing_parts[0] if existing_parts else current_value
                    lodging_details_field.value = f"{base_details} | {extra_details}"
                elif current_value:
                    lodging_details_field.value = (
                        f"{current_value} | {extra_details}"
                    )
                else:
                    lodging_details_field.value = extra_details

            price: float = float(normalized_price or 0)

            # Safe defaults for DB-bound strings
            addr_val = address_field.value or ""
            desc_val = description_field.value or ""
            lodging_val = lodging_details_field.value or ""

            if is_edit:
                assert listing_id is not None
                success = update_listing(
                    int(listing_id),
                    int(user_id),
                    addr_val,
                    price,
                    desc_val,
                    lodging_val,
                    effective_uploaded_files,
                )
                action = "updated"
            else:
                listing_id_new = create_listing(
                    user_id,
                    addr_val,
                    price,
                    desc_val,
                    lodging_val,
                    effective_uploaded_files,
                )
                success = listing_id_new is not None
                action = "created"

            if success:
                snack = ft.SnackBar(
                    content=ft.Text("Property listed successfully."),
                    bgcolor="#4CAF50",
                    action="OK",
                    action_color="white",
                )
                setattr(page, 'snack_bar', snack)
                try:
                    getattr(page, 'snack_bar').open = True
                except Exception:
                    try:
                        page.open(getattr(page, 'snack_bar'))
                    except Exception:
                        pass
                page.go("/pm")
                page.update()
            else:
                msg.value = f"Failed to {action} listing"
                msg.color = "red"
                snack = ft.SnackBar(
                    content=ft.Text(
                        "Something went wrong while saving your listing. Please try again."
                    ),
                    bgcolor="#F44336",
                    action="OK",
                    action_color="white",
                )
                setattr(page, 'snack_bar', snack)
                try:
                    getattr(page, 'snack_bar').open = True
                except Exception:
                    try:
                        page.open(getattr(page, 'snack_bar'))
                    except Exception:
                        pass
                page.update()

        return ft.View(
            f"/pm/add" if not is_edit else f"/pm/edit/{listing_id}",
            padding=0,
            scroll=ft.ScrollMode.AUTO,
            bgcolor="#F5F7FA",
            controls=[
                # Top app bar
                ft.Container(
                    bgcolor="#FFFFFF",
                    padding=ft.padding.symmetric(horizontal=40, vertical=20),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color="#00000008",
                        offset=ft.Offset(0, 2),
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.HOME,
                                        color="#0078FF",
                                        size=24,
                                    ),
                                    ft.Text(
                                        "campusKubo",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color="#1A1A1A",
                                    ),
                                ],
                            ),
                            ft.OutlinedButton(
                                "Back to Dashboard",
                                icon=ft.Icons.ARROW_BACK,
                                style=ft.ButtonStyle(color="#333333"),
                                on_click=lambda _: page.go("/pm"),
                            ),
                        ],
                    ),
                ),
                # Main content
                ft.Container(
                    padding=40,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=30,
                        controls=[
                            # Title + step indicator
                            ft.Column(
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        "Edit Listing"
                                        if is_edit
                                        else "Create a New Listing",
                                        size=26,
                                        weight=ft.FontWeight.BOLD,
                                        color="#1A1A1A",
                                    ),
                                    ft.Row(
                                        ref=step_circles,
                                        spacing=12,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            ft.Container(
                                                width=28,
                                                height=28,
                                                border_radius=14,
                                                bgcolor="#333333",
                                                border=ft.border.all(
                                                    2, "#333333"
                                                ),
                                                content=ft.Text(
                                                    "1",
                                                    color="white",
                                                    size=14,
                                                    text_align=ft.TextAlign.CENTER,
                                                ),
                                                alignment=ft.alignment.center,
                                            ),
                                            ft.Container(
                                                width=28,
                                                height=28,
                                                border_radius=14,
                                                bgcolor="transparent",
                                                border=ft.border.all(
                                                    2, "#E0E0E0"
                                                ),
                                                content=ft.Text(
                                                                    "2",
                                                                    color=ft.Colors.BLACK,
                                                                    size=14,
                                                                    text_align=ft.TextAlign.CENTER,
                                                                ),
                                                alignment=ft.alignment.center,
                                            ),
                                            ft.Container(
                                                width=28,
                                                height=28,
                                                border_radius=14,
                                                bgcolor="transparent",
                                                border=ft.border.all(
                                                    2, "#E0E0E0"
                                                ),
                                                content=ft.Text(
                                                                    "3",
                                                                    color=ft.Colors.BLACK,
                                                                    size=14,
                                                                    text_align=ft.TextAlign.CENTER,
                                                                ),
                                                alignment=ft.alignment.center,
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        ref=step_indicator_text,
                                        value="Step 1 of 3",
                                        size=12,
                                        color="#777",
                                    ),
                                ],
                            ),
                            # Card with step content
                            ft.Container(
                                ref=step_content,
                                width=840,
                                padding=30,
                                bgcolor="#FFFFFF",
                                border_radius=16,
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=20,
                                    color="#00000015",
                                    offset=ft.Offset(0, 4),
                                ),
                                content=get_step_content(1),
                            ),
                        ],
                    ),
                ),
            ],
        )
