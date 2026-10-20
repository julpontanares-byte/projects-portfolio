import sqlite3
import os
import json
import csv
import random
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Tuple

from focusbreaker.data.models import Task, WorkSession, Break, Streak, Settings

logger = logging.getLogger(__name__)


class DBManager:
    def __init__(self, db_path: str = "focusbreaker.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Establish a connection to the database. Re-opens if closed."""
        print(f"[DEBUG DB] connect() called, self.conn={self.conn}", flush=True)
        if self.conn:
            try:
                print("[DEBUG DB] Testing existing connection...", flush=True)
                self._db.execute("SELECT 1")
                print("[DEBUG DB] Existing connection is valid", flush=True)
                return 
            except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
                logger.warning(f"Existing database connection failed, reconnecting: {e}")
                self.conn = None
        
        print(f"[DEBUG DB] Creating new database connection to {self.db_path}...", flush=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        print("[DEBUG DB] Connection created", flush=True)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        print("[DEBUG DB] Setting up database...", flush=True)
        self.init_database()
        print("[DEBUG DB] Migrating database...", flush=True)
        self.migrate_database()
        print("[DEBUG DB] Adding task columns...", flush=True)
        self._add_task_columns()
        print("[DEBUG DB] Database connection complete!", flush=True)
        
    def _add_task_columns(self) -> None:
        try:
            self._db.execute("ALTER TABLE tasks ADD COLUMN manual_break_count INTEGER DEFAULT 0")
            self._db.execute("ALTER TABLE tasks ADD COLUMN manual_break_duration INTEGER DEFAULT 5")
            self._db.commit()
        except sqlite3.OperationalError as e:
            logger.debug(f"Task columns already exist or migration skipped: {e}")

    def close(self):
        """Safely close the database connection."""
        if self.conn:
            try:
                self._db.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
            self.conn = None

    def init_database(self) -> None:
        print("[DEBUG DB] init_database() called", flush=True)
        self._ensure_connected()
        print("[DEBUG DB] Creating database tables...", flush=True)
        c = self._db.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                allocated_time_minutes INTEGER NOT NULL,
                mode TEXT NOT NULL,
                auto_calculate_breaks INTEGER DEFAULT 1,
                manual_break_count INTEGER DEFAULT 0,
                manual_break_duration INTEGER DEFAULT 5,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS work_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                task_name TEXT NOT NULL,
                planned_duration_minutes INTEGER NOT NULL,
                mode TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL DEFAULT 'in_progress',
                breaks_taken INTEGER DEFAULT 0,
                breaks_snoozed INTEGER DEFAULT 0,
                breaks_skipped INTEGER DEFAULT 0,
                emergency_exits INTEGER DEFAULT 0,
                snooze_passes_remaining INTEGER DEFAULT 3,
                extended_count INTEGER DEFAULT 0,
                actual_duration_minutes INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 1.0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS breaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                scheduled_offset_minutes INTEGER NOT NULL,
                duration_minutes INTEGER NOT NULL,
                scheduled_time TEXT,
                actual_time TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                snooze_count INTEGER DEFAULT 0,
                snooze_duration_minutes INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES work_sessions(id)
            );
            CREATE TABLE IF NOT EXISTS break_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                mode TEXT NOT NULL,
                is_jumpscare INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS streaks (
                streak_type TEXT PRIMARY KEY,
                current_count INTEGER DEFAULT 0,
                best_count INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                session_id INTEGER,
                break_id INTEGER,
                description TEXT,
                timestamp TEXT NOT NULL
            );
        """)
        for stype in ["session_streak", "perfect_session", "daily_consistency"]:
            c.execute("INSERT OR IGNORE INTO streaks (streak_type) VALUES (?)", (stype,))
        
        defaults = {
            "username": "User", "is_first_run": "True", "first_close_notified": "False", "normal_work_interval": "25",
            "normal_break_duration": "5", "normal_snooze_duration": "5", "max_snooze_passes": "3",
            "allow_skip_in_normal_mode": "True", "snooze_redistributes_breaks": "True",
            "strict_work_interval": "52", "strict_break_duration": "17", "strict_cooldown": "20",
            "focused_mandatory_break": "30", "media_volume": "80", "alarm_volume": "70", "alarm_duration": "5"
        }
        for k, v in defaults.items():
            c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        self._db.commit()
        print("[DEBUG DB] init_database() complete", flush=True)
        self._cleanup_crashed_sessions()

    def seed_sample_data(self) -> None:
        """Seed the database with specific data from the prompt."""
        self._ensure_connected()
        count = self._db.execute("SELECT COUNT(*) FROM work_sessions").fetchone()[0]
        if count > 0: return

        print("Seeding sample data...")
        
        # Import here to avoid circular imports
        from focusbreaker.core.streak_manager import StreakManager
        streak_mgr = StreakManager(self)
        
        # Note: Streaks will be updated after inserting sessions
        # Initial seeding of streaks is moved to the end of this method

        # 2. Add Prompt History (Specific 10 sessions)
        now = datetime.now()
        prompt_history = [
            {"task": "Deep work — API design", "mode": "strict", "dt": now - timedelta(hours=2), "dur": 52, "taken": 1, "snoozed": 0, "skipped": 0, "emergency": 0, "score": 1.0},
            {"task": "Frontend refactoring", "mode": "normal", "dt": now - timedelta(hours=6), "dur": 75, "taken": 2, "snoozed": 1, "skipped": 0, "emergency": 0, "score": 0.83},
            {"task": "Study session — DSA", "mode": "focused", "dt": now - timedelta(days=1, hours=4), "dur": 120, "taken": 0, "snoozed": 0, "skipped": 0, "emergency": 0, "score": 1.0},
            {"task": "Code review", "mode": "normal", "dt": now - timedelta(days=1, hours=8), "dur": 50, "taken": 1, "snoozed": 1, "skipped": 1, "emergency": 0, "score": 0.50},
            {"task": "Research session", "mode": "strict", "dt": now - timedelta(days=2, hours=10), "dur": 52, "taken": 1, "snoozed": 0, "skipped": 0, "emergency": 1, "score": 0.80},
            {"task": "Writing — blog post", "mode": "focused", "dt": now - timedelta(days=3, hours=2), "dur": 90, "taken": 0, "snoozed": 0, "skipped": 0, "emergency": 0, "score": 1.0},
            {"task": "Sprint planning prep", "mode": "normal", "dt": now - timedelta(days=3, hours=6), "dur": 25, "taken": 0, "snoozed": 0, "skipped": 1, "emergency": 0, "score": 0.0},
            {"task": "Algorithm practice", "mode": "strict", "dt": now - timedelta(days=4, hours=4), "dur": 52, "taken": 1, "snoozed": 0, "skipped": 0, "emergency": 0, "score": 1.0},
            {"task": "System design notes", "mode": "focused", "dt": now - timedelta(days=5, hours=2), "dur": 60, "taken": 0, "snoozed": 0, "skipped": 0, "emergency": 0, "score": 1.0},
            {"task": "Bug bash session", "mode": "normal", "dt": now - timedelta(days=6, hours=5), "dur": 50, "taken": 2, "snoozed": 0, "skipped": 0, "emergency": 0, "score": 1.0},
        ]

        for item in prompt_history:
            st = item['dt'].isoformat()
            self._db.execute("""
                INSERT INTO work_sessions (
                    task_name, planned_duration_minutes, mode, start_time, end_time, status,
                    breaks_taken, breaks_snoozed, breaks_skipped, emergency_exits,
                    actual_duration_minutes, quality_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['task'], item['dur'], item['mode'], st, st, 'completed',
                item['taken'], item['snoozed'], item['skipped'], item['emergency'],
                item['dur'], item['score'], st[:10]
            ))

        # Add bulk historical data for charts (last 6 weeks)
        for i in range(7, 42):
            if random.random() > 0.4:
                num_sess = random.randint(1, 2)
                for _ in range(num_sess):
                    mode = random.choice(['normal', 'strict', 'focused'])
                    dur = random.choice([25, 52, 60, 90])
                    start_time = (now - timedelta(days=i, hours=random.randint(1, 12))).isoformat()
                    taken = random.randint(1, 2) if mode != 'focused' else 0
                    skipped = 1 if random.random() > 0.8 else 0
                    score = 1.0 if skipped == 0 else 0.7
                    self._db.execute("""
                        INSERT INTO work_sessions (
                            task_name, planned_duration_minutes, mode, start_time, end_time, status,
                            breaks_taken, breaks_snoozed, breaks_skipped, emergency_exits,
                            actual_duration_minutes, quality_score, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (f"Historic Task {i}", dur, mode, start_time, start_time, 'completed', taken, 0, skipped, 0, dur, score, start_time[:10]))

        self._db.commit()
        
        # Step: Update streaks for all seeded sessions
        # This ensures streak counts are calculated accurately from the historical data
        logger.info("Processing streaks for all seeded sessions...")
        all_sessions = self._db.execute("SELECT * FROM work_sessions WHERE status='completed' ORDER BY created_at").fetchall()
        
        # Reset streaks to start fresh
        for stype in ["session_streak", "perfect_session", "daily_consistency"]:
            self.update_streak(Streak(stype, 0, 0, ""))
        
        # Process each session in chronological order
        for session_row in all_sessions:
            session = WorkSession(**dict(session_row))
            milestones = streak_mgr.process_session_completion(session)
            if milestones:
                logger.info(f"  Streak milestones for session {session.id}: {[m['type'] for m in milestones]}")
        
        logger.info(f"Seeding complete. Total sessions: {len(all_sessions)}")

    def migrate_database(self) -> None:
        print("[DEBUG DB] migrate_database() called", flush=True)
        self._ensure_connected()
        print("[DEBUG DB] Checking for missing columns...", flush=True)
        c = self._db.cursor()
        c.execute("PRAGMA table_info(work_sessions)")
        cols = [r[1] for r in c.fetchall()]
        ws_req = {"emergency_exits": "INTEGER DEFAULT 0", "snooze_passes_remaining": "INTEGER DEFAULT 3", "extended_count": "INTEGER DEFAULT 0", "actual_duration_minutes": "INTEGER DEFAULT 0", "created_at": "TEXT DEFAULT ''"}
        for col, dtype in ws_req.items():
            if col not in cols: 
                print(f"[DEBUG DB] Adding missing column: {col}", flush=True)
                c.execute(f"ALTER TABLE work_sessions ADD COLUMN {col} {dtype}")
        self._db.commit()
        print("[DEBUG DB] migrate_database() complete", flush=True)

    def _ensure_connected(self) -> None:
        if self.conn is None:
            self.connect()
    
    @property
    def _db(self) -> sqlite3.Connection:
        """Get connection, ensuring it's connected. Raises if connection fails."""
        if self.conn is None:
            raise RuntimeError("Database connection is not established")
        return self.conn

    def update_streak(self, *args, **kwargs) -> None:
        """Update a streak.

        Supports both:
          - update_streak(Streak(...))
          - update_streak(streak_type: str, current_count: int, best_count: int, last_updated: str = "")
        """
        self._ensure_connected()
        stype = None
        cur = 0
        best = 0
        last = ""
        if len(args) == 1 and isinstance(args[0], Streak):
            s = args[0]
            stype = s.streak_type
            cur = s.current_count
            best = s.best_count
            last = s.last_updated
        elif len(args) >= 3 and isinstance(args[0], str):
            stype = args[0]
            cur = args[1]
            best = args[2]
            if len(args) >= 4:
                last = args[3]
        else:
            raise TypeError("update_streak expects a Streak object or (streak_type, current_count, best_count[, last_updated])")

        self._db.execute("INSERT OR REPLACE INTO streaks (streak_type, current_count, best_count, last_updated) VALUES (?, ?, ?, ?)", (stype, cur, best, last))
        self._db.commit()

    def get_streaks(self) -> Dict[str, Streak]:
        self._ensure_connected()
        rows = self._db.execute("SELECT * FROM streaks").fetchall()
        return {r["streak_type"]: Streak(**dict(r)) for r in rows}

    def get_all_sessions(self, limit: Optional[int] = 50) -> List[WorkSession]:
        self._ensure_connected()
        if limit is None:
            rows = self._db.execute("SELECT * FROM work_sessions WHERE status != 'in_progress' ORDER BY start_time DESC").fetchall()
        else:
            rows = self._db.execute("SELECT * FROM work_sessions WHERE status != 'in_progress' ORDER BY start_time DESC LIMIT ?", (limit,)).fetchall()
        return [WorkSession(**dict(r)) for r in rows]

    def getSession(self, session_id: int) -> Optional[WorkSession]:
        """Return a single WorkSession by id."""
        self._ensure_connected()
        row = self._db.execute("SELECT * FROM work_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            return None
        return WorkSession(**dict(row))

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks as Task objects."""
        self._ensure_connected()
        rows = self._db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [Task(**dict(r)) for r in rows]

    def _calculate_compliance(self, sessions_data, settings) -> int:
        """Helper to calculate break compliance percentage from session rows."""
        total_taken = 0
        total_expected = 0
        for row in sessions_data:
            # row format: (mode, actual_min, start, end, taken)
            mode, actual_min, start, end, taken = row
            
            # Cross-validate duration
            calc_min = actual_min
            if start and end:
                try:
                    s_dt = datetime.fromisoformat(start)
                    e_dt = datetime.fromisoformat(end)
                    calc_min = round((e_dt - s_dt).total_seconds() / 60)
                except: pass
            
            total_taken += (taken or 0)
            if mode == "normal":
                interval, brk_dur = settings.normal_work_interval, settings.normal_break_duration
            elif mode == "strict":
                interval, brk_dur = settings.strict_work_interval, settings.strict_break_duration
            else: # focused
                if calc_min > 5: total_expected += 1
                continue
                
            offset = interval
            while offset < calc_min:
                total_expected += 1
                offset += interval + brk_dur
        return round((total_taken / total_expected * 100)) if total_expected > 0 else 100

    def get_stats(self) -> dict:
        self._ensure_connected()
        status_filter = "('completed', 'ended_by_user')"
        
        total = self._db.execute(f"SELECT COUNT(*) FROM work_sessions WHERE status IN {status_filter}").fetchone()[0]
        total_min = self._db.execute(f"SELECT SUM(actual_duration_minutes) FROM work_sessions WHERE status IN {status_filter}").fetchone()[0] or 0
        avg_q = self._db.execute(f"SELECT AVG(quality_score) FROM work_sessions WHERE status IN {status_filter}").fetchone()[0] or 0.0
        
        # We still need sessions_data for compliance calculation
        sessions_data = self._db.execute(f"""
            SELECT mode, actual_duration_minutes, start_time, end_time, breaks_taken 
            FROM work_sessions WHERE status IN {status_filter}
        """).fetchall()
        settings = self.get_settings()
        compliance = self._calculate_compliance(sessions_data, settings)

        return {
            "total_sessions": total, 
            "total_hours": round(total_min / 60, 1), 
            "avg_quality": round(avg_q, 2), 
            "break_compliance": compliance
        }

    def get_detailed_stats(self) -> Dict:
        self._ensure_connected()
        status_filter = "('completed', 'ended_by_user')"
        # 1. Bar Chart: Work hours / day (last 7 days)
        today = date.today()
        bar_data = []
        bar_labels = []
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            res = self._db.execute(f"SELECT SUM(actual_duration_minutes) FROM work_sessions WHERE status IN {status_filter} AND DATE(start_time) = ?", (d,)).fetchone()
            bar_data.append(round((res[0] or 0) / 60, 1))
            bar_labels.append((today - timedelta(days=i)).strftime("%a"))

        # 2. Line Chart: Compliance over time (last 6 weeks)
        line_data = []
        line_labels = []
        settings = self.get_settings()
        for i in range(5, -1, -1):
            start_date = (today - timedelta(weeks=i+1)).isoformat()
            end_date = (today - timedelta(weeks=i)).isoformat()
            rows = self._db.execute(f"""
                SELECT mode, actual_duration_minutes, start_time, end_time, breaks_taken 
                FROM work_sessions WHERE status IN {status_filter} AND start_time > ? AND start_time <= ?
            """, (start_date + "T00:00:00", end_date + "T23:59:59")).fetchall()
            
            comp = self._calculate_compliance(rows, settings)
            line_data.append(comp)
            line_labels.append(f"W{6-i}")

        # 3. Donut: Mode distribution
        mode_rows = self._db.execute(f"SELECT mode, COUNT(*) FROM work_sessions WHERE status IN {status_filter} GROUP BY mode").fetchall()
        total_m = sum(r[1] for r in mode_rows)
        mode_dist = {r[0]: round(r[1]/total_m * 100) for r in mode_rows} if total_m > 0 else {}

        # 4. Heatmap: Activity (last 15 weeks = 105 days)
        heatmap = {}
        for i in range(104, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            res = self._db.execute(f"SELECT COUNT(*) FROM work_sessions WHERE status IN {status_filter} AND DATE(start_time) = ?", (d,)).fetchone()
            heatmap[d] = res[0]
        
        heatmap_max = max(heatmap.values()) if heatmap.values() else 1
        if heatmap_max == 0:
            heatmap_max = 1

        # 5. Highlights
        prod_day_row = self._db.execute(f"""
            SELECT strftime('%w', start_time) as dw, SUM(actual_duration_minutes) as m 
            FROM work_sessions WHERE status IN {status_filter} GROUP BY dw ORDER BY m DESC LIMIT 1
        """).fetchone()
        prod_day = { "0": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday", "4": "Thursday", "5": "Friday", "6": "Saturday" }.get(prod_day_row[0], "N/A") if prod_day_row else "N/A"
        
        fav_mode_row = self._db.execute(f"SELECT mode, COUNT(*) as c FROM work_sessions WHERE status IN {status_filter} GROUP BY mode ORDER BY c DESC LIMIT 1").fetchone()
        fav_mode = fav_mode_row[0].capitalize() if fav_mode_row else "N/A"
        
        avg_len = self._db.execute(f"SELECT AVG(actual_duration_minutes) FROM work_sessions WHERE status IN {status_filter}").fetchone()[0] or 0
        exits = self._db.execute("SELECT SUM(emergency_exits) FROM work_sessions").fetchone()[0] or 0
        perfects = self._db.execute(f"SELECT COUNT(*) FROM work_sessions WHERE quality_score >= 1.0 AND status IN {status_filter}").fetchone()[0]

        # 6. Break Breakdown
        break_stats = self._db.execute(f"""
            SELECT SUM(breaks_taken), SUM(breaks_snoozed), SUM(breaks_skipped)
            FROM work_sessions WHERE status IN {status_filter}
        """).fetchone()
        break_breakdown = {
            "completed": break_stats[0] or 0,
            "snoozed": break_stats[1] or 0,
            "skipped": break_stats[2] or 0
        }

        # 7. Overview deltas (vs last 30d)
        overview = self.get_stats()
        
        # Calculate prior 30 days stats
        d30 = (today - timedelta(days=30)).isoformat() + "T00:00:00"
        d60 = (today - timedelta(days=60)).isoformat() + "T00:00:00"
        
        # Prior 30 days totals
        rows_p = self._db.execute(f"""
            SELECT mode, actual_duration_minutes, start_time, end_time, breaks_taken 
            FROM work_sessions WHERE status IN {status_filter} AND start_time >= ? AND start_time < ?
        """, (d60, d30)).fetchall()
        
        total_p = len(rows_p)
        total_min_p = sum([r[1] for r in rows_p])
        avg_q_p = self._db.execute(f"SELECT AVG(quality_score) FROM work_sessions WHERE status IN {status_filter} AND quality_score IS NOT NULL AND start_time >= ? AND start_time < ?", (d60, d30)).fetchone()[0] or 0.0
        compliance_p = self._calculate_compliance(rows_p, settings)

        # Current 30 days totals
        rows_c = self._db.execute(f"""
            SELECT mode, actual_duration_minutes, start_time, end_time, breaks_taken 
            FROM work_sessions WHERE status IN {status_filter} AND start_time >= ?
        """, (d30,)).fetchall()
        
        total_c = len(rows_c)
        total_min_c = sum([r[1] for r in rows_c])
        avg_q_c = self._db.execute(f"SELECT AVG(quality_score) FROM work_sessions WHERE status IN {status_filter} AND quality_score IS NOT NULL AND start_time >= ?", (d30,)).fetchone()[0] or 0.0
        compliance_c = self._calculate_compliance(rows_c, settings)

        # Format deltas with proper rounding
        delta_hours = round(total_min_c / 60, 1) - round(total_min_p / 60, 1)
        delta_quality = avg_q_c - avg_q_p  # Quality is 0-1 scale, no 100x multiplier
        deltas = {
            "sessions": total_c - total_p,
            "hours": round(delta_hours, 1),
            "quality": round(delta_quality, 2),
            "compliance": compliance_c - compliance_p
        }

        return {
            "overview": overview,
            "deltas": deltas,
            "bar": {"data": bar_data, "labels": bar_labels},
            "line": {"data": line_data, "labels": line_labels},
            "donut": mode_dist,
            "heatmap": heatmap,
            "heatmap_max": heatmap_max,
            "break_breakdown": break_breakdown,
            "highlights": {
                "prod_day": prod_day, "fav_mode": fav_mode, "exits": exits,
                "avg_len": f"{round(avg_len)} min", "perfects": perfects
            }
        }

    def get_achievement_stats(self) -> Dict[str, int]:
        self._ensure_connected()
        total_s = self._db.execute("SELECT COUNT(*) FROM work_sessions WHERE status='completed'").fetchone()[0]
        total_h = round((self._db.execute("SELECT SUM(actual_duration_minutes) FROM work_sessions WHERE status='completed'").fetchone()[0] or 0) / 60)
        streaks = self.get_streaks()
        strict_s = self._db.execute("SELECT COUNT(*) FROM work_sessions WHERE status='completed' AND mode='strict'").fetchone()[0]
        focused_s = self._db.execute("SELECT COUNT(*) FROM work_sessions WHERE status='completed' AND mode='focused'").fetchone()[0]
        modes_w = self._db.execute("SELECT COUNT(DISTINCT mode) FROM work_sessions WHERE status='completed' AND start_time >= date('now', '-7 days')").fetchone()[0]
        no_exit_s = self._db.execute("SELECT COUNT(*) FROM work_sessions WHERE status='completed' AND emergency_exits = 0").fetchone()[0]
        total_b = self._db.execute("SELECT SUM(breaks_taken) FROM work_sessions WHERE status='completed'").fetchone()[0] or 0
        
        rows = self._db.execute("SELECT quality_score FROM work_sessions WHERE status='completed' ORDER BY start_time DESC LIMIT 10").fetchall()
        consecutive_p = 0
        for r in rows:
            if r[0] >= 1.0: consecutive_p += 1
            else: break

        return {
            "sessions": total_s, "hours": total_h, "modes_used": modes_w,
            "daily_streak": streaks['daily_consistency'].current_count,
            "perfect_sessions": streaks['perfect_session'].current_count,
            "consecutive_perfect": consecutive_p,
            "strict_sessions": strict_s, "focused_sessions": focused_s,
            "no_exit_sessions": no_exit_s, "total_breaks": total_b
        }

    def get_settings(self) -> Settings:
        self._ensure_connected()
        rows = self._db.execute("SELECT key, value FROM settings").fetchall()
        d = {r["key"]: r["value"] for r in rows}
        import dataclasses
        kwargs = {}
        for field in dataclasses.fields(Settings):
            if field.name in d:
                val = d[field.name]; tf = type(field.default)
                if field.type == bool or field.type == 'bool' or tf == bool: kwargs[field.name] = (val == 'True' or val == '1')
                else:
                    try: kwargs[field.name] = (tf or field.type)(val)
                    except: kwargs[field.name] = val
        return Settings(**kwargs)

    def save_settings(self, settings: Settings):
        self._ensure_connected()
        import dataclasses
        data = {k: str(v) for k, v in dataclasses.asdict(settings).items()}
        for k, v in data.items(): self._db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v))
        self._db.commit()

    def is_first_run(self) -> bool:
        self._ensure_connected()
        row = self._db.execute("SELECT value FROM settings WHERE key='is_first_run'").fetchone()
        return row[0] == "True" if row else False

    def complete_first_run(self) -> None:
        self._ensure_connected()
        self._db.execute("UPDATE settings SET value='False' WHERE key='is_first_run'")
        self._db.commit()

    def _cleanup_crashed_sessions(self):
        """Mark any lingering 'in_progress' sessions as 'crashed' on startup."""
        self._ensure_connected()
        now = datetime.now().isoformat()
        self._db.execute("UPDATE work_sessions SET status = 'crashed', end_time = ? WHERE status = 'in_progress'", (now,))
        self._db.commit()

    def log_event(self, event_type: str, session_id: Optional[int] = None, break_id: Optional[int] = None, description: str = "") -> None:
        self._ensure_connected()
        now = datetime.now().isoformat()
        self._db.execute("INSERT INTO activity_logs (event_type, session_id, break_id, description, timestamp) VALUES (?, ?, ?, ?, ?)", (event_type, session_id, break_id, description, now))
        self._db.commit()

    def create_task(self, task: Task) -> Optional[int]:
        self._ensure_connected()
        c = self._db.cursor(); now = datetime.now().isoformat()
        logger.info(
            "Persisting task to database: name=%s duration=%s mode=%s auto_breaks=%s manual_break_count=%s manual_break_duration=%s",
            task.name,
            task.allocated_time_minutes,
            task.mode,
            task.auto_calculate_breaks,
            task.manual_break_count,
            task.manual_break_duration,
        )
        c.execute("""INSERT INTO tasks (name, allocated_time_minutes, mode, auto_calculate_breaks, manual_break_count, manual_break_duration, created_at) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                  (task.name, task.allocated_time_minutes, task.mode, 1 if task.auto_calculate_breaks else 0, task.manual_break_count, task.manual_break_duration, now))
        self._db.commit()
        task_id = c.lastrowid
        logger.info("Task persisted with id=%s", task_id)
        return task_id

    def createSession(self, session: WorkSession) -> Optional[int]:
        self._ensure_connected()
        c = self._db.cursor(); now = datetime.now().isoformat()
        c.execute("""INSERT INTO work_sessions (task_id, task_name, planned_duration_minutes, mode, start_time, status, snooze_passes_remaining, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (session.task_id, session.task_name, session.planned_duration_minutes, session.mode, now, 'in_progress', session.snooze_passes_remaining, now))
        self._db.commit(); return c.lastrowid

    def get_next_break_seconds(self, session_id: int, elapsed_seconds: int) -> Optional[int]:
        self._ensure_connected()
        row = self._db.execute("SELECT scheduled_offset_minutes FROM breaks WHERE session_id=? AND status='pending' ORDER BY scheduled_offset_minutes ASC LIMIT 1", (session_id,)).fetchone()
        if not row: return None
        rem = (row[0] * 60) - elapsed_seconds
        return max(0, rem)

    def updateSession(self, session_or_id, **kwargs) -> None:
        """Update work session fields.

        Accepts either a session id or a WorkSession object. If a WorkSession is provided,
        its attributes will be used to build the update payload.
        """
        self._ensure_connected()
        if session_or_id is None:
            return
        if hasattr(session_or_id, 'id'):
            session_id = session_or_id.id
            # Build kwargs from object's attributes if none provided
            if not kwargs:
                # only update fields that differ from defaults; here we send core mutable fields
                attrs = ['status', 'end_time', 'breaks_taken', 'breaks_snoozed', 'breaks_skipped', 'emergency_exits', 'actual_duration_minutes', 'quality_score']
                for a in attrs:
                    if hasattr(session_or_id, a):
                        kwargs[a] = getattr(session_or_id, a)
        else:
            session_id = session_or_id

        if not session_id:
            return
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key}=?")
            values.append(value)
        if not fields:
            return
        values.append(session_id)
        query = f"UPDATE work_sessions SET {', '.join(fields)} WHERE id=?"
        self._db.execute(query, values)
        self._db.commit()

    def updateBreak(self, break_id: int, **kwargs) -> None:
        """Update break fields."""
        self._ensure_connected()
        if not break_id:
            return
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key}=?")
            values.append(value)
        if not fields:
            return
        values.append(break_id)
        query = f"UPDATE breaks SET {', '.join(fields)} WHERE id=?"
        self._db.execute(query, values)
        self._db.commit()

    def canSnooze(self, session_id: int) -> bool:
        """Check if a session can use snooze passes."""
        self._ensure_connected()
        if not session_id:
            return False
        row = self._db.execute("SELECT snooze_passes_remaining FROM work_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            return False
        return row[0] > 0 if row[0] else False

    def useSnoozePass(self, session_id: int) -> None:
        """Decrement snooze pass count."""
        self._ensure_connected()
        if not session_id:
            return
        self._db.execute("UPDATE work_sessions SET snooze_passes_remaining = snooze_passes_remaining - 1 WHERE id=?", (session_id,))
        self._db.commit()

    def redistributeRemainingBreaks(self, session_id: int) -> None:
        """Redistribute remaining pending breaks after a snooze."""
        self._ensure_connected()
        if not session_id:
            return
        try:
            # Get all pending breaks for this session
            breaks = self._db.execute(
                "SELECT id, scheduled_offset_minutes FROM breaks WHERE session_id=? AND status='pending' ORDER BY scheduled_offset_minutes ASC",
                (session_id,)
            ).fetchall()
            
            if not breaks:
                return
            
            # Get session info
            session = self._db.execute("SELECT planned_duration_minutes FROM work_sessions WHERE id=?", (session_id,)).fetchone()
            if not session:
                return
            
            total_duration = session[0]
            interval = self._db.execute("SELECT value FROM settings WHERE key='normal_work_interval'").fetchone()
            interval_mins = int(interval[0]) if interval else 25
            
            # Redistribute breaks evenly across remaining time
            pending_breaks = [b for b in breaks if b[1] < total_duration]
            if pending_breaks:
                step = total_duration // (len(pending_breaks) + 1)
                for i, brk in enumerate(pending_breaks):
                    new_offset = (i + 1) * step
                    if new_offset < total_duration:
                        self._db.execute(
                            "UPDATE breaks SET scheduled_offset_minutes=? WHERE id=?",
                            (new_offset, brk[0])
                        )
            
            self._db.commit()
            logger.debug(f"Redistributed {len(pending_breaks)} breaks for session {session_id}")
        except Exception as e:
            logger.error(f"Error redistributing breaks for session {session_id}: {e}")
            self._db.rollback()

    def get_user_media(self, mode: Optional[str] = None) -> List[Dict]:
        """Get configured media files for a given mode."""
        self._ensure_connected()
        if mode is not None:
            rows = self._db.execute(
                "SELECT file_path, is_jumpscare, enabled FROM break_media WHERE mode=? AND enabled=1 ORDER BY RANDOM()",
                (mode,)
            ).fetchall()
        else:
            rows = self._db.execute(
                "SELECT file_path, is_jumpscare, enabled FROM break_media WHERE enabled=1 ORDER BY RANDOM()"
            ).fetchall()
        return [{"file_path": r[0], "is_jumpscare": r[1], "enabled": r[2]} for r in rows]

    def reset_database(self) -> None:
        """Reset the database to initial state (wipes everything including settings)."""
        self._ensure_connected()
        tables = ['activity_logs', 'breaks', 'work_sessions', 'tasks', 'break_media', 'streaks', 'settings']
        for table in tables:
            self._db.execute(f"DELETE FROM {table}")
        
        # Re-initialize streaks
        for stype in ["session_streak", "perfect_session", "daily_consistency"]:
            self._db.execute(
                "INSERT OR REPLACE INTO streaks (streak_type, current_count, best_count, last_updated) VALUES (?, ?, ?, ?)",
                (stype, 0, 0, '')
            )
        
        # Re-initialize default settings
        defaults = {
            "username": "User", "is_first_run": "True", "first_close_notified": "False", "normal_work_interval": "25",
            "normal_break_duration": "5", "normal_snooze_duration": "5", "max_snooze_passes": "3",
            "allow_skip_in_normal_mode": "True", "snooze_redistributes_breaks": "True",
            "strict_work_interval": "52", "strict_break_duration": "17", "strict_cooldown": "20",
            "focused_mandatory_break": "30", "media_volume": "80", "alarm_volume": "70", "alarm_duration": "5"
        }
        for k, v in defaults.items():
            self._db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

        self._db.commit()

