import flet as ft
from typing import Optional


def open_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Safely attach and open a dialog on the given page.

    This function is defensive across different Flet versions: it attempts
    to append the dialog to `page.overlay` when available and also sets
    `page.dialog` as a fallback. It always attempts to call `page.update()`
    but won't raise if the page is not live (e.g., during import-time tests).
    """
    try:
        # Prefer overlay when present
        if hasattr(page, "overlay"):
            try:
                page.overlay.append(dialog)
            except Exception:
                # ignore overlay append failures
                pass

        # Also set page.dialog when possible (some runtimes expect it)
        try:
            page.dialog = dialog
        except Exception:
            pass

        # Open and update
        try:
            dialog.open = True
        except Exception:
            pass

        try:
            page.update()
        except Exception:
            pass
    except Exception:
        pass


def close_dialog(page: ft.Page, dialog: ft.AlertDialog, remove: bool = True):
    """Close and remove a dialog from the page overlays where possible.

    When `remove` is True this will try to remove the exact dialog object
    from `page.overlay` and also clear `page.dialog` if it references the
    same dialog. As a defensive measure it will also remove any lingering
    `AlertDialog` instances from the overlay to avoid leaving a dim scrim.
    """
    try:
        # Close the dialog first
        try:
            dialog.open = False
        except Exception:
            pass

        # Try to remove the exact dialog object from overlay if present
        if remove:
            try:
                # Remove by identity if possible
                if hasattr(page, 'overlay') and dialog in list(page.overlay):
                    try:
                        page.overlay.remove(dialog)
                    except Exception:
                        # Some Flet versions may disallow direct remove; fallthrough
                        pass
            except Exception:
                pass

            # Clear page.dialog if it references this dialog
            try:
                if getattr(page, 'dialog', None) is dialog:
                    page.dialog = None
            except Exception:
                pass

            # As a defensive fallback, remove any AlertDialog instances from overlay
            try:
                if hasattr(page, 'overlay'):
                    # Create a new list excluding AlertDialog instances
                    cleaned = [item for item in list(page.overlay) if not isinstance(item, ft.AlertDialog)]
                    # Only replace overlay if we removed something
                    if len(cleaned) != len(list(page.overlay)):
                        try:
                            page.overlay.clear()
                            for item in cleaned:
                                page.overlay.append(item)
                        except Exception:
                            pass
            except Exception:
                pass

        # Finally, ensure page.dialog is cleared as well
        try:
            if getattr(page, 'dialog', None) is not None:
                page.dialog = None
        except Exception:
            pass

        # Final page update
        try:
            page.update()
        except Exception:
            pass
    except Exception:
        pass
