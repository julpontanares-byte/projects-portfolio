"""
Application state management
"""


class AppState:
    """Global application state"""

    def __init__(self):
        """Initialize app state"""
        self.search_query = ""
        self.selected_filters = {
            'price_min': None,
            'price_max': None,
            'amenities': [],
            'room_type': None,
            'location': None
        }
        self.current_listing = None

    def set_search_query(self, query: str):
        """Set search query"""
        self.search_query = query

    def get_search_query(self) -> str:
        """Get search query"""
        return self.search_query

    def set_filter(self, filter_name: str, value):
        """Set a specific filter"""
        if filter_name in self.selected_filters:
            self.selected_filters[filter_name] = value

    def get_filter(self, filter_name: str):
        """Get a specific filter value"""
        return self.selected_filters.get(filter_name)

    def clear_filters(self):
        """Reset all filters"""
        self.selected_filters = {
            'price_min': None,
            'price_max': None,
            'amenities': [],
            'room_type': None,
            'location': None
        }

    def set_current_listing(self, listing):
        """Set currently viewed listing"""
        self.current_listing = listing

    def get_current_listing(self):
        """Get currently viewed listing"""
        return self.current_listing