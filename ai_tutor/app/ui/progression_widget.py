# app/ui/progression_widget.py
"""
Progression Display Widget - Shows user's XP, level, and progress bar.
"""

from __future__ import annotations

from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui

try:
    from app.services.progression_service import (
        get_progression_service,
        UserProgress,
        LEVEL_THRESHOLDS,
    )
except ImportError:
    UserProgress = None
    LEVEL_THRESHOLDS = []
    def get_progression_service():
        return None


class ProgressionWidget(QtWidgets.QFrame):
    """Compact widget showing level, XP progress bar, and streak."""

    levelChanged = QtCore.Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = None
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        self.setObjectName("ProgressionWidget")
        self.setStyleSheet("""
            #ProgressionWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e8f5e9, stop:1 #e3f2fd
                );
                border: 2px solid #81c784;
                border-radius: 16px;
            }
        """)

        # Fixed size for the widget
        self.setFixedHeight(48)
        self.setMinimumWidth(340)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        # === Level badge ===
        self.level_badge = QtWidgets.QLabel("A1")
        self.level_badge.setAlignment(QtCore.Qt.AlignCenter)
        self.level_badge.setFixedSize(32, 32)
        self.level_badge.setStyleSheet("""
            QLabel {
                background: #4caf50;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 16px;
            }
        """)
        layout.addWidget(self.level_badge, 0, QtCore.Qt.AlignVCenter)

        # === Progress info (vertical: title + progress bar + xp text) ===
        info_widget = QtWidgets.QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_widget.setFixedSize(90, 36)
        info_layout = QtWidgets.QVBoxLayout(info_widget)
        info_layout.setSpacing(1)
        info_layout.setContentsMargins(0, 2, 0, 2)

        self.level_title = QtWidgets.QLabel("Beginner")
        self.level_title.setStyleSheet("font-weight: 600; font-size: 10px; color: #2e7d32; background: transparent;")
        self.level_title.setFixedHeight(12)
        info_layout.addWidget(self.level_title)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedSize(85, 5)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #c8e6c9;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: #43a047;
                border-radius: 2px;
            }
        """)
        info_layout.addWidget(self.progress_bar)

        self.xp_label = QtWidgets.QLabel("0 / 1,000 XP")
        self.xp_label.setStyleSheet("font-size: 8px; color: #558b2f; background: transparent;")
        self.xp_label.setFixedHeight(10)
        info_layout.addWidget(self.xp_label)

        layout.addWidget(info_widget, 0, QtCore.Qt.AlignVCenter)

        # === Separator ===
        sep1 = QtWidgets.QFrame()
        sep1.setFixedSize(1, 28)
        sep1.setStyleSheet("background: #b5e48c;")
        layout.addWidget(sep1, 0, QtCore.Qt.AlignVCenter)

        # === Streak badge ===
        self.streak_badge = QtWidgets.QLabel("🔥 0")
        self.streak_badge.setFixedSize(44, 26)
        self.streak_badge.setAlignment(QtCore.Qt.AlignCenter)
        self.streak_badge.setStyleSheet("""
            QLabel {
                background: #fff3e0;
                color: #e65100;
                font-size: 10px;
                font-weight: bold;
                border-radius: 6px;
                border: 1px solid #ffcc80;
            }
        """)
        self.streak_badge.setToolTip("Current streak (consecutive days)")
        layout.addWidget(self.streak_badge, 0, QtCore.Qt.AlignVCenter)

        # === Today's XP ===
        self.today_xp = QtWidgets.QLabel("⚡ 0")
        self.today_xp.setFixedSize(44, 26)
        self.today_xp.setAlignment(QtCore.Qt.AlignCenter)
        self.today_xp.setStyleSheet("""
            QLabel {
                background: #e3f2fd;
                color: #1565c0;
                font-size: 10px;
                font-weight: bold;
                border-radius: 6px;
                border: 1px solid #90caf9;
            }
        """)
        self.today_xp.setToolTip("XP earned today")
        layout.addWidget(self.today_xp, 0, QtCore.Qt.AlignVCenter)

        # === Separator ===
        sep2 = QtWidgets.QFrame()
        sep2.setFixedSize(1, 28)
        sep2.setStyleSheet("background: #b5e48c;")
        layout.addWidget(sep2, 0, QtCore.Qt.AlignVCenter)

        # === Details button ===
        self.details_btn = QtWidgets.QPushButton("📊")
        self.details_btn.setFixedSize(26, 26)
        self.details_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.details_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #81c784;
                border-radius: 13px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #c8e6c9;
            }
        """)
        self.details_btn.setToolTip("View detailed progress")
        self.details_btn.clicked.connect(self._show_details_dialog)
        layout.addWidget(self.details_btn, 0, QtCore.Qt.AlignVCenter)

    def refresh(self):
        """Refresh progress data from service."""
        try:
            service = get_progression_service()
            if service:
                self._progress = service.get_progress()
                self._update_display()
        except Exception as e:
            print(f"[ProgressionWidget] Error refreshing: {e}")

    def _update_display(self):
        """Update UI with current progress data."""
        if not self._progress:
            return

        p = self._progress

        # Find level info
        level_info = None
        for lt in LEVEL_THRESHOLDS:
            if lt.level == p.current_level:
                level_info = lt
                break

        if level_info:
            self.level_badge.setText(p.current_level)
            self.level_badge.setStyleSheet(f"""
                QLabel {{
                    background: {level_info.color};
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 16px;
                }}
            """)
            self.level_title.setText(level_info.title)

        # XP display
        next_level_xp = level_info.max_xp if level_info else 1000
        if next_level_xp > 100000:
            self.xp_label.setText(f"{p.total_xp:,} XP")
        else:
            self.xp_label.setText(f"{p.total_xp:,} / {next_level_xp:,}")

        # Progress bar
        self.progress_bar.setValue(int(p.progress_percent))

        # Streak
        self.streak_badge.setText(f"🔥 {p.current_streak}")
        if p.current_streak >= 7:
            self.streak_badge.setStyleSheet("""
                QLabel {
                    background: #ffeb3b;
                    color: #f57f17;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 6px;
                    border: 1px solid #ffc107;
                }
            """)

        # Today's XP
        self.today_xp.setText(f"⚡ {p.xp_earned_today}")

    def _show_details_dialog(self):
        """Show detailed progress dialog."""
        dlg = ProgressionDetailsDialog(self._progress, self.window())
        dlg.exec()


