# app/services/progression_service.py
"""
Progression & XP System for Language Learning App
Tracks user progress across all activities and calculates level progression.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

from app.services.db_supabase import (
    get_client,
    current_user_id,
    get_current_profile,
)


# ============================================================================
# XP Configuration
# ============================================================================

@dataclass
class XPConfig:
    """XP rewards for different activities"""

    # Chat activities
    CHAT_MESSAGE_SENT: int = 5
    CHAT_MESSAGE_NO_ERRORS: int = 10  # Bonus for error-free message
    GRAMMAR_ERROR_CORRECTED: int = 3  # Learning from mistakes

    # Vocabulary
    VOCAB_WORD_LEARNED: int = 15
    VOCAB_WORD_REVIEWED: int = 5
    VOCAB_WORD_MASTERED: int = 25  # After 5 correct reviews

    # Listening
    LISTENING_QUIZ_COMPLETED: int = 20
    LISTENING_CORRECT_ANSWER: int = 8
    LISTENING_PERFECT_SCORE: int = 30  # Bonus

    # Reading
    READING_ARTICLE_STARTED: int = 10
    READING_ARTICLE_COMPLETED: int = 30
    READING_COMPREHENSION_CORRECT: int = 10

    # Streaks & Bonuses
    DAILY_LOGIN: int = 20
    STREAK_MULTIPLIER_PER_DAY: float = 0.05  # +5% per streak day, max 50%
    MAX_STREAK_MULTIPLIER: float = 0.50

    # Placement test
    PLACEMENT_TEST_COMPLETED: int = 100


@dataclass
class LevelThreshold:
    """XP thresholds for each CEFR level"""
    level: str
    min_xp: int
    max_xp: int
    title: str
    color: str


LEVEL_THRESHOLDS: List[LevelThreshold] = [
    LevelThreshold("A1", 0, 1000, "Beginner", "#4caf50"),
    LevelThreshold("A2", 1000, 3000, "Elementary", "#2196f3"),
    LevelThreshold("B1", 3000, 7000, "Intermediate", "#ff9800"),
    LevelThreshold("B2", 7000, 15000, "Upper-Intermediate", "#e91e63"),
    LevelThreshold("C1", 15000, 30000, "Advanced", "#9c27b0"),
    LevelThreshold("C2", 30000, 999999, "Proficient", "#795548"),
]


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class UserProgress:
    """Current user progress snapshot"""
    user_id: str
    total_xp: int = 0
    current_level: str = "A1"
    xp_to_next_level: int = 0
    progress_percent: float = 0.0
    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: Optional[str] = None

    # Activity counts
    total_messages: int = 0
    total_words_learned: int = 0
    total_listening_quizzes: int = 0
    total_reading_articles: int = 0
    total_grammar_corrections: int = 0

    # Today's stats
    xp_earned_today: int = 0
    activities_today: int = 0


@dataclass
class XPEvent:
    """A single XP earning event"""
    event_type: str
    xp_amount: int
    description: str
    bonus_applied: float = 0.0
    timestamp: Optional[datetime] = None


# ============================================================================
# Progression Service
# ============================================================================

class ProgressionService:
    """
    Manages user progression, XP tracking, and level calculations.

    Usage:
        service = ProgressionService()

        # Award XP for activities
        service.award_xp("chat_message", {"has_errors": False})
        service.award_xp("vocab_learned", {"word": "hello"})

        # Get current progress
        progress = service.get_progress()
        print(f"Level: {progress.current_level}, XP: {progress.total_xp}")
    """

    def __init__(self):
        self.config = XPConfig()
        self._sb = get_client()

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------

    def get_progress(self) -> Optional[UserProgress]:
        """Get current user's complete progress snapshot."""
        uid = current_user_id()
        if not uid:
            return None

        try:
            # Get or create progress record
            progress_data = self._get_or_create_progress(uid)

            # Calculate derived values
            level_info = self._get_level_info(progress_data["total_xp"])
            streak_info = self._calculate_streak(uid)
            today_stats = self._get_today_stats(uid)

            return UserProgress(
                user_id=uid,
                total_xp=progress_data["total_xp"],
                current_level=level_info["level"],
                xp_to_next_level=level_info["xp_to_next"],
                progress_percent=level_info["progress_percent"],
                current_streak=streak_info["current"],
                longest_streak=streak_info["longest"],
                last_activity_date=progress_data.get("last_activity_date"),
                total_messages=progress_data.get("total_messages", 0),
                total_words_learned=progress_data.get("total_words_learned", 0),
                total_listening_quizzes=progress_data.get("total_listening_quizzes", 0),
                total_reading_articles=progress_data.get("total_reading_articles", 0),
                total_grammar_corrections=progress_data.get("total_grammar_corrections", 0),
                xp_earned_today=today_stats["xp"],
                activities_today=today_stats["count"],
            )
        except Exception as e:
            print(f"[ProgressionService] Error getting progress: {e}")
            return None

    def award_xp(
            self,
            event_type: str,
            context: Optional[Dict[str, Any]] = None
    ) -> Optional[XPEvent]:
        """
        Award XP for an activity.

        Args:
            event_type: Type of activity (e.g., "chat_message", "vocab_learned")
            context: Additional context for XP calculation

        Returns:
            XPEvent with details of XP awarded, or None if failed
        """
        uid = current_user_id()
        if not uid:
            return None

        context = context or {}

        try:
            # Calculate base XP
            base_xp, description = self._calculate_xp(event_type, context)
            if base_xp <= 0:
                return None

            # Apply streak bonus
            streak_info = self._calculate_streak(uid)
            streak_multiplier = min(
                streak_info["current"] * self.config.STREAK_MULTIPLIER_PER_DAY,
                self.config.MAX_STREAK_MULTIPLIER
            )
            bonus_xp = int(base_xp * streak_multiplier)
            total_xp = base_xp + bonus_xp

            # Record the XP event
            self._record_xp_event(uid, event_type, total_xp, context)

            # Update progress totals
            self._update_progress_totals(uid, event_type, total_xp)

            # Check for level up
            self._check_level_up(uid)

            return XPEvent(
                event_type=event_type,
                xp_amount=total_xp,
                description=description,
                bonus_applied=streak_multiplier,
                timestamp=datetime.now(),
            )

        except Exception as e:
            print(f"[ProgressionService] Error awarding XP: {e}")
            return None

    def check_daily_login(self) -> Optional[XPEvent]:
        """Check and award daily login bonus if applicable."""
        uid = current_user_id()
        if not uid:
            return None

        try:
            today = datetime.now().date().isoformat()

            # Check if already logged in today
            res = (
                self._sb.table("user_xp_events")
                .select("id")
                .eq("user_id", uid)
                .eq("event_type", "daily_login")
                .gte("created_at", today)
                .limit(1)
                .execute()
            )

            if res.data:
                return None  # Already claimed today

            # Award daily login XP
            return self.award_xp("daily_login", {})

        except Exception as e:
            print(f"[ProgressionService] Error checking daily login: {e}")
            return None

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by XP (for gamification)."""
        try:
            res = (
                self._sb.table("user_progress")
                .select("user_id, total_xp, current_streak")
                .order("total_xp", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception:
            return []

    def get_recent_xp_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent XP events for the current user."""
        uid = current_user_id()
        if not uid:
            return []

        try:
            res = (
                self._sb.table("user_xp_events")
                .select("*")
                .eq("user_id", uid)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception:
            return []

    def get_achievements(self) -> List[Dict[str, Any]]:
        """Get user's earned achievements/badges."""
        uid = current_user_id()
        if not uid:
            return []

        try:
            res = (
                self._sb.table("user_achievements")
                .select("*")
                .eq("user_id", uid)
                .order("earned_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception:
            return []

    # ------------------------------------------------------------------------
    # XP Calculation
    # ------------------------------------------------------------------------

    def _calculate_xp(
            self,
            event_type: str,
            context: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Calculate base XP for an event type."""

        cfg = self.config

        if event_type == "chat_message":
            has_errors = context.get("has_errors", True)
            error_count = context.get("error_count", 0)

            base = cfg.CHAT_MESSAGE_SENT
            if not has_errors:
                base += cfg.CHAT_MESSAGE_NO_ERRORS

            # Small bonus for corrected errors (learning)
            if error_count > 0:
                base += min(error_count * cfg.GRAMMAR_ERROR_CORRECTED, 15)

            return base, f"Chat message sent (+{base} XP)"

        elif event_type == "vocab_learned":
            word = context.get("word", "")
            return cfg.VOCAB_WORD_LEARNED, f"Learned word: {word}"

        elif event_type == "vocab_reviewed":
            return cfg.VOCAB_WORD_REVIEWED, "Reviewed vocabulary"

        elif event_type == "vocab_mastered":
            word = context.get("word", "")
            return cfg.VOCAB_WORD_MASTERED, f"Mastered word: {word}"

        elif event_type == "listening_completed":
            score = context.get("score", 0)
            total = context.get("total", 1)
            correct = context.get("correct", 0)

            base = cfg.LISTENING_QUIZ_COMPLETED
            base += correct * cfg.LISTENING_CORRECT_ANSWER

            if correct == total and total > 0:
                base += cfg.LISTENING_PERFECT_SCORE

            return base, f"Listening quiz: {correct}/{total} correct"

        elif event_type == "reading_started":
            return cfg.READING_ARTICLE_STARTED, "Started reading article"

        elif event_type == "reading_completed":
            comprehension_score = context.get("comprehension_score", 0)
            base = cfg.READING_ARTICLE_COMPLETED
            base += int(comprehension_score * cfg.READING_COMPREHENSION_CORRECT)
            return base, "Completed reading article"

        elif event_type == "daily_login":
            return cfg.DAILY_LOGIN, "Daily login bonus"

        elif event_type == "placement_test":
            return cfg.PLACEMENT_TEST_COMPLETED, "Completed placement test"

        elif event_type == "grammar_correction":
            return cfg.GRAMMAR_ERROR_CORRECTED, "Learned from grammar mistake"

        return 0, ""

    # ------------------------------------------------------------------------
    # Level Calculation
    # ------------------------------------------------------------------------

    def _get_level_info(self, total_xp: int) -> Dict[str, Any]:
        """Calculate level information from total XP."""

        current_threshold = LEVEL_THRESHOLDS[0]
        next_threshold = LEVEL_THRESHOLDS[1] if len(LEVEL_THRESHOLDS) > 1 else None

        for i, threshold in enumerate(LEVEL_THRESHOLDS):
            if total_xp >= threshold.min_xp:
                current_threshold = threshold
                next_threshold = (
                    LEVEL_THRESHOLDS[i + 1]
                    if i + 1 < len(LEVEL_THRESHOLDS)
                    else None
                )

        # Calculate progress to next level
        if next_threshold:
            xp_in_level = total_xp - current_threshold.min_xp
            xp_needed = next_threshold.min_xp - current_threshold.min_xp
            progress_percent = min(100, (xp_in_level / xp_needed) * 100)
            xp_to_next = next_threshold.min_xp - total_xp
        else:
            # Max level reached
            progress_percent = 100.0
            xp_to_next = 0

        return {
            "level": current_threshold.level,
            "title": current_threshold.title,
            "color": current_threshold.color,
            "progress_percent": progress_percent,
            "xp_to_next": xp_to_next,
            "min_xp": current_threshold.min_xp,
            "max_xp": current_threshold.max_xp if next_threshold else total_xp,
        }

    # ------------------------------------------------------------------------
    # Streak Calculation
    # ------------------------------------------------------------------------

    def _calculate_streak(self, uid: str) -> Dict[str, int]:
        """Calculate current and longest streak for user."""
        try:
            res = (
                self._sb.table("user_progress")
                .select("current_streak, longest_streak, last_activity_date")
                .eq("user_id", uid)
                .limit(1)
                .execute()
            )

            if not res.data:
                return {"current": 0, "longest": 0}

            data = res.data[0]
            current = data.get("current_streak", 0)
            longest = data.get("longest_streak", 0)
            last_date = data.get("last_activity_date")

            # Check if streak is still valid (activity within last 24-48 hours)
            if last_date:
                try:
                    last_dt = datetime.fromisoformat(last_date.replace("Z", "+00:00"))
                    now = datetime.now(last_dt.tzinfo) if last_dt.tzinfo else datetime.now()
                    days_since = (now.date() - last_dt.date()).days

                    if days_since > 1:
                        # Streak broken
                        current = 0
                except Exception:
                    pass

            return {"current": current, "longest": longest}

        except Exception:
            return {"current": 0, "longest": 0}

    # ------------------------------------------------------------------------
    # Database Operations
    # ------------------------------------------------------------------------

    def _get_or_create_progress(self, uid: str) -> Dict[str, Any]:
        """Get or create user progress record."""
        res = (
            self._sb.table("user_progress")
            .select("*")
            .eq("user_id", uid)
            .limit(1)
            .execute()
        )

        if res.data:
            return res.data[0]

        # Create new record
        new_record = {
            "user_id": uid,
            "total_xp": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "total_messages": 0,
            "total_words_learned": 0,
            "total_listening_quizzes": 0,
            "total_reading_articles": 0,
            "total_grammar_corrections": 0,
        }

        ins = self._sb.table("user_progress").insert(new_record).execute()
        return ins.data[0] if ins.data else new_record

    def _record_xp_event(
            self,
            uid: str,
            event_type: str,
            xp_amount: int,
            context: Dict[str, Any]
    ):
        """Record an XP event to history."""
        self._sb.table("user_xp_events").insert({
            "user_id": uid,
            "event_type": event_type,
            "xp_amount": xp_amount,
            "context": context,
        }).execute()

    def _update_progress_totals(
            self,
            uid: str,
            event_type: str,
            xp_earned: int
    ):
        """Update user's progress totals."""
        today = datetime.now().date().isoformat()

        # Get current progress
        progress = self._get_or_create_progress(uid)

        # Calculate updates
        updates = {
            "total_xp": progress["total_xp"] + xp_earned,
            "last_activity_date": today,
        }

        # Update streak
        last_date = progress.get("last_activity_date")
        current_streak = progress.get("current_streak", 0)
        longest_streak = progress.get("longest_streak", 0)

        if last_date:
            try:
                last_dt = datetime.fromisoformat(last_date)
                days_diff = (datetime.now().date() - last_dt.date()).days

                if days_diff == 0:
                    pass  # Same day, no streak change
                elif days_diff == 1:
                    current_streak += 1  # Consecutive day
                else:
                    current_streak = 1  # Streak broken, start new
            except Exception:
                current_streak = 1
        else:
            current_streak = 1

        updates["current_streak"] = current_streak
        updates["longest_streak"] = max(longest_streak, current_streak)

        # Update activity-specific counters
        if event_type == "chat_message":
            updates["total_messages"] = progress.get("total_messages", 0) + 1
        elif event_type in ("vocab_learned", "vocab_mastered"):
            updates["total_words_learned"] = progress.get("total_words_learned", 0) + 1
        elif event_type == "listening_completed":
            updates["total_listening_quizzes"] = progress.get("total_listening_quizzes", 0) + 1
        elif event_type in ("reading_started", "reading_completed"):
            updates["total_reading_articles"] = progress.get("total_reading_articles", 0) + 1
        elif event_type == "grammar_correction":
            updates["total_grammar_corrections"] = progress.get("total_grammar_corrections", 0) + 1

        # Save to database
        self._sb.table("user_progress").update(updates).eq("user_id", uid).execute()

    def _get_today_stats(self, uid: str) -> Dict[str, int]:
        """Get XP earned and activities count for today."""
        today = datetime.now().date().isoformat()

        try:
            res = (
                self._sb.table("user_xp_events")
                .select("xp_amount")
                .eq("user_id", uid)
                .gte("created_at", today)
                .execute()
            )

            events = res.data or []
            total_xp = sum(e.get("xp_amount", 0) for e in events)

            return {"xp": total_xp, "count": len(events)}

        except Exception:
            return {"xp": 0, "count": 0}

    def _check_level_up(self, uid: str):
        """Check if user leveled up and update profile if needed."""
        progress = self._get_or_create_progress(uid)
        level_info = self._get_level_info(progress["total_xp"])

        # Get current profile level
        profile = get_current_profile()
        current_level = profile.get("cefr_level") if profile else None

        new_level = level_info["level"]

        # If calculated level is higher, update profile
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if current_level and new_level:
            try:
                current_idx = level_order.index(current_level)
                new_idx = level_order.index(new_level)

                if new_idx > current_idx:
                    # Level up! Update profile
                    from app.services.db_supabase import update_profile_level
                    update_profile_level(new_level)

                    # Record achievement
                    self._record_achievement(uid, f"level_up_{new_level}", {
                        "from_level": current_level,
                        "to_level": new_level,
                        "total_xp": progress["total_xp"],
                    })
            except ValueError:
                pass

    def _record_achievement(
            self,
            uid: str,
            achievement_type: str,
            context: Dict[str, Any]
    ):
        """Record an achievement for the user."""
        try:
            self._sb.table("user_achievements").insert({
                "user_id": uid,
                "achievement_type": achievement_type,
                "context": context,
            }).execute()
        except Exception as e:
            print(f"[ProgressionService] Error recording achievement: {e}")


# ============================================================================
# Singleton instance
# ============================================================================

_progression_service: Optional[ProgressionService] = None

def get_progression_service() -> ProgressionService:
    """Get the singleton ProgressionService instance."""
    global _progression_service
    if _progression_service is None:
        _progression_service = ProgressionService()
    return _progression_service