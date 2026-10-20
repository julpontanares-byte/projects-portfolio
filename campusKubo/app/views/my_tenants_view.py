"""My Tenants view for Property Managers"""
import os
import flet as ft
from typing import Optional, List, Dict, Any
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


class MyTenantsView:
    def __init__(self, page: ft.Page, property_id: Optional[int] = None):
        self.page = page
        self.property_id = property_id
        self.session = SessionState(page)
        self.current_sort = "name_az"
        self.current_filter = "all"
        self.all_data = []

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

        # If property_id is provided, show tenants for that property
        selected_property = None
        if self.property_id:
            for prop in properties:
                if self._safe_get(prop, "id", 0) == self.property_id:
                    selected_property = prop
                    break

        return self._build_tenants_management(selected_property)

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
        full_name = profile.get("full_name") if profile else self.session.get_full_name() or "User"
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
                on_click=lambda e, pid=prop_id: self.page.go(f"/my-tenants/{pid}"),
                tooltip=f"View tenants for {prop_name}",
            )
            property_cards.append(property_card)

        return ft.View(
            "/my-tenants",
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
                                            "Select a property to view its tenants",
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

    def _build_tenants_management(self, selected_property):
        """Build tenants management view for a specific property"""
        user_id = self.session.get_user_id()

        # Get user avatar
        profile = get_user_by_id(user_id) if user_id else None
        full_name = (profile.get("full_name") if profile else None) or self.session.get_full_name() or "User"
        pm_initials = "".join([part[0].upper() for part in full_name.split()[:2] if part]) or "U"

        tenant_avatar = ft.Container(
            content=ft.CircleAvatar(
                content=ft.Text(pm_initials, color="white", weight="bold"),
                bgcolor="#0078FF",
                radius=18,
            ),
            on_click=lambda e: self.page.go("/pm/profile"),
            tooltip="Open profile",
        )

        # Load tenant data
        self._load_tenants(user_id)

        # Refs for dynamic updates
        table_rows_ref = ft.Ref[ft.Column]()
        sort_by_text = ft.Ref[ft.Text]()
        filter_by_text = ft.Ref[ft.Text]()

        # Create table rows
        table_rows = ft.Column(
            ref=table_rows_ref,
            spacing=0,
            controls=[self._create_table_row(item) for item in self.all_data],
            scroll="AUTO",
            expand=True
        )

        # Get property name
        property_name = "My Tenants"
        if selected_property:
            property_name = self._safe_get(selected_property, "property_name", "") or "My Tenants"

        return ft.View(
            f"/my-tenants/{self.property_id}" if self.property_id else "/my-tenants",
            [
                ft.Container(
                    expand=True,
                    bgcolor="#F5F7FA",
                    content=ft.Column(
                        spacing=0,
                        controls=[
                            # Header
                            ft.Container(
                                padding=ft.padding.all(24),
                                bgcolor="#FFFFFF",
                                content=ft.Row(
                                    controls=[
                                        tenant_avatar,
                                        ft.Text(
                                            property_name,
                                            size=28,
                                            weight="bold",
                                            color="#1A1A1A"
                                        ),
                                        ft.Container(expand=True),
                                    ],
                                    spacing=12,
                                    vertical_alignment="center"
                                )
                            ),
                            # Controls Section
                            ft.Container(
                                padding=ft.padding.all(24),
                                bgcolor="#F5F7FA",
                                content=ft.Column(
                                    spacing=16,
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Text("Sort by:", size=14, color="#666666"),
                                                ft.Container(
                                                    content=ft.Text(
                                                        "Name (A-Z)",
                                                        ref=sort_by_text,
                                                        size=14,
                                                        color="#1A1A1A"
                                                    ),
                                                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                                    bgcolor="#FFFFFF",
                                                    border_radius=8,
                                                ),
                                                ft.Container(width=20),
                                                ft.Text("Filter by:", size=14, color="#666666"),
                                                ft.Container(
                                                    content=ft.Text(
                                                        "All",
                                                        ref=filter_by_text,
                                                        size=14,
                                                        color="#1A1A1A"
                                                    ),
                                                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                                    bgcolor="#FFFFFF",
                                                    border_radius=8,
                                                ),
                                                ft.Container(expand=True),
                                                ft.ElevatedButton(
                                                    "Add new Tenant",
                                                    icon=ft.Icons.PERSON_ADD,
                                                    style=ft.ButtonStyle(
                                                        color="white",
                                                        bgcolor="#0078FF",
                                                    ),
                                                    on_click=lambda e: self._show_add_tenant_dialog()
                                                )
                                            ],
                                            spacing=8
                                        )
                                    ]
                                )
                            ),
                            # Main Content - Table
                            ft.Container(
                                expand=True,
                                padding=ft.padding.only(left=24, right=24, top=24, bottom=24),
                                content=ft.Container(
                                    bgcolor="#FFFFFF",
                                    border_radius=8,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0,
                                        blur_radius=4,
                                        color="#00000010",
                                        offset=ft.Offset(0, 2)
                                    ),
                                    content=ft.Column(
                                        spacing=0,
                                        controls=[
                                            # Header
                                            ft.Container(
                                                padding=ft.padding.all(16),
                                                bgcolor="#F5F7FA",
                                                border_radius=ft.border_radius.only(top_left=8, top_right=8),
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Container(
                                                            content=ft.Text("Name", size=14, weight="bold", color="#1A1A1A"),
                                                            expand=2,
                                                            alignment=ft.alignment.center
                                                        ),
                                                        ft.Container(
                                                            content=ft.Text("Room Number", size=14, weight="bold", color="#1A1A1A"),
                                                            expand=1,
                                                            alignment=ft.alignment.center
                                                        ),
                                                        ft.Container(
                                                            content=ft.Text("Room Type", size=14, weight="bold", color="#1A1A1A"),
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
                                                        ft.Container(width=24),
                                                    ],
                                                    spacing=12
                                                )
                                            ),
                                            # Rows
                                            table_rows
                                        ]
                                    )
                                )
                            )
                        ]
                    )
                )
            ]
        )

    def _load_tenants(self, user_id):
        """Load tenant data from database"""
        tenants = get_tenants(user_id)
        self.all_data.clear()

        # Filter and sort tenants
        filtered_tenants = self._filter_tenants(tenants)
        sorted_tenants = self._sort_tenants(filtered_tenants)

        # Convert to display format
        for tenant in sorted_tenants:
            name = tenant.get("name", "") if tenant.get("name") else ""
            avatar_letter = name[0].upper() if name else "M"
            self.all_data.append({
                "id": tenant.get("id"),
                "name": name,
                "room_number": tenant.get("room_number", ""),
                "room_type": tenant.get("room_type", ""),
                "status": tenant.get("status", ""),
                "avatar": avatar_letter,
                "has_avatar": True
            })

    def _filter_tenants(self, tenants):
        """Filter tenants based on current filter"""
        if self.current_filter == "all":
            return tenants

        filtered = []
        for tenant in tenants:
            status = tenant.get("status", "").lower()
            if self.current_filter == "occupied" and "occupied" in status:
                filtered.append(tenant)
            elif self.current_filter == "pending" and "pending" in status:
                filtered.append(tenant)
            elif self.current_filter == "vacant" and "vacant" in status:
                filtered.append(tenant)

        return filtered

    def _sort_tenants(self, tenants):
        """Sort tenants based on current sort"""
        if self.current_sort == "name_az":
            return sorted(tenants, key=lambda x: x.get("name", "").lower())
        elif self.current_sort == "name_za":
            return sorted(tenants, key=lambda x: x.get("name", "").lower(), reverse=True)
        return tenants

    def _create_table_row(self, item):
        """Create a tenant table row"""
        status_color = "#4CAF50" if item["status"] == "Occupied" else "#FF9800"
        avatar_color = "#2196F3" if ord(item["avatar"]) % 2 == 0 else "#E91E63"

        return ft.Container(
            content=ft.Row(
                controls=[
                    # Name with avatar
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.CircleAvatar(
                                    content=ft.Text(item["avatar"], color="white", weight="bold", size=12),
                                    bgcolor=avatar_color,
                                    radius=16,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text(item["name"], size=14, color="#1A1A1A", weight="normal"),
                                        ft.Container(
                                            width=6,
                                            height=6,
                                            border_radius=3,
                                            bgcolor="#0078FF"
                                        )
                                    ],
                                    spacing=6,
                                    tight=True
                                )
                            ],
                            spacing=8,
                            tight=True
                        ),
                        expand=2,
                        alignment=ft.alignment.center
                    ),
                    # Room Number
                    ft.Container(
                        content=ft.Text(item["room_number"], size=14, color="#1A1A1A", weight="normal"),
                        expand=1,
                        alignment=ft.alignment.center
                    ),
                    # Room Type
                    ft.Container(
                        content=ft.Text(item["room_type"], size=14, color="#1A1A1A", weight="normal"),
                        expand=2,
                        alignment=ft.alignment.center
                    ),
                    # Status
                    ft.Container(
                        content=ft.Container(
                            content=ft.Text(
                                item["status"],
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
                                    on_click=lambda e, tid=item["id"]: self._edit_tenant(tid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color="#F44336",
                                    icon_size=18,
                                    tooltip="Delete",
                                    on_click=lambda e, tid=item["id"], name=item["name"]: self._delete_tenant(tid, name)
                                )
                            ],
                            spacing=4,
                            tight=True
                        ),
                        width=120,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(width=24),
                ],
                spacing=12,
                vertical_alignment="center"
            ),
            padding=ft.padding.symmetric(horizontal=0, vertical=12),
            border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0"))
        )

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
                self.page.go(f"/my-tenants/{self.property_id}")
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

    def _edit_tenant(self, tenant_id):
        """Edit tenant handler"""
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
                self.page.go(f"/my-tenants/{self.property_id}")
            else:
                self.page.open(ft.SnackBar(
                    content=ft.Text("Failed to update tenant"),
                    bgcolor="#F44336"


                ))
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Tenant", size=20, weight=ft.FontWeight.BOLD),
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

    def _delete_tenant(self, tenant_id, name):
        """Delete tenant handler"""
        # Simple confirmation via snackbar for now
        if delete_tenant(tenant_id):
            self.page.open(ft.SnackBar(
                content=ft.Text(f"Tenant {name} deleted successfully"),
                bgcolor="#4CAF50"


            ))
            self.page.go(f"/my-tenants/{self.property_id}")
        else:
            self.page.open(ft.SnackBar(
                content=ft.Text("Failed to delete tenant"),
                bgcolor="#F44336"


            ))
        self.page.update()
