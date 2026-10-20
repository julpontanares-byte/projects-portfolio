# app/services/refresh_service.py
"""
Simple observer service for notifying views about data refresh events.
Views can register callback functions which will be called when a global
refresh is triggered (for example by a refresh button in the navbar).
"""
from typing import Callable, List
import threading


class RefreshService:
    _callbacks: List[Callable] = []
    _lock = threading.Lock()

    @classmethod
    def register(cls, cb: Callable):
        if not callable(cb):
            return False
        with cls._lock:
            cls._callbacks.append(cb)
        return True

    @classmethod
    def unregister(cls, cb: Callable):
        with cls._lock:
            try:
                cls._callbacks.remove(cb)
            except ValueError:
                pass

    @classmethod
    def notify(cls):
        # Make a snapshot copy to avoid mutation during iteration
        with cls._lock:
            callbacks = list(cls._callbacks)
        for cb in callbacks:
            try:
                cb()
            except Exception:
                # swallow exceptions to avoid breaking the broadcaster
                pass


# Convenience module-level functions
register = RefreshService.register
unregister = RefreshService.unregister
notify = RefreshService.notify
