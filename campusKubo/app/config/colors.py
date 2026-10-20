# config/colors.py
"""
Centralized color palette configuration for CampusKubo application.
Earthy color scheme with warm, natural tones.
"""

COLORS = {
    # PRIMARY COLORS - Main Brand Identity
    "primary": "#8B7355",           # Warm brown
    # Used for: Main CTAs, primary buttons, active states, brand text, navigation highlights

    "secondary": "#A67C52",         # Terracotta/clay
    # Used for: Secondary buttons, icons, ratings, section headers, accent elements

    "accent": "#9CAF88",            # Sage green
    # Used for: Success states, available status, highlights, special features, snackbars

    # BACKGROUND COLORS - Canvas & Containers
    "background": "#F5F1E8",        # Warm beige
    # Used for: Page backgrounds, input fields, filter sections, secondary containers

    "card_bg": "#FDFBF7",          # Off-white cream
    # Used for: Cards, dialog boxes, form containers, property listings, main content areas

    # TEXT COLORS - Typography Hierarchy
    "text_dark": "#3E3127",        # Dark brown
    # Used for: Headings, primary text, labels, important information

    "text_light": "#6B5D52",       # Medium brown
    # Used for: Secondary text, descriptions, hints, metadata, timestamps

    # UI ELEMENTS - Borders & Dividers
    "border": "#D4C4B0",           # Light tan
    # Used for: Borders, dividers, outlines, image placeholders, inactive sliders

    # STATUS COLORS - Feedback & States
    "success": "#9CAF88",          # Sage green
    # Used for: Success messages, "Available" badges, confirmation states, checkmarks

    "error": "#C9A690",            # Dusty rose
    # Used for: Error messages, validation errors, "Unavailable" badges, warnings

    "available": "#9CAF88",        # Sage green
    # Used for: Available property status, in-stock indicators

    "unavailable": "#C9A690",      # Dusty rose
    # Used for: Reserved/Full status, out-of-stock indicators

    # INTERACTIVE STATES - Hover & Focus
    "hover": "#7D6E5C",            # Muted brown (darker than primary)
    # Used for: Button hover states, interactive element highlights

    "focus": "#8B7355",            # Warm brown (same as primary)
    # Used for: Focus borders, active input states
}

def get_colors():
    """
    Returns the color palette dictionary.

    Returns:
        dict: Color palette with semantic color names and hex values
    """
    return COLORS.copy()