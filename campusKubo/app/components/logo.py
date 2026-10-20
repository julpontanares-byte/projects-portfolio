"""Reusable CampusKubo logo component."""

import flet as ft


def _render_logo(size: int = 22, color: str | None = None, with_icon: bool = False, subtitle: str | None = None) -> ft.Control:
    """Internal renderer for the logo control."""
    color = color or "#1A1A1A"

    if with_icon:
        column_controls = [ft.Text("CampusKubo", size=size, weight=ft.FontWeight.BOLD, color=color)]
        if subtitle:
            column_controls.append(ft.Text(subtitle, size=max(12, int(size * 0.55)), color=ft.Colors.BLACK))

        return ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.HOME, size=int(size * 1.2), color="#0078FF"),
                ft.Column(spacing=0, controls=column_controls),
            ],
        )

    # Default: single-line textual logo, preserving the house emoji used on home pages
    return ft.Text(" C🏠mpusKubo", size=size, weight=ft.FontWeight.BOLD, color=color)


class LogoWrapper:
    """Compatibility wrapper returned when tests call `Logo(page)`.

    Provides a `.build()` method so older tests expecting `Logo(page).build()`
    continue to work.
    """

    def __init__(self, page: ft.Page, *, size: int = 22, color: str | None = None, with_icon: bool = False, subtitle: str | None = None):
        self.page = page
        self.size = size
        self.color = color
        self.with_icon = with_icon
        self.subtitle = subtitle

    def build(self) -> ft.Control:
        # Return a container to match existing test expectations
        return ft.Container(content=_render_logo(self.size, self.color, self.with_icon, self.subtitle))


def Logo(*args, **kwargs):
    """Public API: either return a logo control or a wrapper when called with a page.

    Usage:
    - `Logo(size=20)` -> returns `ft.Control` (logo)
    - `Logo(page)` -> returns an object with `.build()` for compatibility
    """
    if args and (isinstance(args[0], ft.Page) or hasattr(args[0], "session") or hasattr(args[0], "go")):
        page = args[0]
        # allow overrides via kwargs
        return LogoWrapper(page, **kwargs)

    # Otherwise behave like the old function returning a control
    return _render_logo(*args, **kwargs)
