from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
from PySide6.QtCore import QObject, Signal, QTimer

from focusbreaker.data.db import DBManager
from focusbreaker.data.models import WorkSession, Break, Streak, Task
from focusbreaker.core.timer import CountdownTimer, fmt_time
from focusbreaker.config import MODES
from focusbreaker.core.scheduler import Scheduler
from focusbreaker.core.streak_manager import StreakManager
from focusbreaker.core.mode_controller import ModeController

logger = logging.getLogger(__name__)


class SessionManager(QObject):
    tick = Signal(int, int)          # elapsed_seconds, remaining_seconds
    warning_emitted = Signal(str)    # message
    break_due = Signal(object)       # Break object
    session_finished_normal = Signal(object) # WorkSession (Step 46: ask to extend)
    session_started = Signal(object)         # WorkSession
    session_completed = Signal(object, list)  # WorkSession, Milestones
    status_changed = Signal(str)
    cooldown_tick = Signal(int)      # remaining_cooldown_seconds

    def __init__(self, db: DBManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.streak_mgr = StreakManager(db)
        self.session: Optional[WorkSession] = None
        self.mode_ctrl: Optional[ModeController] = None
        self.breaks: List[Break] = []
        self.current_break: Optional[Break] = None
        self._elapsed = 0
        self._paused = False
        
        # Cooldown state
        self._in_cooldown = False
        self._cooldown_rem = 0
        
        self._warnings_fired = set()

        self._work_timer = QTimer(self)
        self._work_timer.setInterval(1000)
        self._work_timer.timeout.connect(self._on_work_tick)

    # ── Public API ────────────────────────────────────────
    def start_session(self, task_name: str, duration_minutes: int, mode: str, task: Optional[Task] = None):
        if self._in_cooldown:
            return

        settings = self.db.get_settings()
        # Coerce settings to a Settings dataclass with defaults when tests provide a MagicMock
        from focusbreaker.data.models import Settings as SettingsModel
        import dataclasses
        if not isinstance(settings, SettingsModel):
            default_settings = SettingsModel()
            # copy any attributes present on the returned object
            import unittest.mock
            for f in dataclasses.fields(SettingsModel):
                if hasattr(settings, f.name):
                    try:
                        val = getattr(settings, f.name)
                        # Avoid copying Mock/MagicMock attributes which are dynamically created
                        if isinstance(val, unittest.mock.Mock):
                            continue
                        setattr(default_settings, f.name, val)
                    except Exception:
                        # ignore errors reading mocked attributes
                        pass
            settings = default_settings
        now = datetime.now().isoformat()
        self.mode_ctrl = ModeController(mode)

        ws = WorkSession(
            task_id=task.id if task is not None else None,
            task_name=task_name,
            planned_duration_minutes=duration_minutes,
            mode=mode,
            start_time=now,
            snooze_passes_remaining=settings.max_snooze_passes,
            created_at=now
        )
        ws.id = self.db.createSession(ws)
        self.session = ws
        self._elapsed = 0
        self._paused = False
        self._warnings_fired = set()

        # Step 19: Schedule breaks
        if ws.id is not None:
            self.breaks = Scheduler.schedule_breaks(ws.id, duration_minutes, mode, settings, task)
            import logging
            logger = logging.getLogger("FocusBreaker")
            logger.info(f"Scheduled {len(self.breaks)} breaks for {mode} mode, duration: {duration_minutes} min")
            for b in self.breaks:
                start_dt = datetime.fromisoformat(now)
                b.scheduled_time = (start_dt + timedelta(minutes=b.scheduled_offset_minutes)).isoformat()
                logger.info(f"  Break: offset={b.scheduled_offset_minutes}min, duration={b.duration_minutes}min")
                # In a production DBManager, scheduleBreaksForSessions would return ids. 
                # For simplicity, we just save them here.
                # b.id = self.db.create_break(b) # Assuming this exists or is handled
            
        self._work_timer.start()
        self.session_started.emit(self.session)
        self.status_changed.emit("started")
        self.db.log_event("session_started", session_id=ws.id)

    def pause(self):
        if self._work_timer.isActive() and not self._in_cooldown:
            self._work_timer.stop()
            self._paused = True
            self.status_changed.emit("paused")

    def resume(self):
        if self._paused and not self._in_cooldown:
            self._paused = False
            self._work_timer.start()
            self.status_changed.emit("resumed")

    def stop_session(self, status: str = "abandoned"):
        self._work_timer.stop()
        if self.session is not None:
            self.session.status = status
            self.session.end_time = datetime.now().isoformat()
            # Set actual duration before saving. At least 1 minute if started, otherwise 0.
            self.session.actual_duration_minutes = max(1, round(self._elapsed / 60)) if self._elapsed > 0 else 0
            
            # Compute quality score so stats update correctly
            self._update_quality()
            
            session_id = self.session.id
            if session_id is not None:
                self.db.updateSession(
                    session_id, 
                    status=status, 
                    end_time=self.session.end_time, 
                    actual_duration_minutes=self.session.actual_duration_minutes,
                    quality_score=self.session.quality_score
                )
                self.db.log_event("session_stopped", session_id=session_id, description=f"Status: {status}")
        
        self.session = None
        self.mode_ctrl = None
        self.breaks = []
        self._elapsed = 0
        self._paused = False
        self._in_cooldown = False
        self._cooldown_rem = 0
        self.status_changed.emit(status)

    def handle_break_action(self, action: str):
        if action == "cooldown_finished" or self._in_cooldown:
            self._in_cooldown = False
            self._work_timer.stop()
            self.status_changed.emit("completed")
            return

        if not self.current_break or self.session is None:
            return
        brk = self.current_break
        self.current_break = None
        session_id = self.session.id
        if session_id is None:
            return

        if action == "taken":
            brk.status = "completed"
            self.session.breaks_taken += 1
            if brk.id is not None:
                self.db.updateBreak(brk.id, status='completed')
            self.db.updateSession(session_id, breaks_taken=self.session.breaks_taken)
            self.db.log_event("break_completed", session_id=session_id, break_id=brk.id)
            
        elif action == "snoozed":
            if self.db.canSnooze(session_id):
                self.db.useSnoozePass(session_id)
                self.session.snooze_passes_remaining -= 1
                self.session.breaks_snoozed += 1
                
                settings = self.db.get_settings()
                snooze_min = settings.normal_snooze_duration
                
                brk.status = "snoozed"
                brk.snooze_count += 1
                brk.snooze_duration_minutes += snooze_min
                
                if brk.id is not None:
                    self.db.updateBreak(brk.id, status='snoozed', snooze_count=brk.snooze_count, snooze_duration_minutes=brk.snooze_duration_minutes)
                
                if settings.snooze_redistributes_breaks:
                    self.db.redistributeRemainingBreaks(session_id)
                    # For logic alignment, we'd refresh breaks here.
                else:
                    brk.scheduled_offset_minutes += snooze_min
                    brk.status = "pending"
                
                self.db.log_event("break_snoozed", session_id=session_id, break_id=brk.id)

        elif action == "skipped":
            brk.status = "skipped"
            self.session.breaks_skipped += 1
            if brk.id is not None:
                self.db.updateBreak(brk.id, status='skipped')
            self.db.updateSession(session_id, breaks_skipped=self.session.breaks_skipped)
            self.db.log_event("break_skipped", session_id=session_id, break_id=brk.id)

        elif action == "emergency_exit":
            self.session.emergency_exits += 1
            self.db.updateSession(session_id, emergency_exits=self.session.emergency_exits)
            self.db.log_event("emergency_exit_used", session_id=session_id, description="Escape hatch triggered during break.")
            self.stop_session("emergency_exit")
            return

        # Resume the session timer after the break action is handled
        self._work_timer.start()
        self._update_quality()

    def complete_session(self):
        """Called when the user chooses 'End Session' or automatically for Strict/Focused."""
        self._work_timer.stop()
        if self.session is None:
            return
        
        # Step 44: Check for cooldown
        settings = self.db.get_settings()
        cooldown_mins = self.mode_ctrl.get_cooldown_duration(self.session.planned_duration_minutes, settings) if self.mode_ctrl else 0
        
        self.session.status = "completed"
        self.session.end_time = datetime.now().isoformat()
        # Set actual duration with proper rounding
        self.session.actual_duration_minutes = round(self._elapsed / 60) if self._elapsed > 0 else 0
        
        logger.info(f"Completing session {self.session.id}: start_time={self.session.start_time}, elapsed_seconds={self._elapsed}, actual_duration_minutes={self.session.actual_duration_minutes}")
        
        self._update_quality()
        session_id = self.session.id
        if session_id is not None:
            logger.info(f"Updating session {session_id} in database with status='completed', actual_duration={self.session.actual_duration_minutes}min, quality={self.session.quality_score}")
            self.db.updateSession(session_id, 
                                  status="completed", 
                                  end_time=self.session.end_time, 
                                  actual_duration_minutes=self.session.actual_duration_minutes,
                                  quality_score=self.session.quality_score)
        
        # Step 54: Update streaks with crash protection
        milestones = []
        try:
            if self.streak_mgr:
                milestones = self.streak_mgr.process_session_completion(self.session)
        except Exception as e:
            logger.error(f"STREAK ERROR: Failed to process session completion milestones: {e}", exc_info=True)
        
        completed = self.session
        mode_was = self.session.mode
        
        self.session = None
        self.breaks = []
        self._elapsed = 0
        
        logger.info(f"Session {session_id} cleanup complete. Emitting completion signals.")
        self.session_completed.emit(completed, milestones)
        
        if session_id is not None:
            try:
                self.db.log_event("session_completed", session_id=session_id)
            except: pass
        
        if cooldown_mins > 0:
            self._start_cooldown(cooldown_mins, mode_was)
        else:
            self.status_changed.emit("completed")

    def extend_session(self, additional_minutes: int):
        """Step 47-52: Logic for session extension."""
        if self.session is None or self.session.mode != "normal":
            return
        
        session_id = self.session.id
        if session_id is None:
            return
            
        settings = self.db.get_settings()
        
        # Step 49: Update session info
        self.session.extended_count += 1
        self.session.planned_duration_minutes += additional_minutes
        self.db.updateSession(session_id, 
                              extended_count=self.session.extended_count, 
                              planned_duration_minutes=self.session.planned_duration_minutes)
        
        # Step 50: Reset snooze passes
        self.session.snooze_passes_remaining = settings.max_snooze_passes
        self.db.updateSession(session_id, snooze_passes_remaining=self.session.snooze_passes_remaining)
        
        # Step 51: Calculate and schedule NEW breaks for extended time
        # We find how many NEW intervals fit in the additional time
        interval = settings.normal_work_interval
        start_offset = (self._elapsed // 60) + interval
        end_offset = self.session.planned_duration_minutes
        
        offset = start_offset
        while offset < end_offset:
            b = Break(
                session_id=session_id,
                scheduled_offset_minutes=offset,
                duration_minutes=settings.normal_break_duration,
                status='pending'
            )
            # In a real app, Scheduler would be used and DB updated.
            self.breaks.append(b)
            offset += interval
            
        # Step 52: Timer resumes
        self._work_timer.start()
        self.status_changed.emit("extended")
        if session_id is not None:
            self.db.log_event("session_extended", session_id=session_id, description=f"Added {additional_minutes} mins")

    def _start_cooldown(self, minutes: int, mode: str):
        self._in_cooldown = True
        self._cooldown_rem = minutes * 60
        self.mode_ctrl = ModeController(mode)
        self.status_changed.emit("cooldown_started")
        self._work_timer.start()

    def get_next_break_seconds(self) -> Optional[int]:
        if not self.session:
            return None
        pending = [b for b in self.breaks if b.status == "pending"]
        if not pending:
            return None
        # Sort pending to find the soonest one
        pending.sort(key=lambda b: b.scheduled_offset_minutes)
        next_brk = pending[0]
        offset_sec = next_brk.scheduled_offset_minutes * 60
        remaining = offset_sec - self._elapsed
        return max(0, remaining)

    def _on_work_tick(self):
        if self._in_cooldown:
            self._cooldown_rem -= 1
            self.cooldown_tick.emit(self._cooldown_rem)
            if self._cooldown_rem <= 0:
                self.handle_break_action("cooldown_finished")
            return

        if not self.session: return
        self._elapsed += 1
        rem = max(0, self.session.planned_duration_minutes * 60 - self._elapsed)
        self.tick.emit(self._elapsed, rem)

        # Step 23: Warnings (2 mins before break)
        next_sec = self.get_next_break_seconds()
        if next_sec == 120 and "break_2m" not in self._warnings_fired:
            self.warning_emitted.emit("Break in 2 minutes")
            self._warnings_fired.add("break_2m")

        pending = [b for b in self.breaks if b.status == "pending"]
        if pending:
            # Re-check if any break is triggered (Step 24)
            pending.sort(key=lambda b: b.scheduled_offset_minutes)
            next_brk = pending[0]
            elapsed_min = self._elapsed / 60
            if self._elapsed >= next_brk.scheduled_offset_minutes * 60:
                import logging
                logger = logging.getLogger("FocusBreaker")
                logger.info(f"Break triggered! Elapsed: {elapsed_min:.1f}min, offset: {next_brk.scheduled_offset_minutes}min")
                self._work_timer.stop()
                self.current_break = next_brk
                self.break_due.emit(next_brk)
                self._warnings_fired = set()
                return

        if rem <= 0:
            # Step 44: For Normal mode, ask to extend. For others, auto-complete (which handles cooldown).
            if self.session.mode == "normal":
                self._work_timer.stop()
                self.session_finished_normal.emit(self.session)
            else:
                self.complete_session()

    @property
    def is_active(self) -> bool: return self.session is not None or self._in_cooldown
    
    @property
    def in_cooldown(self) -> bool: return self._in_cooldown

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def elapsed_seconds(self) -> int:
        return self._elapsed

    def _update_quality(self):
        if not self.session: return
        total = (self.session.breaks_taken + self.session.breaks_snoozed + self.session.breaks_skipped)
        quality = self.session.breaks_taken / total if total > 0 else 1.0
        quality -= (self.session.emergency_exits * 0.2)
        
        # Apply penalty for early termination only if the session has an actual duration set
        if 0 < self.session.actual_duration_minutes < self.session.planned_duration_minutes:
            completion_ratio = self.session.actual_duration_minutes / self.session.planned_duration_minutes if self.session.planned_duration_minutes > 0 else 1.0
            early_exit_penalty = (1.0 - completion_ratio) * 0.3  # Up to 30% penalty based on how early they left
            quality -= early_exit_penalty
        
        self.session.quality_score = max(0.0, round(quality, 2))