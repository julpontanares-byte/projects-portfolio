from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import logging
from focusbreaker.data.db import DBManager
from focusbreaker.data.models import Streak, WorkSession

logger = logging.getLogger(__name__)

class StreakManager:
    """
    Manages calculation and persistence of streak types.
    Fixed bugs identified in user_flow.md.
    """
    MILESTONES = [5, 10, 25, 50, 100]

    def __init__(self, db: DBManager):
        self.db = db

    def process_session_completion(self, session: WorkSession) -> List[Dict[str, Any]]:
        """
        Step 54: Updates streaks after a session.
        Returns a list of milestones reached during this update.
        """
        streaks = self.db.get_streaks()
        today = date.today().isoformat()
        milestones_reached = []

        # 1. Session Streak (No skips, No emergency exits)
        has_skips = session.breaks_skipped > 0
        has_emergency = getattr(session, 'emergency_exits', 0) > 0
        session_valid = not has_skips and not has_emergency
        
        logger.info(f"Updating streaks for session {session.id}: valid={session_valid}, perfect not yet checked)")
        
        sess_streak = streaks.get("session_streak", Streak("session_streak"))
        self._update_streak_count(sess_streak, session_valid, today)
        self.db.update_streak(sess_streak)
        logger.info(f"  Session streak: {sess_streak.current_count} (best: {sess_streak.best_count})")
        
        m = self.check_streak_milestone(sess_streak)
        if m: milestones_reached.append(m)

        # 2. Perfect Session Streak (No skips, No snoozes, No emergency exits)
        has_snoozes = session.breaks_snoozed > 0
        session_perfect = session_valid and not has_snoozes
        
        perf_streak = streaks.get("perfect_session", Streak("perfect_session"))
        # Fixed Step 54 Bug: Correct instance reference used in _update_streak_count
        self._update_streak_count(perf_streak, session_perfect, today)
        self.db.update_streak(perf_streak)
        logger.info(f"  Perfect streak: {perf_streak.current_count} (best: {perf_streak.best_count})")
        
        m = self.check_streak_milestone(perf_streak)
        if m: milestones_reached.append(m)

        # 3. Daily Consistency
        # Step 54 logic for daily consistency
        daily = streaks.get("daily_consistency", Streak("daily_consistency"))
        self._update_daily_consistency(daily, session.created_at)
        self.db.update_streak(daily)
        
        m = self.check_streak_milestone(daily)
        if m: milestones_reached.append(m)

        return milestones_reached

    def _update_streak_count(self, streak: Streak, is_valid: bool, today: str):
        """Helper to increment or reset streak."""
        if is_valid:
            streak.current_count += 1
            streak.best_count = max(streak.best_count, streak.current_count)
        else:
            streak.current_count = 0
        streak.last_updated = today

    def _update_daily_consistency(self, daily: Streak, session_created_at: str):
        """Step 54 specialized logic for daily consistency."""
        today = date.today()
        today_str = today.isoformat()
        
        # Parse the session created_at date (can be full ISO datetime like "2026-03-18T14:30:00")
        try:
            session_date = datetime.fromisoformat(session_created_at).date()
        except (ValueError, AttributeError):
            try:
                session_date = date.fromisoformat(session_created_at)
            except:
                session_date = today  # Fallback to today
        
        if daily.last_updated == today_str:
            return # Already counted today

        if not daily.last_updated:
            daily.current_count = 1
        else:
            last_date = date.fromisoformat(daily.last_updated)
            diff = (today - last_date).days
            if diff == 1:
                daily.current_count += 1
            elif diff > 1:
                daily.current_count = 1 # Streak broken, reset to 1 since we worked today
            else:
                return # Should not happen (diff <= 0 handled by check above)

        daily.best_count = max(daily.best_count, daily.current_count)
        daily.last_updated = today_str

    def check_streak_milestone(self, streak: Streak) -> Optional[Dict[str, Any]]:
        """Step 55: Detects if a major milestone was hit."""
        if streak.current_count in self.MILESTONES:
            return {
                "type": streak.streak_type,
                "count": streak.current_count,
                "emoji": "🔥" if streak.streak_type == "session_streak" else "⭐",
                "message": f"{streak.current_count}-day streak! Amazing!" if streak.streak_type == "daily_consistency" else f"{streak.current_count} sessions streak!"
            }
        return None

    def can_recover_streak(self, streak_type: str) -> bool:
        """Fixed Bug: Compares streak_type string correctly."""
        return streak_type != "daily_consistency"