class ProgressionDetailsDialog(QtWidgets.QDialog):
    """Detailed view of user's progression."""

    def __init__(self, progress, parent=None):
        super().__init__(parent)
        self._progress = progress
        self.setWindowTitle("Your Progress")
        self.resize(500, 500)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: #ffffff;
            }
            QLabel {
                color: #184e77;
                background: transparent;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #b5e48c;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 12px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)

        if not self._progress:
            layout.addWidget(QtWidgets.QLabel("No progress data available. Start practicing to earn XP!"))
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn)
            return

        p = self._progress

        # Level Card
        level_card = self._create_level_card(p)
        layout.addWidget(level_card)

        # Stats Grid
        stats_group = QtWidgets.QGroupBox("Activity Statistics")
        stats_layout = QtWidgets.QGridLayout(stats_group)

        stats = [
            ("💬 Messages Sent", p.total_messages),
            ("📚 Words Learned", p.total_words_learned),
            ("🎧 Listening Quizzes", p.total_listening_quizzes),
            ("📖 Articles Read", p.total_reading_articles),
            ("✏️ Grammar Corrections", p.total_grammar_corrections),
            ("⚡ XP Today", p.xp_earned_today),
        ]

        for i, (label, value) in enumerate(stats):
            row, col = i // 2, i % 2
            stat_widget = self._create_stat_item(label, str(value))
            stats_layout.addWidget(stat_widget, row, col)

        layout.addWidget(stats_group)

        # Streak Info
        streak_group = QtWidgets.QGroupBox("Streaks")
        streak_layout = QtWidgets.QHBoxLayout(streak_group)
        streak_layout.addWidget(self._create_stat_item("🔥 Current Streak", f"{p.current_streak} days"))
        streak_layout.addWidget(self._create_stat_item("🏆 Longest Streak", f"{p.longest_streak} days"))
        layout.addWidget(streak_group)

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _create_level_card(self, p) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e8f5e9, stop:1 #c8e6c9
                );
                border-radius: 16px;
                padding: 16px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(card)

        level_row = QtWidgets.QHBoxLayout()

        badge = QtWidgets.QLabel(p.current_level)
        badge.setFixedSize(64, 64)
        badge.setAlignment(QtCore.Qt.AlignCenter)
        badge.setStyleSheet("""
            QLabel {
                background: #43a047;
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 32px;
            }
        """)
        level_row.addWidget(badge)

        info = QtWidgets.QVBoxLayout()

        for lt in LEVEL_THRESHOLDS:
            if lt.level == p.current_level:
                title = QtWidgets.QLabel(lt.title)
                title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2e7d32; background: transparent;")
                info.addWidget(title)
                break

        xp_label = QtWidgets.QLabel(f"{p.total_xp:,} XP Total")
        xp_label.setStyleSheet("font-size: 14px; color: #558b2f; background: transparent;")
        info.addWidget(xp_label)

        level_row.addLayout(info)
        level_row.addStretch()

        layout.addLayout(level_row)

        if p.xp_to_next_level > 0:
            progress_label = QtWidgets.QLabel(
                f"{p.xp_to_next_level:,} XP to next level ({p.progress_percent:.0f}%)"
            )
            progress_label.setStyleSheet("font-size: 12px; color: #388e3c; background: transparent;")
            layout.addWidget(progress_label)

            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(int(p.progress_percent))
            progress_bar.setFixedHeight(8)
            progress_bar.setTextVisible(False)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    background: #a5d6a7;
                    border: none;
                    border-radius: 4px;
                }
                QProgressBar::chunk {
                    background: #2e7d32;
                    border-radius: 4px;
                }
            """)
            layout.addWidget(progress_bar)

        return card

    def _create_stat_item(self, label: str, value: str) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #f5f5f5;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        label_widget = QtWidgets.QLabel(label)
        label_widget.setStyleSheet("font-size: 11px; color: #666; background: transparent;")

        value_widget = QtWidgets.QLabel(value)
        value_widget.setStyleSheet("font-size: 16px; font-weight: bold; color: #184e77; background: transparent;")

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return frame


class XPGainPopup(QtWidgets.QFrame):
    """Small popup that appears when XP is gained."""

    def __init__(self, xp_amount: int, description: str = "", parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        self._setup_ui(xp_amount, description)
        self._setup_animation()

    def _setup_ui(self, xp_amount: int, description: str):
        self.setFixedSize(150, 40)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        inner = QtWidgets.QFrame(self)
        inner.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4caf50, stop:1 #66bb6a
                );
                border-radius: 10px;
            }
        """)
        inner_layout = QtWidgets.QVBoxLayout(inner)
        inner_layout.setContentsMargins(8, 4, 8, 4)
        inner_layout.setSpacing(0)

        xp_label = QtWidgets.QLabel(f"+{xp_amount} XP")
        xp_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        xp_label.setAlignment(QtCore.Qt.AlignCenter)
        inner_layout.addWidget(xp_label)

        if description:
            desc_label = QtWidgets.QLabel(description[:20])
            desc_label.setStyleSheet("font-size: 8px; color: #e8f5e9; background: transparent;")
            desc_label.setAlignment(QtCore.Qt.AlignCenter)
            inner_layout.addWidget(desc_label)

        layout.addWidget(inner)

    def _setup_animation(self):
        self._opacity = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)

        self._anim = QtCore.QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(2500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QtCore.QEasingCurve.InQuad)
        self._anim.finished.connect(self.deleteLater)

    def show_at(self, global_pos: QtCore.QPoint):
        self.move(global_pos)
        self.show()
        self._anim.start()