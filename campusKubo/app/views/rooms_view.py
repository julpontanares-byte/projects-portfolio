"""Rooms management view for Property Managers"""
import os
import flet as ft
from typing import Optional
from storage.db import (
    get_listings,
    get_listing_images,
    get_tenants,
    create_tenant,
    update_tenant,
    delete_tenant,
    get_user_by_id
)
from state.session_state import SessionState


class RoomsView:
    def __init__(self, page: ft.Page, property_id: Optional[int] = None):
        self.page = page
        self.property_id = property_id
        self.session = SessionState(page)

    def build(self):
        page = self.page
        user_id = self.session.get_user_id()
        if not user_id:
            page.go("/login")
            return None

        # Get all properties for this user
        properties = get_listings(user_id)

        # If no property selected, show property selection screen
        if not self.property_id and properties:
            return self._build_property_selection(properties)

        # If property_id is provided, show rooms for that property
        selected_property = None
        if self.property_id:
            for prop in properties:
                if self._safe_get(prop, "id", 0) == self.property_id:
                    selected_property = prop
                    break

        return self._build_rooms_management(selected_property)

    def _safe_get(self, prop, key, default=None):
        """Safely get value from property (handles sqlite3.Row)"""
        if default is None:
            default = ""
        try:
            if hasattr(prop, "get"):
                return prop.get(key, default)
            elif hasattr(prop, "keys") and key in prop.keys():
                return prop[key]
            else:
                return default
        except (KeyError, TypeError, AttributeError):
            return default

    def _build_property_selection(self, properties):
        """Build property selection view"""
        user_id = self.session.get_user_id()

        # Get user avatar
        profile = get_user_by_id(user_id) if user_id else None
        full_name = (profile.get("full_name") if profile else None) or self.session.get_full_name() or "User"
        pm_initials = "".join([part[0].upper() for part in full_name.split()[:2] if part]) or "U"

        pm_avatar = ft.Container(
            content=ft.CircleAvatar(
                content=ft.Text(pm_initials, color="white", weight=ft.FontWeight.BOLD),
                bgcolor="#0078FF",
                radius=18,
            ),
            on_click=lambda e: self.page.go("/pm/profile"),
        )

        # Build property cards
        property_cards = []
        for prop in properties:
            prop_name = self._safe_get(prop, "property_name", "") or self._safe_get(prop, "address", "Unnamed Property")
            prop_id = self._safe_get(prop, "id", 0)

            # Get main image
            images = get_listing_images(prop_id)
            main_image = images[0] if images else None

            property_card = ft.Container(
                width=300,
                height=200,
                border_radius=12,
                bgcolor="#FFFFFF",
                border=ft.border.all(1, "#E0E0E0"),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color="#00000008",
                    offset=ft.Offset(0, 2)
                ),
                content=ft.Column(
                    spacing=0,
                    controls=[
                        # Image
                        ft.Container(
                            width=300,
                            height=120,
                            border_radius=ft.border_radius.only(top_left=12, top_right=12),
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            content=ft.Image(
                                src=main_image,
                                width=300,
                                height=120,
                                fit=ft.ImageFit.COVER,
                            ) if main_image and os.path.exists(main_image) else ft.Container(
                                content=ft.Icon(ft.Icons.HOME, size=40, color="#999"),
                                alignment=ft.alignment.center
                            )
                        ),
                        # Property name
                        ft.Container(
                            content=ft.Text(
                                prop_name,
                                size=18,
                                weight="bold",
                                color="#1A1A1A"
                            ),
                            padding=ft.padding.all(16),
                            alignment=ft.alignment.center
                        )
                    ]
                ),
                on_click=lambda e, pid=prop_id: self.page.go(f"/rooms/{pid}"),
                tooltip=f"View rooms for {prop_name}",
            )
            property_cards.append(property_card)

        return ft.View(
            "/rooms",
            [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            # Header
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        pm_avatar,
                                        ft.Text("Select Property", size=24, weight="bold", color="#1A1A1A"),
                                    ],
                                    spacing=12,
                                    vertical_alignment="center"
                                ),
                                padding=ft.padding.symmetric(horizontal=24, vertical=20),
                                bgcolor="#FFFFFF",
                                border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0"))
                            ),
                            # Property selection grid
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            "Select a property to view its rooms",
                                            size=16,
                                            color="#666",
                                            text_align="left"
                                        ),
                                        ft.Container(height=20),
                                        ft.Row(
                                            controls=property_cards,
                                            wrap=True,
                                            spacing=20,
                                            alignment="start"
                                        ) if property_cards else ft.Container(
                                            content=ft.Column(
                                                controls=[
                                                    ft.Icon(ft.Icons.HOME, size=60, color="#999"),
                                                    ft.Text(
                                                        "No properties found",
                                                        size=16,
                                                        color="#666"
                                                    ),
                                                    ft.TextButton(
                                                        "Add New Property",
                                                        on_click=lambda e: self.page.go("/pm/add")
                                                    )
                                                ],
                                                horizontal_alignment="center",
                                                spacing=12
                                            ),
                                            padding=40
                                        )
                                    ],
                                    horizontal_alignment="start",
                                    spacing=0
                                ),
                                padding=ft.padding.all(24),
                                expand=True
                            )
                        ],
                        spacing=0
                    ),
                    expand=True
                )
            ],
            bgcolor="#F5F7FA",
            padding=0
        )

    def _build_rooms_management(self, selected_property):
        """Build rooms management view for a specific property"""
        user_id = self.session.get_user_id()
        if not user_id:
            self.page.go("/login")
            return ft.View()

        # Get user avatar
        profile = get_user_by_id(user_id)
        full_name = (profile.get("full_name") if profile else None) or self.session.get_full_name() or "User"
        pm_initials = "".join([part[0].upper() for part in full_name.split()[:2] if part]) or "U"

        pm_avatar = ft.Container(
            content=ft.CircleAvatar(
                content=ft.Text(pm_initials, color="white", weight=ft.FontWeight.BOLD),
                bgcolor="#0078FF",
                radius=18,
            ),
            on_click=lambda e: self.page.go("/pm/profile"),
        )

        # Generate sample room data with sequential numbers
        sample_rooms = self._generate_sample_rooms()

        # Get actual tenant data and merge
        tenants = get_tenants(user_id)
        self._merge_tenant_data(sample_rooms, tenants)

        # Group rooms by type
        rooms_by_category = self._group_rooms_by_type(sample_rooms)

        # Create table sections
        category_tables = self._create_category_tables(rooms_by_category, tenants)

        # Get property name
        property_name = "Rooms"
        if selected_property:
            property_name = self._safe_get(selected_property, "property_name", "") or self._safe_get(selected_property, "address", "Rooms")

        return ft.View(
            f"/rooms/{self.property_id}" if self.property_id else "/rooms",
            [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            # Header
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        pm_avatar,
                                        ft.Column(
                                            controls=[
                                                ft.Text(property_name, size=24, weight="bold", color="#1A1A1A"),
                                                ft.Text("Rooms", size=14, color="#666") if selected_property else ft.Container(),
                                            ],
                                            spacing=2,
                                            tight=True
                                        ),
                                        ft.Container(expand=True),
                                        ft.TextButton(
                                            "Back to Properties",
                                            on_click=lambda e: self.page.go("/rooms"),
                                            style=ft.ButtonStyle(color="#0078FF")
                                        ) if self.property_id else ft.Container(),
                                    ],
                                    spacing=12,
                                    vertical_alignment="center"
                                ),
                                padding=ft.padding.symmetric(horizontal=24, vertical=20),
                                bgcolor="#FFFFFF",
                                border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0"))
                            ),
                            # Content
                            ft.Container(
                                content=ft.Column(
                                    controls=category_tables,
                                    spacing=0,
                                    scroll=ft.ScrollMode.AUTO
                                ),
                                padding=ft.padding.all(24),
                                expand=True
                            )
                        ],
                        spacing=0,
                        tight=True
                    ),
                    expand=True
                )
            ],
            bgcolor="#F5F7FA",
            padding=0
        )

    def _generate_sample_rooms(self):
        """Generate sample room data (01-17)"""
        rooms = []
        room_num = 1

        # 5 Single rooms (01-05)
        for i in range(5):
            rooms.append({
                "room_number": f"{room_num:02d}",
                "room_type": "Single",
                "name": "Vacant",
                "status": "Vacant"
            })
            room_num += 1

        # 5 Double deck for 2 (06-10)
        for i in range(5):
            rooms.append({
                "room_number": f"{room_num:02d}",
                "room_type": "Double deck for two (2)",
                "name": "Vacant",
                "status": "Vacant"
            })
            room_num += 1

        # 4 Double deck for 4 (11-14)
        for i in range(4):
            rooms.append({
                "room_number": f"{room_num:02d}",
                "room_type": "Double deck for four (4)",
                "name": "Vacant",
                "status": "Vacant"
            })
            room_num += 1

        # 3 Studio type (15-17)
        for i in range(3):
            rooms.append({
                "room_number": f"{room_num:02d}",
                "room_type": "Studio Type",
                "name": "Vacant",
                "status": "Vacant"
            })
            room_num += 1

        return rooms

    def _merge_tenant_data(self, sample_rooms, tenants):
        """Merge tenant data into sample rooms"""
        tenant_dict = {}
        for tenant in tenants:
            room_key = tenant["room_number"]
            tenant_dict[room_key] = {
                "name": tenant["name"] if tenant["name"] else "Vacant",
                "status": tenant["status"],
                "room_type": tenant["room_type"] if tenant["room_type"] else None,
                "id": tenant["id"]
            }

        # Update sample rooms with actual tenant data
        for room in sample_rooms:
            if room["room_number"] in tenant_dict:
                tenant_data = tenant_dict[room["room_number"]]
                room["name"] = tenant_data["name"]
                room["status"] = tenant_data["status"]
                room["tenant_id"] = tenant_data["id"]
                if tenant_data["room_type"]:
                    room["room_type"] = tenant_data["room_type"]

    def _group_rooms_by_type(self, rooms):
        """Group rooms by room type"""
        rooms_by_category = {}
        for room in rooms:
            room_type = room["room_type"]
            if room_type not in rooms_by_category:
                rooms_by_category[room_type] = []
            rooms_by_category[room_type].append(room)
        return rooms_by_category

    def _create_category_tables(self, rooms_by_category, all_tenants):
        """Create table sections by category"""
        category_tables = []

        for room_type, rooms in rooms_by_category.items():
            # Create rows for this category
            table_rows = []
            for room in rooms:
                table_rows.append(self._create_room_row(room, all_tenants))

            # Category table section
            category_table = ft.Container(
                content=ft.Column(
                    controls=[
                        # Category header
                        ft.Container(
                            content=ft.Text(
                                room_type,
                                size=18,
                                weight="bold",
                                color="#1A1A1A"
                            ),
                            padding=ft.padding.symmetric(horizontal=24, vertical=16),
                            bgcolor="#F5F7FA",
                            border_radius=ft.border_radius.only(top_left=8, top_right=8)
                        ),
                        # Table header
                        ft.Container(
                            padding=ft.padding.all(16),
                            bgcolor="#F5F7FA",
                            border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0")),
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text("Room Number", size=14, weight="bold", color="#1A1A1A"),
                                        expand=1,
                                        alignment=ft.alignment.center
                                    ),
                                    ft.Container(
                                        content=ft.Text("Tenant Name", size=14, weight="bold", color="#1A1A1A"),
                                        expand=2,
                                        alignment=ft.alignment.center
                                    ),
                                    ft.Container(
                                        content=ft.Text("Status", size=14, weight="bold", color="#1A1A1A"),
                                        expand=1,
                                        alignment=ft.alignment.center
                                    ),
                                    ft.Container(
                                        content=ft.Text("Actions", size=14, weight="bold", color="#1A1A1A"),
                                        width=120,
                                        alignment=ft.alignment.center
                                    ),
                                ],
                                spacing=12
                            )
                        ),
                        # Table rows
                        ft.Column(controls=table_rows, spacing=0, tight=True)
                    ],
                    spacing=0,
                    tight=True
                ),
                bgcolor="#FFFFFF",
                border_radius=8,
                border=ft.border.all(1, "#E0E0E0"),
                margin=ft.margin.only(bottom=24)
            )
            category_tables.append(category_table)

        return category_tables

    def _create_room_row(self, room, all_tenants):
        """Create a room table row"""
        status_color = "#4CAF50" if room["status"] == "Occupied" else "#FF9800"
        avatar_letter = room["name"][0].upper() if room["name"] and room["name"] != "Vacant" else "V"
        avatar_color = "#2196F3" if ord(avatar_letter) % 2 == 0 else "#E91E63"

        tenant_id = room.get("tenant_id", None)

        row = ft.Container(
            content=ft.Row(
                controls=[
                    # Room Number
                    ft.Container(
                        content=ft.Text(room["room_number"], size=14, color="#1A1A1A", weight="normal"),
                        expand=1,
                        alignment=ft.alignment.center
                    ),
                    # Tenant Name with avatar
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.CircleAvatar(
                                    content=ft.Text(avatar_letter, color="white", weight="bold", size=12),
                                    bgcolor=avatar_color,
                                    radius=16,
                                ),
                                ft.Text(room["name"], size=14, color="#1A1A1A", weight="normal"),
                            ],
                            spacing=8,
                            tight=True
                        ),
                        expand=2,
                        alignment=ft.alignment.center
                    ),
                    # Status
                    ft.Container(
                        content=ft.Container(
                            content=ft.Text(
                                room["status"],
                                size=12,
                                color="#FFFFFF",
                                weight="normal"
                            ),
                            padding=ft.padding.symmetric(horizontal=6, vertical=3),
                            bgcolor=status_color,
                            border_radius=4,
                            alignment=ft.alignment.center
                        ),
                        expand=1,
                        alignment=ft.alignment.center
                    ),
                    # Actions
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color="#0078FF",
                                    icon_size=18,
                                    tooltip="Edit",
                                    on_click=lambda e, r=room, tid=tenant_id: self._edit_room(r, tid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color="#F44336",
                                    icon_size=18,
                                    tooltip="Delete",
                                    on_click=lambda e, r=room, tid=tenant_id: self._delete_room(r, tid)
                                )
                            ],
                            spacing=4,
                            tight=True
                        ),
                        width=120,
                        alignment=ft.alignment.center
                    ),
                ],
                spacing=12,
                vertical_alignment="center"
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0"))
        )
        return row

    def _show_add_tenant_dialog(self):
        """Show add tenant dialog"""
        # Form fields
        tenant_name = ft.TextField(
            label="Tenant Name",
            hint_text="Enter full name",
            autofocus=True,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        room_number = ft.Dropdown(
            label="Room Number",
            hint_text="Select room",
            options=[
                ft.dropdown.Option(f"{i:02d}") for i in range(1, 18)
            ],
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        room_type = ft.Dropdown(
            label="Room Type",
            hint_text="Select type",
            options=[
                ft.dropdown.Option("Single"),
                ft.dropdown.Option("Double deck for 2"),
                ft.dropdown.Option("Double deck for 4"),
                ft.dropdown.Option("Studio Type"),
            ],
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        status = ft.Dropdown(
            label="Status",
            hint_text="Select status",
            value="Occupied",
            options=[
                ft.dropdown.Option("Occupied"),
                ft.dropdown.Option("Pending"),
                ft.dropdown.Option("Vacant"),
            ],
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def save_tenant(e):
            # Validation
            if not tenant_name.value or not tenant_name.value.strip():
                self.page.open(ft.SnackBar(
                    content=ft.Text("Tenant name is required"),
                    bgcolor="#F44336"


                ))
                self.page.update()
                return

            if not room_number.value:
                self.page.open(ft.SnackBar(
                    content=ft.Text("Room number is required"),
                    bgcolor="#F44336"


                ))
                self.page.update()
                return

            if not room_type.value:
                self.page.open(ft.SnackBar(
                    content=ft.Text("Room type is required"),
                    bgcolor="#F44336"


                ))
                self.page.update()
                return

            # Generate avatar from initials
            name_parts = tenant_name.value.strip().split()
            avatar = "".join([part[0].upper() for part in name_parts[:2] if part]) or "T"

            # Create tenant
            user_id = self.session.get_user_id()
            tenant_id = create_tenant(
                owner_id=user_id,
                name=tenant_name.value.strip(),
                room_number=room_number.value,
                room_type=room_type.value,
                status=status.value,
                avatar=avatar
            )

            if tenant_id:
                dialog.open = False
                self.page.open(ft.SnackBar(
                    content=ft.Text("Tenant added successfully"),
                    bgcolor="#4CAF50"


                ))
                # Refresh the view
                self.page.go(f"/rooms/{self.property_id}")
            else:
                self.page.open(ft.SnackBar(
                    content=ft.Text("Failed to add tenant"),
                    bgcolor="#F44336"


                ))
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add New Tenant", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    tight=True,
                    spacing=15,
                    controls=[
                        tenant_name,
                        room_number,
                        room_type,
                        status,
                    ]
                )
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Add Tenant",
                    on_click=save_tenant,
                    style=ft.ButtonStyle(
                        bgcolor="#333333",
                        color="white",
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _edit_room(self, room, tenant_id):
        """Edit room/tenant handler"""
        if not tenant_id:
            # No tenant assigned, show add dialog
            self._show_add_tenant_dialog()
            return

        # Get tenant data
        user_id = self.session.get_user_id()
        tenants = get_tenants(user_id)
        tenant = next((t for t in tenants if t["id"] == tenant_id), None)

        if not tenant:
            self.page.open(ft.SnackBar(
                content=ft.Text("Tenant not found"),
                bgcolor="#F44336"


            ))
            self.page.update()
            return

        # Form fields with existing data
        tenant_name = ft.TextField(
            label="Tenant Name",
            value=tenant["name"],
            autofocus=True,
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        room_number = ft.Dropdown(
            label="Room Number",
            value=tenant["room_number"],
            options=[
                ft.dropdown.Option(f"{i:02d}") for i in range(1, 18)
            ],
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        room_type = ft.Dropdown(
            label="Room Type",
            value=tenant["room_type"],
            options=[
                ft.dropdown.Option("Single"),
                ft.dropdown.Option("Double deck for 2"),
                ft.dropdown.Option("Double deck for 4"),
                ft.dropdown.Option("Studio Type"),
            ],
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        status = ft.Dropdown(
            label="Status",
            value=tenant["status"],
            options=[
                ft.dropdown.Option("Occupied"),
                ft.dropdown.Option("Pending"),
                ft.dropdown.Option("Vacant"),
            ],
            border_radius=8,
            bgcolor="#FAFAFA",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def update_tenant_data(e):
            # Validation
            if not tenant_name.value or not tenant_name.value.strip():
                self.page.open(ft.SnackBar(
                    content=ft.Text("Tenant name is required"),
                    bgcolor="#F44336"


                ))
                self.page.update()
                return

            # Generate new avatar if name changed
            name_parts = tenant_name.value.strip().split()
            avatar = "".join([part[0].upper() for part in name_parts[:2] if part]) or "T"

            # Update tenant
            success = update_tenant(
                tenant_id,
                name=tenant_name.value.strip(),
                room_number=room_number.value,
                room_type=room_type.value,
                status=status.value,
                avatar=avatar
            )

            if success:
                dialog.open = False
                self.page.open(ft.SnackBar(
                    content=ft.Text("Tenant updated successfully"),
                    bgcolor="#4CAF50"


                ))
                # Refresh the view
                self.page.go(f"/rooms/{self.property_id}")
            else:
                self.page.open(ft.SnackBar(
                    content=ft.Text("Failed to update tenant"),
                    bgcolor="#F44336"


                ))
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Tenant", size=20, weight="bold"),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    tight=True,
                    spacing=15,
                    controls=[
                        tenant_name,
                        room_number,
                        room_type,
                        status,
                    ]
                )
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Save Changes",
                    on_click=update_tenant_data,
                    style=ft.ButtonStyle(
                        bgcolor="#333333",
                        color="white",
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _delete_room(self, room, tenant_id):
        """Delete room handler - placeholder"""
        if not tenant_id:
            self.page.open(ft.SnackBar(
                content=ft.Text("No tenant assigned to this room"),
                bgcolor="#FF9800"


            ))
            self.page.update()
            return

        # Delete tenant
        if delete_tenant(tenant_id):
            self.page.open(ft.SnackBar(
                content=ft.Text("Tenant deleted successfully"),
                bgcolor="#4CAF50"


            ))
            self.page.go(f"/rooms/{self.property_id}")
        else:
            self.page.open(ft.SnackBar(
                content=ft.Text("Failed to delete tenant"),
                bgcolor="#F44336"


            ))
        self.page.update()
