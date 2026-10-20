"""
Property details view
Updated from main.py property_details_view implementation
"""
"""
Property details view with earthy color palette
"""
import flet as ft
from datetime import datetime, timedelta
from storage.db import get_property_by_id, create_reservation, get_listing_availability
from components.reservation_form import ReservationForm
from config.colors import COLORS
from utils.navigation import go_back


class PropertyDetailView:
    """Property details view"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.colors = COLORS

    def go_back(self, e):
        go_back(self.page, "/browse")

    def build(self):
        """Build property details view - matching model"""
        property_id = self.page.session.get("selected_property_id")

        if not property_id:
            snack_bar = ft.SnackBar(
                ft.Text("Property not found. Please select a property first.", color=self.colors["card_bg"]),
                bgcolor=self.colors["error"]
            )
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.go("/browse")
            return

        property_data = get_property_by_id(property_id)

        if not property_data:
            snack_bar = ft.SnackBar(
                ft.Text("Property not found. Please select a valid property.", color=self.colors["card_bg"]),
                bgcolor=self.colors["error"]
            )
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.go("/browse")
            return

        def handle_action_button(e):
            # Show inline reservation dialog for tenants to avoid role-based redirects
            user_role = self.page.session.get("role")
            print(f"[DEBUG] handle_action_button clicked - role={user_role}, selected_property_id={property_id}")
            if not user_role:
                show_auth_dialog()
                return

            # Inline dialog helpers
            def show_reservation_dialog(listing_id: int):
                print(f"[DEBUG] show_reservation_dialog called with listing_id={listing_id}")
                availability = []
                try:
                    rows = get_listing_availability(listing_id)
                    for r in rows:
                        try:
                            s = datetime.fromisoformat(str(r['start_date']))
                            t = datetime.fromisoformat(str(r['end_date']))
                            availability.append((s, t))
                        except Exception:
                            pass
                except Exception:
                    availability = []

                # Use ReservationForm component for date selection and submission
                error_text = ft.Text("", color=ft.Colors.RED)

                def on_submit_handler(listing_id_param, start_dt, end_dt, msg_control):
                    print(f"[DEBUG] ReservationForm submitted - listing={listing_id_param}, start={start_dt}, end={end_dt}")
                    tenant_id = self.page.session.get('user_id')
                    if not tenant_id:
                        msg_control.value = "You must be logged in to reserve"
                        self.page.update()
                        return

                    res = create_reservation(listing_id_param, tenant_id, start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))
                    print(f"[DEBUG] create_reservation returned: {res}")
                    if res:
                        self.page.snack_bar = ft.SnackBar(ft.Text('Reservation created!'), bgcolor=ft.Colors.GREEN)
                        self.page.snack_bar.open = True
                        try:
                            self.page.close(dlg)
                        except Exception:
                            pass
                        self.page.update()
                    else:
                        msg_control.value = "Failed to create reservation"
                        self.page.update()

                form = ReservationForm(self.page, listing_id, on_submit=on_submit_handler)
                form_ui = form.build()

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text('Reserve Property'),
                    content=ft.Column([
                        ft.Text("Select your reservation dates:", size=16),
                        form_ui
                    ], tight=True),
                    actions=[
                        ft.TextButton('Cancel', on_click=lambda ev: (print("[DEBUG] Cancel button clicked - closing dialog"), self.page.close(dlg))),
                    ]
                )
                print(f"[DEBUG] Created AlertDialog with ReservationForm")
                try:
                    self.page.open(dlg)
                    print(f"[DEBUG] self.page.open(dlg) called successfully - dialog should be visible now")
                    self.page.update()
                except Exception as e:
                    print(f"[DEBUG] Exception in self.page.open(dlg): {e}")
                    import traceback
                    traceback.print_exc()

            # If tenant, open dialog inline. Otherwise show coming-soon snackbar.
            if user_role == 'tenant':
                try:
                    show_reservation_dialog(property_id)
                except Exception as ex:
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=self.colors['error']); self.page.snack_bar.open = True; self.page.update()
            else:
                snack_bar = ft.SnackBar(
                    ft.Text("Reservation feature coming soon!", color=self.colors["card_bg"]),
                    bgcolor=self.colors["accent"]
                )
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()

        def show_auth_dialog():
            def close_dialog():
                dialog.open = False
                self.page.update()

            def close_and_navigate(route):
                dialog.open = False
                self.page.update()
                self.page.go(route)

            dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.LOCK_PERSON, color=self.colors["secondary"], size=30),
                    ft.Text("Account Required", weight=ft.FontWeight.BOLD, color=self.colors["text_dark"])
                ], spacing=10),
                content=ft.Container(
                    width=300,
                    content=ft.Column(
                        tight=True,
                        spacing=10,
                        controls=[
                            ft.Text(
                                "To reserve this property, you need to create an account or sign in.",
                                size=14,
                                color=self.colors["text_dark"]
                            ),
                            ft.Divider(height=1, color=self.colors["border"]),
                            ft.Text("✨ Benefits of signing up:", size=13, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                            ft.Text("• Reserve properties instantly", size=12, color=self.colors["text_light"]),
                            ft.Text("• Contact property owners", size=12, color=self.colors["text_light"]),
                            ft.Text("• Save favorite listings", size=12, color=self.colors["text_light"]),
                            ft.Text("• Track your reservations", size=12, color=self.colors["text_light"]),
                        ]
                    )
                ),
                actions=[
                    ft.ElevatedButton(
                        "Create Account",
                        icon=ft.Icons.PERSON_ADD,
                        bgcolor=self.colors["accent"],
                        color=self.colors["card_bg"],
                        on_click=lambda _: close_and_navigate("/signup")
                    ),
                    ft.OutlinedButton(
                        "Sign In",
                        icon=ft.Icons.LOGIN,
                        on_click=lambda _: close_and_navigate("/login"),
                        style=ft.ButtonStyle(
                            color=self.colors["text_dark"],
                            side=ft.BorderSide(color=self.colors["border"], width=1)
                        )
                    ),
                    ft.TextButton(
                        "Maybe Later",
                        on_click=lambda _: close_dialog(),
                        style=ft.ButtonStyle(color=self.colors["text_light"])
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                bgcolor=self.colors["card_bg"]
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        from components.logo import Logo

        nav_bar = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.95, self.colors["background"]),
            padding=ft.padding.symmetric(horizontal=25, vertical=15),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, self.colors["text_light"]),
                offset=ft.Offset(0, 2)
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    # Left side — only back button + logo
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=self.go_back,
                            icon_color=self.colors["primary"],
                            tooltip="Back"
                        ),
                        Logo(size=24, color=self.colors["text_dark"]),
                    ], spacing=5),

                    # Right side — completely empty
                    ft.Container()  # This keeps the Row spaced correctly
                ]
            )
        )

        # Determine button state based on login status
        user_role = self.page.session.get("role")
        is_available = property_data.get("availability_status", "Available") == "Available"

        action_button = ft.ElevatedButton(
            "Reserve Now" if is_available else "Contact Owner",
            width=250,
            height=50,
            bgcolor=self.colors["primary"] if is_available else self.colors["border"],
            color=self.colors["card_bg"],
            disabled=not is_available and not user_role,
            on_click=handle_action_button,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )

        amenities_str = property_data.get("amenities", "")
        amenities_list = [a.strip() for a in amenities_str.split(",")] if amenities_str else []

        # Create amenity chips
        amenity_chips = []
        for amenity in amenities_list:
            amenity_chips.append(
                ft.Container(
                    bgcolor=ft.Colors.with_opacity(0.3, self.colors["accent"]),
                    padding=ft.padding.symmetric(horizontal=15, vertical=10),
                    border_radius=20,
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=self.colors["primary"]),
                        ft.Text(amenity, size=14, color=self.colors["text_dark"], weight=ft.FontWeight.W_500)
                    ], spacing=8, tight=True)
                )
            )

        # Get available room types
        available_rooms_str = property_data.get("available_room_types", "")
        available_rooms_list = [r.strip() for r in available_rooms_str.split(",")] if available_rooms_str else []

        # Create available rooms list items
        available_rooms_items = []
        for room_type in available_rooms_list:
            available_rooms_items.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=0, vertical=8),
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=self.colors["primary"]),
                        ft.Text(room_type, size=14, color=self.colors["text_dark"])
                    ], spacing=10)
                )
            )

        # Get all property images
        image_urls = []
        if property_data.get("image_url"):
            image_urls.append(property_data.get("image_url"))
        # Add additional images if they exist
        for i in range(2, 5):  # For image_url_2, image_url_3, image_url_4
            img_url = property_data.get(f"image_url_{i}")
            if img_url:
                image_urls.append(img_url)

        def show_image_viewer(start_index):
            current_index = [start_index]

            def close_viewer():
                viewer_dialog.open = False
                self.page.update()

            def next_image():
                if current_index[0] < len(image_urls) - 1:
                    current_index[0] += 1
                    viewer_image.src = image_urls[current_index[0]]
                    image_counter.value = f"{current_index[0] + 1} / {len(image_urls)}"
                    update_arrows()
                    self.page.update()

            def prev_image():
                if current_index[0] > 0:
                    current_index[0] -= 1
                    viewer_image.src = image_urls[current_index[0]]
                    image_counter.value = f"{current_index[0] + 1} / {len(image_urls)}"
                    update_arrows()
                    self.page.update()

            def update_arrows():
                prev_btn.visible = current_index[0] > 0
                next_btn.visible = current_index[0] < len(image_urls) - 1
                self.page.update()

            # Main image
            viewer_image = ft.Image(
                src=image_urls[start_index],
                fit=ft.ImageFit.CONTAIN,
                expand=True,
            )

            image_counter = ft.Text(
                f"{start_index + 1} / {len(image_urls)}",
                color=ft.Colors.WHITE,
                size=16,
                weight=ft.FontWeight.BOLD,
            )

            # Arrows
            prev_btn = ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                icon_size=40,
                icon_color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=20),
                on_click=lambda _: prev_image(),
                visible=start_index > 0,
            )

            next_btn = ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                icon_size=40,
                icon_color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=20),
                on_click=lambda _: next_image(),
                visible=start_index < len(image_urls) - 1,
            )

            # SWIPE + TAP (left/right = navigate, center = close)
            def on_tap(e: ft.TapEvent):
                width = e.control.width or 900
                if e.local_x < width * 0.3:
                    prev_image()
                elif e.local_x > width * 0.7:
                    next_image()
                else:
                    close_viewer()

            def on_pan_update(e: ft.DragUpdateEvent):
                if e.delta_x < -40:
                    next_image()
                elif e.delta_x > 40:
                    prev_image()

            swipe_container = ft.GestureDetector(
                content=viewer_image,
                on_tap=on_tap,
                on_pan_update=on_pan_update,
                drag_interval=15,
            )

            # FINAL DIALOG — X BUTTON IN TOP-LEFT CORNER (OUTSIDE IMAGE)
            viewer_dialog = ft.AlertDialog(
                modal=True,
                bgcolor=ft.Colors.TRANSPARENT,
                content_padding=0,
                content=ft.Stack([
                    # Dark background
                    ft.Container(bgcolor=ft.Colors.with_opacity(0.97, ft.Colors.BLACK), expand=True),

                    # Centered image container
                    ft.Container(
                        content=swipe_container,
                        width=920,
                        height=680,
                        bgcolor=ft.Colors.BLACK,
                        border_radius=20,
                        alignment=ft.alignment.center,
                    ),

                    # Counter at bottom center
                    ft.Container(
                        content=image_counter,
                        bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
                        padding=12,
                        border_radius=30,
                        bottom=40,
                        alignment=ft.alignment.center,
                    ),

                    # Left & Right arrows
                    ft.Row([
                        prev_btn,
                        ft.Container(expand=True),
                        next_btn,
                    ], top=0, bottom=0, left=30, right=30),

                    # X BUTTON — TOP-LEFT CORNER (SAFE & CLEAN)
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.CLOSE_ROUNDED,
                            icon_size=34,
                            icon_color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
                            style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=14),
                            on_click=lambda _: close_viewer(),
                        ),
                        top=40,
                        left=40,
                    ),
                ]),
                shape=ft.RoundedRectangleBorder(radius=0),
            )

            self.page.overlay.append(viewer_dialog)
            viewer_dialog.open = True
            self.page.update()

        return ft.View(
            "/property-details",
            padding=0,
            scroll=ft.ScrollMode.AUTO,
            bgcolor=ft.Colors.with_opacity(0.98, self.colors["background"]),
            controls=[
                nav_bar,

                # Main Content Container
                ft.Container(
                    padding=30,
                    content=ft.Column(
                        spacing=25,
                        controls=[
                            # Header Section with Title and Price
                            ft.Container(
                                bgcolor=ft.Colors.with_opacity(0.95, self.colors["card_bg"]),
                                padding=25,
                                border_radius=12,
                                border=ft.border.all(1, self.colors["border"]),
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=15,
                                    color=ft.Colors.with_opacity(0.08, self.colors["text_light"]),
                                ),
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                    controls=[
                                        ft.Column(
                                            expand=True,
                                            spacing=15,
                                            controls=[
                                                ft.Text(
                                                    property_data.get("name", "Property"),
                                                    size=36,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=self.colors["text_dark"]
                                                ),
                                                ft.Row([
                                                    ft.Icon(ft.Icons.LOCATION_ON, size=22, color=self.colors["primary"]),
                                                    ft.Text(
                                                        property_data.get("address", "N/A"),
                                                        size=16,
                                                        color=self.colors["text_light"]
                                                    )
                                                ], spacing=8),
                                                ft.Row([
                                                    ft.Icon(ft.Icons.PLACE, size=20, color=self.colors["secondary"]),
                                                    ft.Text(
                                                        property_data.get("location", "N/A"),
                                                        size=15,
                                                        color=self.colors["text_light"]
                                                    )
                                                ], spacing=8)
                                            ]
                                        ),
                                        ft.Container(
                                            bgcolor=ft.Colors.with_opacity(0.4, self.colors["accent"]),
                                            padding=20,
                                            border_radius=12,
                                            border=ft.border.all(2, self.colors["primary"]),
                                            content=ft.Column(
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                spacing=8,
                                                controls=[
                                                    ft.Text(
                                                        "Monthly Rent",
                                                        size=14,
                                                        color=self.colors["text_light"],
                                                        weight=ft.FontWeight.W_500
                                                    ),
                                                    ft.Text(
                                                        f"₱{property_data.get('price', 0):,.0f}",
                                                        size=32,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=self.colors["text_dark"]
                                                    )
                                                ]
                                            )
                                        )
                                    ]
                                )
                            ),

                            # Image and Description Side by Side
                            ft.Container(
                                bgcolor=ft.Colors.with_opacity(0.95, self.colors["card_bg"]),
                                padding=25,
                                border_radius=12,
                                border=ft.border.all(1, self.colors["border"]),
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=15,
                                    color=ft.Colors.with_opacity(0.08, self.colors["text_light"]),
                                ),
                                content=ft.Row(
                                    spacing=25,
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                    controls=[
                                        # Image Gallery (Left Side)
                                        ft.Container(
                                            width=500,
                                            content=ft.Column(
                                                spacing=15,
                                                controls=[
                                                    ft.Text(
                                                        "Photos",
                                                        size=22,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=self.colors["text_dark"]
                                                    ),
                                                    ft.Column(
                                                        spacing=10,
                                                        controls=[
                                                            # Large main image on top
                                                            ft.Container(
                                                                width=500,
                                                                height=300,
                                                                bgcolor=ft.Colors.with_opacity(0.4, self.colors["border"]),
                                                                border_radius=12,
                                                                ink=True,
                                                                on_click=lambda _: show_image_viewer(0) if image_urls else None,
                                                                content=ft.Image(
                                                                    src=image_urls[0] if image_urls else "",
                                                                    width=500,
                                                                    height=300,
                                                                    fit=ft.ImageFit.COVER,
                                                                    border_radius=ft.border_radius.all(12),
                                                                ) if image_urls else ft.Column(
                                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                    controls=[
                                                                        ft.Icon(
                                                                            ft.Icons.IMAGE_OUTLINED,
                                                                            size=80,
                                                                            color=self.colors["text_light"]
                                                                        ),
                                                                        ft.Text(
                                                                            "No Image Available",
                                                                            color=self.colors["text_light"],
                                                                            size=14
                                                                        )
                                                                    ]
                                                                )
                                                            ),
                                                            # Three smaller images below
                                                            ft.Row(
                                                                spacing=10,
                                                                controls=[
                                                                    # Photo 2
                                                                    ft.Container(
                                                                        expand=True,
                                                                        height=150,
                                                                        bgcolor=ft.Colors.with_opacity(0.4, self.colors["border"]),
                                                                        border_radius=10,
                                                                        ink=True,
                                                                        on_click=lambda e, i=1: show_image_viewer(i) if len(image_urls) > i else None,
                                                                        content=ft.Image(
                                                                            src=image_urls[1] if len(image_urls) > 1 else "",
                                                                            fit=ft.ImageFit.COVER,
                                                                            border_radius=ft.border_radius.all(10),
                                                                        ) if len(image_urls) > 1 else ft.Column(
                                                                            alignment=ft.MainAxisAlignment.CENTER,
                                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                            controls=[
                                                                                ft.Icon(ft.Icons.IMAGE_OUTLINED, size=40, color=self.colors["text_light"]),
                                                                                ft.Text("Photo 2", color=self.colors["text_light"], size=12)
                                                                            ]
                                                                        )
                                                                    ),
                                                                    # Photo 3
                                                                    ft.Container(
                                                                        expand=True,
                                                                        height=150,
                                                                        bgcolor=ft.Colors.with_opacity(0.4, self.colors["border"]),
                                                                        border_radius=10,
                                                                        ink=True,
                                                                        on_click=lambda e, i=2: show_image_viewer(i) if len(image_urls) > i else None,
                                                                        content=ft.Image(
                                                                            src=image_urls[2] if len(image_urls) > 2 else "",
                                                                            fit=ft.ImageFit.COVER,
                                                                            border_radius=ft.border_radius.all(10),
                                                                        ) if len(image_urls) > 2 else ft.Column(
                                                                            alignment=ft.MainAxisAlignment.CENTER,
                                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                            controls=[
                                                                                ft.Icon(ft.Icons.IMAGE_OUTLINED, size=40, color=self.colors["text_light"]),
                                                                                ft.Text("Photo 3", color=self.colors["text_light"], size=12)
                                                                            ]
                                                                        )
                                                                    ),
                                                                    # Photo 4
                                                                    ft.Container(
                                                                        expand=True,
                                                                        height=150,
                                                                        bgcolor=ft.Colors.with_opacity(0.4, self.colors["border"]),
                                                                        border_radius=10,
                                                                        ink=True,
                                                                        on_click=lambda e, i=3: show_image_viewer(i) if len(image_urls) > i else None,
                                                                        content=ft.Image(
                                                                            src=image_urls[3] if len(image_urls) > 3 else "",
                                                                            fit=ft.ImageFit.COVER,
                                                                            border_radius=ft.border_radius.all(10),
                                                                        ) if len(image_urls) > 3 else ft.Column(
                                                                            alignment=ft.MainAxisAlignment.CENTER,
                                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                            controls=[
                                                                                ft.Icon(ft.Icons.IMAGE_OUTLINED, size=40, color=self.colors["text_light"]),
                                                                                ft.Text("Photo 4", color=self.colors["text_light"], size=12)
                                                                            ]
                                                                        )
                                                                    ),
                                                                ]
                                                            )
                                                        ]
                                                    )
                                                ]
                                            )
                                        ),

                                        # Description (Right Side)
                                        ft.Container(
                                            expand=True,
                                            content=ft.Column(
                                                spacing=15,
                                                controls=[
                                                    ft.Text(
                                                        "Description",
                                                        size=22,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=self.colors["text_dark"]
                                                    ),
                                                    ft.Container(
                                                        bgcolor=self.colors["background"],
                                                        padding=20,
                                                        border_radius=12,
                                                        height=460,
                                                        border=ft.border.all(1, self.colors["border"]),
                                                        content=ft.Column(
                                                            scroll=ft.ScrollMode.AUTO,
                                                            controls=[
                                                                ft.Text(
                                                                    property_data.get("description", "No description available"),
                                                                    size=15,
                                                                    color=self.colors["text_light"],
                                                                    text_align=ft.TextAlign.JUSTIFY
                                                                )
                                                            ]
                                                        )
                                                    )
                                                ]
                                            )
                                        )
                                    ]
                                )
                            ),

                            # Property Details and Amenities Side by Side
                            ft.Container(
                                bgcolor=ft.Colors.with_opacity(0.95, self.colors["card_bg"]),
                                padding=25,
                                border_radius=12,
                                border=ft.border.all(1, self.colors["border"]),
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=15,
                                    color=ft.Colors.with_opacity(0.08, self.colors["text_light"]),
                                ),
                                content=ft.Row(
                                    spacing=25,
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                    controls=[
                                        # Property Details (Left Side)
                                        ft.Container(
                                            expand=1,
                                            content=ft.Column(
                                                spacing=20,
                                                controls=[
                                                    ft.Text(
                                                        "Property Details",
                                                        size=22,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=self.colors["text_dark"]
                                                    ),
                                                    ft.Row(
                                                        wrap=True,
                                                        spacing=20,
                                                        run_spacing=20,
                                                        controls=[
                                                            ft.Container(
                                                                bgcolor=self.colors["background"],
                                                                padding=20,
                                                                border_radius=10,
                                                                border=ft.border.all(1, self.colors["border"]),
                                                                content=ft.Column([
                                                                    ft.Icon(ft.Icons.MEETING_ROOM, size=36, color=self.colors["primary"]),
                                                                    ft.Text("Room Type", size=13, color=self.colors["text_light"]),
                                                                    ft.Text(
                                                                        property_data.get("room_type", "N/A"),
                                                                        size=18,
                                                                        weight=ft.FontWeight.BOLD,
                                                                        color=self.colors["text_dark"]
                                                                    )
                                                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                                                            ),
                                                            ft.Container(
                                                                bgcolor=self.colors["background"],
                                                                padding=20,
                                                                border_radius=10,
                                                                border=ft.border.all(1, self.colors["border"]),
                                                                content=ft.Column([
                                                                    ft.Icon(
                                                                        ft.Icons.CHECK_CIRCLE if is_available else ft.Icons.CANCEL,
                                                                        size=36,
                                                                        color=self.colors["available"] if is_available else self.colors["unavailable"]
                                                                    ),
                                                                    ft.Text("Availability", size=13, color=self.colors["text_light"]),
                                                                    ft.Text(
                                                                        property_data.get("availability_status", "N/A"),
                                                                        size=18,
                                                                        weight=ft.FontWeight.BOLD,
                                                                        color=self.colors["available"] if is_available else self.colors["unavailable"]
                                                                    )
                                                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                                                            ),
                                                            ft.Container(
                                                                bgcolor=self.colors["background"],
                                                                padding=20,
                                                                border_radius=10,
                                                                border=ft.border.all(1, self.colors["border"]),
                                                                content=ft.Column([
                                                                    ft.Icon(ft.Icons.BED, size=36, color=self.colors["primary"]),
                                                                    ft.Text("Available Rooms", size=13, color=self.colors["text_light"]),
                                                                    ft.Text(
                                                                        f"{property_data.get('available_rooms', 0)}/{property_data.get('total_rooms', 0)}",
                                                                        size=18,
                                                                        weight=ft.FontWeight.BOLD,
                                                                        color=self.colors["text_dark"]
                                                                    )
                                                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            )
                                        ),

                                        # Amenities (Right Side)
                                        ft.Container(
                                            expand=1,
                                            content=ft.Column(
                                                spacing=20,
                                                controls=[
                                                    ft.Text(
                                                        "Amenities & Features",
                                                        size=22,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=self.colors["text_dark"]
                                                    ),
                                                    ft.Row(
                                                        wrap=True,
                                                        spacing=12,
                                                        run_spacing=12,
                                                        controls=amenity_chips
                                                    ) if amenities_list else ft.Text(
                                                        "No amenities listed",
                                                        size=15,
                                                        color=self.colors["text_light"]
                                                    )
                                                ]
                                            )
                                        )
                                    ]
                                )
                            ),

                            # Action Button Section
                            ft.Container(
                                bgcolor=ft.Colors.with_opacity(0.95, self.colors["card_bg"]),
                                padding=30,
                                border_radius=12,
                                border=ft.border.all(1, self.colors["border"]),
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=15,
                                    color=ft.Colors.with_opacity(0.08, self.colors["text_light"]),
                                ),
                                alignment=ft.alignment.center,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            spacing=15,
                                            controls=[
                                                action_button,
                                                ft.Text(
                                                    "Sign in to make a reservation" if not user_role else "",
                                                    size=13,
                                                    color=self.colors["text_light"],
                                                    italic=True
                                                ) if is_available else ft.Text(
                                                    "This property is currently not available",
                                                    size=13,
                                                    color=self.colors["unavailable"],
                                                    italic=True,
                                                    weight=ft.FontWeight.W_500
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ),

                            ft.Container(height=20),
                        ]
                    )
                )
            ]
        )
