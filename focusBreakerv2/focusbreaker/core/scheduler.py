from typing import List, Optional
from focusbreaker.data.models import Break, Settings, Task
from focusbreaker.config import TimingConfig

class Scheduler:
    """
    Handles the calculation of break times for different work modes.
    """
    @staticmethod
    def schedule_breaks(session_id: int, duration_minutes: int, mode: str, settings: Settings, task: Optional[Task] = None) -> List[Break]:
        breaks = []
        import logging
        logger = logging.getLogger("FocusBreaker")

        if mode == "focused":
            # Focused mode: one break at the very end
            brk_dur = settings.focused_mandatory_break
            if duration_minutes >= 240:
                brk_dur = 60
            elif duration_minutes >= 120:
                brk_dur = 45
            
            # If task has manual duration, respect it
            if task and not task.auto_calculate_breaks:
                brk_dur = task.manual_break_duration

            logger.info(f"Scheduler: Using FOCUSED break - duration={brk_dur}min at end")
                
            b = Break(
                session_id=session_id,
                scheduled_offset_minutes=duration_minutes,
                duration_minutes=brk_dur
            )
            breaks.append(b)
            return breaks

        if task and not task.auto_calculate_breaks and task.manual_break_count > 0:
            count = task.manual_break_count
            brk_dur = task.manual_break_duration
            logger.info(f"Scheduler: Using MANUAL breaks - count={count}, duration={brk_dur}min")
            
            # Distribute breaks evenly
            interval = duration_minutes // (count + 1)
            offset = interval
            for _ in range(count):
                b = Break(
                    session_id=session_id,
                    scheduled_offset_minutes=offset,
                    duration_minutes=brk_dur
                )
                breaks.append(b)
                offset += interval
                
            logger.info(f"Scheduler: Created {len(breaks)} manual breaks")
            return breaks

        if mode == "normal":
            interval = settings.normal_work_interval
            brk_dur = settings.normal_break_duration
            logger.info(f"Scheduler: Using AUTO NORMAL breaks - interval={interval}min, duration={brk_dur}min")
            offset = interval
            while offset < duration_minutes:
                b = Break(
                    session_id=session_id,
                    scheduled_offset_minutes=offset,
                    duration_minutes=brk_dur
                )
                breaks.append(b)
                offset += interval + brk_dur
                
        elif mode == "strict":
            interval = settings.strict_work_interval
            brk_dur = settings.strict_break_duration
            logger.info(f"Scheduler: Using AUTO STRICT breaks - interval={interval}min, duration={brk_dur}min")
            offset = interval
            while offset < duration_minutes:
                b = Break(
                    session_id=session_id,
                    scheduled_offset_minutes=offset,
                    duration_minutes=brk_dur
                )
                breaks.append(b)
                offset += interval + brk_dur
                
        # Note: Focused mode handled at the top
        pass
            
        logger.info(f"Scheduler: Total breaks created: {len(breaks)}")
        return breaks
