def go_home(page):
    """Navigate to a role-aware home route without clearing session."""
    role = page.session.get("role") if hasattr(page, "session") else None
    if role == "admin":
        page.go("/admin")
    elif role == "pm":
        page.go("/pm")
    elif role == "tenant":
        page.go("/tenant")
    else:
        page.go("/")


def debug_click(button_name, original_callback=None):
    """Debug wrapper for button clicks."""
    def wrapper(e=None):
        print(f"DEBUG: Button clicked - {button_name}")
        if original_callback:
            return original_callback(e)
    return wrapper


def go_back(page, fallback="/"):
    """Navigate back using navigation history, with fallback route."""
    history = getattr(page, "_nav_history", [])
    if history:
        prev_route = history.pop()
        setattr(page, "_nav_back_navigation", True)
        page.go(prev_route)
    else:
        page.go(fallback)
