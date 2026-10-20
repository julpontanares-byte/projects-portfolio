"""
Listing cards used across CampusKubo roles.

The module now provides opinionated builders for:
- Property manager cards (horizontal layout with management actions)
- Tenant cards (vertical layout with save/unsave controls)
- Admin moderation cards (status-aware actions)
- Home/static cards for marketing pages

Legacy compatibility is preserved via the ``ListingCard`` class which now
delegates to the new helpers when possible.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional, Sequence, Union

import flet as ft

from models.listing import Listing
from storage.db import is_property_saved, save_property, unsave_property

ListingInput = Union[Listing, Dict[str, Any]]
ActionHandler = Optional[Callable[[ft.ControlEvent], None]]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def _listing_to_dict(listing: ListingInput) -> Dict[str, Any]:
    if isinstance(listing, dict):
        return dict(listing)

    if hasattr(listing, "to_dict"):
        try:
            return dict(listing.to_dict())
        except Exception:
            pass

    data: Dict[str, Any] = {}
    for attr in [
        "id",
        "listing_id",
        "property_name",
        "address",
        "price",
        "description",
        "status",
        "pm_id",
        "pm_email",
        "owner_name",
    ]:
        if hasattr(listing, attr):
            data[attr] = getattr(listing, attr)
    return data


def _format_price(value: Any, *, decimals: int = 0, suffix: str = "/month") -> str:
    try:
        numeric = float(str(value).replace("₱", "").replace(",", "").strip())
        formatted = f"₱{numeric:,.{decimals}f}" if decimals else f"₱{numeric:,.0f}"
    except (TypeError, ValueError):
        formatted = f"₱{value}" if value not in (None, "") else "₱0"
    return f"{formatted}{suffix}" if suffix else formatted


def _truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit - 3] + "..."


def _image_exists(path: Optional[str]) -> bool:
    return bool(path and (path.startswith("http") or os.path.exists(path)))


def _select_main_image(images: Optional[Sequence[str]]) -> Optional[str]:
    if not images:
        return None
    for img in images:
        if _image_exists(img):
            return img
    return None


def _build_availability_badge(is_available: bool) -> ft.Container:
    label = "Available" if is_available else "Occupied"
    color = "#4CAF50" if is_available else "#F44336"
    icon = ft.Icons.CHECK_CIRCLE if is_available else ft.Icons.CANCEL
    return ft.Container(
        content=ft.Row(
            spacing=6,
            controls=[
                ft.Icon(icon, size=14, color="white"),
                ft.Text(label, size=11, color="white", weight=ft.FontWeight.BOLD),
            ],
        ),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=20,
    )


def _build_image_block(
    image_path: Optional[str],
    *,
    width: int,
    height: int,
    is_available: bool,
    extra_overlays: Optional[Sequence[ft.Control]] = None,
) -> ft.Container:
    overlays = [
        ft.Container(
            content=_build_availability_badge(is_available),
            alignment=ft.alignment.top_left,
            margin=10,
        )
    ]
    if extra_overlays:
        overlays.extend(extra_overlays)

    image_control: ft.Control
    if _image_exists(image_path):
        image_control = ft.Image(src=image_path, width=width, height=height, fit=ft.ImageFit.COVER)
    else:
        image_control = ft.Container(
            width=width,
            height=height,
            bgcolor="#E0E0E0",
            content=ft.Icon(ft.Icons.HOME_WORK, size=52, color="#9E9E9E"),
            alignment=ft.alignment.center,
        )

    return ft.Container(
        width=width,
        height=height,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border_radius=ft.border_radius.all(12),
        content=ft.Stack(
            controls=[image_control, *overlays],
            expand=True,
        ),
    )


def _build_rating_row(rating: float = 4.5, reviews: int = 24) -> ft.Row:
    return ft.Row(
        spacing=4,
        controls=[
            ft.Icon(ft.Icons.STAR, size=16, color="#FFB800"),
            ft.Text(f"{rating:.1f}", size=13, weight=ft.FontWeight.BOLD, color="#333333"),
            ft.Text(f"({reviews} reviews)", size=11, color=ft.Colors.GREY_600),
        ],
    )


def _card_container(content: ft.Control, *, padding: ft.padding.Padding, width: Optional[int] = None) -> ft.Container:
    return ft.Container(
        width=width,
        padding=padding,
        bgcolor="#FFFFFF",
        border_radius=12,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=20,
            color="#00000010",
            offset=ft.Offset(0, 6),
        ),
        content=content,
    )


# ---------------------------------------------------------------------------
# Property Manager Listing Card
# ---------------------------------------------------------------------------
def create_pm_listing_card(
    listing: ListingInput,
    images: Optional[Sequence[str]] = None,
    is_available: bool = True,
    owner_id: Optional[int] = None,
    on_preview: ActionHandler = None,
    on_edit: ActionHandler = None,
    on_delete: ActionHandler = None,
) -> ft.Container:
    data = _listing_to_dict(listing)
    prop_name = data.get("property_name") or data.get("address") or "Listing"
    description = _truncate(str(data.get("description", "")), 200)
    price_text = _format_price(data.get("price", 0), decimals=2)
    main_image = _select_main_image(images) or data.get("image_url")

    content = ft.Row(
        spacing=18,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            _build_image_block(main_image, width=250, height=200, is_available=is_available),
            ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    ft.Text(prop_name, size=20, weight=ft.FontWeight.BOLD, color="#1A1A1A"),
                    _build_rating_row(),
                    ft.Text(description or "No description provided.", size=13, color="#555555", max_lines=3),
                    ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Icon(ft.Icons.PRICE_CHANGE, size=20, color="#0078FF"),
                            ft.Text(price_text, size=18, weight=ft.FontWeight.BOLD, color="#0078FF"),
                        ],
                    ),
                    ft.Row(
                        spacing=8,
                        wrap=True,
                        controls=[
                            ft.OutlinedButton(
                                "Preview",
                                icon=ft.Icons.VISIBILITY,
                                on_click=on_preview,
                                disabled=on_preview is None,
                            ),
                            ft.ElevatedButton(
                                "Edit",
                                icon=ft.Icons.EDIT,
                                on_click=on_edit,
                                disabled=on_edit is None,
                                style=ft.ButtonStyle(color="white", bgcolor="#0078FF"),
                            ),
                            ft.OutlinedButton(
                                "Delete",
                                icon=ft.Icons.DELETE_FOREVER,
                                on_click=on_delete,
                                disabled=on_delete is None,
                                style=ft.ButtonStyle(color="#C62828"),
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    return _card_container(content, padding=ft.padding.all(18))


# ---------------------------------------------------------------------------
# Tenant Listing Card
# ---------------------------------------------------------------------------
def create_tenant_listing_card(
    listing: ListingInput,
    image_url: Optional[str],
    is_available: bool,
    *,
    user_id: Optional[int] = None,
    show_save_button: bool = True,
    show_cta: bool = True,
    on_click: ActionHandler = None,
    page: Optional[ft.Page] = None,
) -> ft.Container:
    data = _listing_to_dict(listing)
    listing_id = data.get("id") or data.get("listing_id")
    prop_name = data.get("property_name") or data.get("address") or "Listing"
    price_text = _format_price(data.get("price", 0), decimals=0)
    subtitle = _truncate(str(data.get("description", "")), 90)

    saved_state = [False]
    if show_save_button and user_id and listing_id:
        saved_state[0] = is_property_saved(user_id, listing_id)

    heart_button: Optional[ft.IconButton] = None
    if show_save_button:
        heart_button = ft.IconButton(
            icon=ft.Icons.FAVORITE if saved_state[0] else ft.Icons.FAVORITE_BORDER,
            icon_color="#FF4D73" if saved_state[0] else "white",
            bgcolor="#0000004D",
            style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=8),
            disabled=not (user_id and listing_id),
        )

        def _toggle_save(_: ft.ControlEvent) -> None:
            if not (user_id and listing_id):
                return
            if saved_state[0]:
                changed = unsave_property(user_id, listing_id)
                if changed:
                    saved_state[0] = False
            else:
                changed = save_property(user_id, listing_id)
                if changed:
                    saved_state[0] = True

            heart_button.icon = ft.Icons.FAVORITE if saved_state[0] else ft.Icons.FAVORITE_BORDER
            heart_button.icon_color = "#FF4D73" if saved_state[0] else "white"
            heart_button.update()

            if page:
                msg = "Listing saved" if saved_state[0] else "Listing removed"
                page.open(ft.SnackBar(ft.Text(msg)))

        if user_id and listing_id:
            heart_button.on_click = _toggle_save

    overlays: list[ft.Control] = []
    if heart_button:
        overlays.append(ft.Container(content=heart_button, alignment=ft.alignment.top_right, margin=10))

    image_block = _build_image_block(image_url, width=220, height=150, is_available=is_available, extra_overlays=overlays)

    body_controls: list[ft.Control] = [
        ft.Text(prop_name, size=16, weight=ft.FontWeight.BOLD, color="#1A1A1A", max_lines=2),
        ft.Text(price_text, color="#0078FF", size=15, weight=ft.FontWeight.BOLD),
        _build_rating_row(),
        ft.Text(subtitle or "", size=12, color="#616161", max_lines=2),
    ]

    if show_cta:
        body_controls.append(
            ft.ElevatedButton(
                "View Details",
                icon=ft.Icons.VISIBILITY,
                on_click=on_click,
                height=36,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=18)),
            )
        )

    body = ft.Column(spacing=8, controls=body_controls)

    container = ft.Container(
        width=240,
        bgcolor="#FFFFFF",
        border_radius=12,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color="#0000000D",
            offset=ft.Offset(0, 4),
        ),
        content=ft.Column(spacing=12, controls=[image_block, ft.Container(padding=12, content=body)]),
        on_click=on_click,
    )

    return container


# ---------------------------------------------------------------------------
# Admin Listing Card
# ---------------------------------------------------------------------------
def create_admin_listing_card(
    listing: ListingInput,
    images: Optional[Sequence[str]] = None,
    *,
    status: Optional[str] = None,
    pm_contact: Optional[str] = None,
    is_available: bool = True,
    on_preview: ActionHandler = None,
    on_edit: ActionHandler = None,
    on_approve: ActionHandler = None,
    on_reject: ActionHandler = None,
    on_delete: ActionHandler = None,
) -> ft.Container:
    data = _listing_to_dict(listing)
    prop_name = data.get("property_name") or data.get("address") or "Listing"
    description = _truncate(str(data.get("description", "")), 180)
    price_text = _format_price(data.get("price", 0), decimals=2)
    status_value = (status or data.get("status") or "Unknown").title()
    status_color = {
        "Active": ft.Colors.GREEN,
        "Approved": ft.Colors.GREEN,
        "Pending": ft.Colors.ORANGE,
        "Rejected": ft.Colors.RED,
        "Archived": ft.Colors.GREY,
    }.get(status_value, ft.Colors.BLUE_GREY)

    main_image = _select_main_image(images) or data.get("image_url")

    chip = ft.Chip(label=ft.Text(status_value, size=11, color="white"), bgcolor=status_color, padding=6)

    actions: list[ft.Control] = [
        ft.OutlinedButton(
            "Preview",
            icon=ft.Icons.VISIBILITY,
            on_click=on_preview,
            disabled=on_preview is None,
        )
    ]

    if on_edit:
        actions.append(
            ft.ElevatedButton(
                "Edit",
                icon=ft.Icons.EDIT,
                on_click=on_edit,
                style=ft.ButtonStyle(color="white", bgcolor="#0078FF"),
            )
        )

    if status_value == "Pending" and on_approve:
        actions.append(
            ft.ElevatedButton(
                "Approve",
                icon=ft.Icons.CHECK,
                on_click=on_approve,
                style=ft.ButtonStyle(color="white", bgcolor="#2E7D32"),
            )
        )

    if status_value == "Pending" and on_reject:
        actions.append(
            ft.OutlinedButton(
                "Reject",
                icon=ft.Icons.CLOSE,
                on_click=on_reject,
                style=ft.ButtonStyle(color="#C62828"),
            )
        )

    if on_delete and status_value != "Pending":
        actions.append(
            ft.ElevatedButton(
                "Delete",
                icon=ft.Icons.DELETE_FOREVER,
                on_click=on_delete,
                style=ft.ButtonStyle(color="white", bgcolor="#C62828"),
            )
        )

    content = ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(prop_name, size=18, weight=ft.FontWeight.BOLD, color="#1A1A1A"),
                    chip,
                ],
            ),
            _build_image_block(main_image, width=420, height=160, is_available=is_available),
            ft.Text(description or "No description provided.", size=13, color="#555555", max_lines=3),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.PRICE_CHANGE, size=18, color="#0078FF"),
                            ft.Text(price_text, size=16, weight=ft.FontWeight.BOLD, color="#0078FF"),
                        ],
                    ),
                    ft.Text(pm_contact or "Unknown PM", size=12, color=ft.Colors.GREY_600),
                ],
            ),
            ft.Row(spacing=8, wrap=True, controls=actions),
        ],
    )

    return _card_container(content, padding=ft.padding.all(16), width=460)


# ---------------------------------------------------------------------------
# Home / Static variant
# ---------------------------------------------------------------------------
def create_home_listing_card(
    listing: ListingInput,
    image_url: Optional[str],
    is_available: bool,
    *,
    on_click: ActionHandler = None,
    show_cta: bool = True,
    page: Optional[ft.Page] = None,
) -> ft.Container:
    return create_tenant_listing_card(
        listing,
        image_url,
        is_available,
        user_id=None,
        show_save_button=False,
        show_cta=show_cta,
        on_click=on_click,
        page=page,
    )


# ---------------------------------------------------------------------------
# Legacy compatibility wrapper
# ---------------------------------------------------------------------------
class ListingCard:
    """Backward compatible wrapper around the new helper functions."""

    def __init__(
        self,
        *args,
        image_url: str = "",
        is_available: bool = True,
        on_click: ActionHandler = None,
        show_actions: bool = False,
        on_edit: ActionHandler = None,
        on_delete: ActionHandler = None,
        layout: str = "vertical",
        **kwargs,
    ):
        # Support both signatures: (listing, ...) and (page, listing)
        first = args[0] if args else None
        second = args[1] if len(args) > 1 else None
        if first is not None and hasattr(first, "session") and second is not None:
            # signature: (page, listing, ...)
            self.page = first
            self.listing = second
        else:
            # signature: (listing, ...)
            self.page = None
            self.listing = first

        self.image_url = image_url
        self.is_available = is_available
        self.on_click = on_click
        self.show_actions = show_actions
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.layout = layout

    def build_card(self) -> ft.Container:
        if self.layout == "horizontal":
            return create_pm_listing_card(
                listing=self.listing,
                images=[self.image_url] if self.image_url else None,
                is_available=self.is_available,
                on_preview=self.on_click,
                on_edit=self.on_edit,
                on_delete=self.on_delete,
            )

        return create_tenant_listing_card(
            listing=self.listing,
            image_url=self.image_url,
            is_available=self.is_available,
            show_save_button=not self.show_actions,
            on_click=self.on_click,
        )

    def build(self):
        return self.build_card()

