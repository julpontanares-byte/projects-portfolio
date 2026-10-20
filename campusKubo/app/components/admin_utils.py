from datetime import datetime
from typing import Union, Optional


def format_id(prefix: str, numeric_id: Optional[int]) -> str:
    """Return a display id with an alphabetic prefix and zero-padded numeric suffix (chronological)."""
    try:
        nid = int(numeric_id) if numeric_id is not None else 0
        return f"{prefix.upper()}{nid:05d}"
    except Exception:
        return f"{prefix.upper()}00000"


def format_name(name: str) -> str:
    """Return a name in Title Case (Capitalized per word)."""
    try:
        return str(name).title() if name else ""
    except Exception:
        return str(name or "")

def format_datetime(iso_value: Union[str, datetime]) -> str:
    """Format ISO datetime string to 'YYYY-MM-DD HH:MM:SS' (no milliseconds)."""
    if not iso_value:
        return ""
    try:
        # Some DB rows may already be datetime objects
        if isinstance(iso_value, datetime):
            return iso_value.strftime('%Y-%m-%d %H:%M:%S')
        dt = datetime.fromisoformat(str(iso_value))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        # fallback: try trimming fractional seconds
        s = str(iso_value)
        if '.' in s:
            s = s.split('.')[0]
        return s
        return s
