from datetime import datetime, timedelta
from unittest.mock import patch

from models import Task, TaskPriority
from task_priority import calculate_task_score


def test_recency_bonus_uses_elapsed_days_boundary():
    fixed_now = datetime(2026, 9, 8, 12, 0, 0)

    recent_task = Task("Recently updated", priority=TaskPriority.LOW)
    recent_task.updated_at = fixed_now - timedelta(hours=23)

    old_task = Task("Updated yesterday", priority=TaskPriority.LOW)
    old_task.updated_at = fixed_now - timedelta(days=1)

    with patch("task_priority.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_now

        recent_score = calculate_task_score(recent_task)
        old_score = calculate_task_score(old_task)

    assert recent_score == 15
    assert old_score == 10