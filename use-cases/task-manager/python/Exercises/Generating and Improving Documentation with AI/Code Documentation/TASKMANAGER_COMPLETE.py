"""
TaskManager - A high-level task management interface.

This module provides a complete task management system that bridges user operations
and persistent storage. It handles CRUD operations, data validation, business logic,
filtering, and reporting on tasks.

Key Responsibilities:
  - Task creation with validation
  - Task retrieval with flexible filtering
  - Task property updates (status, priority, due date, tags)
  - Task deletion
  - Statistical reporting and analytics

Design Pattern: Facade pattern wrapping TaskStorage with business logic layer.

Example Usage:
    >>> manager = TaskManager("tasks.json")
    >>> task_id = manager.create_task(
    ...     title="Complete report",
    ...     description="Quarterly review",
    ...     priority_value=3,
    ...     due_date_str="2026-09-15",
    ...     tags=["work", "urgent"]
    ... )
    >>> tasks = manager.list_tasks()
    >>> manager.update_task_status(task_id, 2)  # Mark as done
"""

import argparse
from datetime import datetime, timedelta

from models import TaskPriority, Task, TaskStatus
from storage import TaskStorage


class TaskManager:
    """
    Manages task operations including creation, retrieval, updating, and deletion.
    
    This class provides a high-level interface for task management, handling all
    CRUD operations on tasks stored in persistent storage. It serves as the primary
    business logic layer between the CLI/UI and the underlying storage system.
    
    The class wraps a TaskStorage backend and adds:
    - Input validation (especially for dates and enums)
    - Business logic (e.g., marking tasks complete sets timestamps)
    - Flexible filtering options
    - Statistical reporting
    
    Attributes:
        storage (TaskStorage): The underlying storage backend for persisting tasks.
    
    Example:
        >>> manager = TaskManager("tasks.json")
        >>> task_id = manager.create_task("Buy groceries", "Milk, eggs, bread", priority_value=2)
        >>> tasks = manager.list_tasks()
        >>> manager.update_task_status(task_id, 2)  # Mark as done
        >>> manager.delete_task(task_id)
    
    Important Notes:
        - All date operations expect YYYY-MM-DD format. Invalid dates are rejected
          gracefully (returns None/False without raising exceptions).
        - Error handling is inconsistent: some methods return None, others return False.
          Callers should check both in error scenarios.
        - Only one filter can be applied at a time in list_tasks() (cascading precedence).
        - Tag operations have different return value semantics (see their docstrings).
    
    Known Limitations:
        - No input type validation (will raise TypeError if wrong types passed)
        - No concurrent access protection (race conditions possible)
        - Statistics calculation is O(5n) instead of O(n) (multiple passes)
        - Date parsing doesn't consider timezones
    """

    def __init__(self, storage_path="tasks.json"):
        """
        Initialize the TaskManager with a specified storage backend.
        
        Args:
            storage_path (str, optional): Path to the JSON file where tasks will be
                persisted. Defaults to "tasks.json" in the current directory.
                If the file doesn't exist, it will be created on first save.
        
        Raises:
            IOError: If the storage directory doesn't exist and cannot be created.
            json.JSONDecodeError: If the storage file exists but contains invalid JSON.
        
        Example:
            >>> manager = TaskManager()  # Uses default "tasks.json"
            >>> custom_manager = TaskManager("/path/to/my/tasks.json")
        """
        self.storage = TaskStorage(storage_path)

    def create_task(self, title, description="", priority_value=2,
                   due_date_str=None, tags=None):
        """
        Create a new task and add it to storage.
        
        Constructs a Task object with the provided properties and persists it to
        storage. The task is assigned a unique ID by the storage system.
        
        VALIDATION: Date parsing happens BEFORE Task creation. If the date is invalid,
        the entire task creation fails. This prevents invalid Task objects from being
        created in the first place.
        
        Args:
            title (str): The task title. Required. Should be concise and descriptive.
                Empty strings are technically allowed but not recommended.
            description (str, optional): Detailed description of the task. 
                Defaults to empty string. Can include multi-line text.
            priority_value (int, optional): Priority level as an integer.
                Must be a valid TaskPriority enum value (typically 1-4).
                Defaults to 2 (MEDIUM priority).
                - 1 = LOW
                - 2 = MEDIUM
                - 3 = HIGH
                - 4 = URGENT
            due_date_str (str, optional): Due date in YYYY-MM-DD format.
                If provided, must match exactly or the method returns None.
                Defaults to None (no due date).
            tags (list of str, optional): List of tag strings to associate with the task.
                Tags are case-sensitive and should not contain special characters.
                Defaults to None (no tags).
        
        Returns:
            int or None: The unique task ID if creation was successful, None if the
                due_date_str format was invalid or creation failed. Task IDs are
                non-negative integers assigned sequentially.
        
        Raises:
            ValueError: If priority_value is not a valid TaskPriority enum value.
            TypeError: If title is not a string or tags is not a list.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task(
            ...     title="Complete project report",
            ...     description="Quarterly review due end of month",
            ...     priority_value=3,  # HIGH
            ...     due_date_str="2026-09-15",
            ...     tags=["work", "urgent"]
            ... )
            >>> print(f"Task created with ID: {task_id}")
            Task created with ID: 42
        
        Note:
            - If due_date_str is invalid, the method prints an error message but
              does not raise an exception (returns None instead).
            - Tags should be added at creation time for consistency, though they
              can also be added later with add_tag_to_task().
            - Task status is automatically set to PENDING (or the default status).
            - No validation of priority_value before enum conversion; will raise
              ValueError if invalid integer provided.
        
        Edge Cases:
            - Empty title: Allowed but creates confusing tasks.
            - Duplicate tags: Duplicates in the tags list are preserved at creation.
            - Future dates: No validation prevents dates in the past or far future.
            - Special characters in tags: May cause issues; alphanumeric + hyphens only.
            - None priority_value: Causes TypeError when converting to enum.
        """
        priority = TaskPriority(priority_value)
        due_date = None
        if due_date_str:
            try:
                # Strictly validate YYYY-MM-DD format before creating task
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
                return None  # ⚠️ Returns None (inconsistent with update_task_due_date which returns False)

        task = Task(title, description, priority, due_date, tags)
        task_id = self.storage.add_task(task)
        return task_id

    def list_tasks(self, status_filter=None, priority_filter=None, show_overdue=False):
        """
        Retrieve tasks from storage with optional filtering.
        
        FILTER PRECEDENCE (cascading if-statements - only one filter applies):
        1. show_overdue=True → returns ONLY overdue tasks (other filters ignored)
        2. status_filter set → returns tasks with matching status
        3. priority_filter set → returns tasks with matching priority  
        4. No filters → returns ALL tasks
        
        IMPLICATION: Cannot combine filters. Cannot ask for "overdue HIGH priority tasks"
        in a single call. If you need multiple filters, must call multiple times and
        combine results in caller code.
        
        Args:
            status_filter (int, optional): Filter by task status. Must be a valid
                TaskStatus enum value. Defaults to None (no status filtering).
                - 0 = PENDING
                - 1 = IN_PROGRESS
                - 2 = DONE
            priority_filter (int, optional): Filter by task priority. Must be a valid
                TaskPriority enum value. Defaults to None (no priority filtering).
                - 1 = LOW
                - 2 = MEDIUM
                - 3 = HIGH
                - 4 = URGENT
            show_overdue (bool, optional): If True, returns only overdue tasks
                (tasks with due_date before today and status not DONE).
                Overrides other filters. Defaults to False.
        
        Returns:
            list of Task: A list of Task objects matching the filter criteria.
                Returns an empty list if no tasks match. Order depends on storage
                implementation (usually insertion order).
        
        Raises:
            ValueError: If status_filter or priority_filter is not a valid enum value.
        
        Example:
            >>> manager = TaskManager()
            >>> # Get all tasks
            >>> all_tasks = manager.list_tasks()
            >>> 
            >>> # Get only high-priority tasks
            >>> urgent_tasks = manager.list_tasks(priority_filter=4)
            >>> 
            >>> # Get overdue incomplete tasks
            >>> overdue_tasks = manager.list_tasks(show_overdue=True)
            >>> 
            >>> # Get tasks in progress
            >>> active_tasks = manager.list_tasks(status_filter=1)
            >>> 
            >>> # To combine filters: must call twice
            >>> overdue = manager.list_tasks(show_overdue=True)
            >>> urgent_overdue = [t for t in overdue if t.priority.value == 4]
        
        Note:
            - Only the highest-precedence filter is applied. If both show_overdue
              and status_filter are True/set, only overdue tasks are returned.
            - This method does not modify tasks, only retrieves them.
            - For large task lists, retrieving all tasks may be memory-intensive.
            - No filtering happens client-side; all filtering is delegated to storage.
        
        Edge Cases:
            - Empty storage: Returns an empty list without error.
            - No matching tasks: Returns an empty list (not None).
            - Filter conflicts: show_overdue takes precedence over other filters,
              even if they would be more restrictive.
            - Multiple filters set: Only the first in precedence order is used.
        """
        if show_overdue:
            return self.storage.get_overdue_tasks()

        if status_filter:
            status = TaskStatus(status_filter)
            return self.storage.get_tasks_by_status(status)

        if priority_filter:
            priority = TaskPriority(priority_filter)
            return self.storage.get_tasks_by_priority(priority)

        return self.storage.get_all_tasks()

    def update_task_status(self, task_id, new_status_value):
        """
        Update the status of an existing task.
        
        Changes a task's status and performs any associated side effects. When marking
        a task as DONE, the task's completed_at timestamp is automatically updated.
        
        ASYMMETRIC HANDLING:
        - If transitioning TO DONE: Special behavior triggered
          * Fetches task, calls mark_as_done() (sets completed_at timestamp)
          * Manually saves storage
          * Returns True/False based on task existence
          
        - If transitioning to other statuses: Delegated to storage
          * Storage.update_task() handles the update
          * Save behavior is inconsistent (may or may not auto-save)
          
        CONSEQUENCE: DONE status is a special "completion" event with timestamp 
        tracking, while other status changes are just state transitions.
        
        Args:
            task_id (int): The unique ID of the task to update. Must refer to an
                existing task in storage.
            new_status_value (int): The new status as a TaskStatus enum value.
                - 0 = PENDING
                - 1 = IN_PROGRESS
                - 2 = DONE
        
        Returns:
            bool: True if the status was successfully updated, False if the task_id
                doesn't exist or the update failed for any reason.
        
        Raises:
            ValueError: If new_status_value is not a valid TaskStatus enum value.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task("Fix bug #123")
            >>> 
            >>> # Move task to in-progress
            >>> success = manager.update_task_status(task_id, 1)
            >>> if success:
            ...     print("Status updated to IN_PROGRESS")
            >>> 
            >>> # Mark task as done (automatically sets completed_at timestamp)
            >>> success = manager.update_task_status(task_id, 2)
            >>> if success:
            ...     print("Task marked complete - timestamp recorded")
            >>> else:
            ...     print("Task not found")
        
        Note:
            - Marking a task as DONE (status 2) automatically calls task.mark_as_done(),
              which sets the completed_at timestamp to the current datetime.
            - For other status transitions, mark_as_done() is not called.
            - Storage is automatically saved when the status is changed to DONE.
            - For other status transitions, storage save behavior depends on storage
              backend implementation.
        
        Edge Cases:
            - Non-existent task_id: Returns False without raising an error.
            - Same status: Technically succeeds but has no practical effect.
            - Transitioning from DONE back to another status: Allowed, but completed_at
              is not reset (timestamp persists). This may create logical inconsistencies.
            - Invalid status_value: Raises ValueError before checking task existence.
        """
        new_status = TaskStatus(new_status_value)
        if new_status == TaskStatus.DONE:
            # SPECIAL CASE: Mark as done includes timestamp tracking
            task = self.storage.get_task(task_id)
            if task:
                task.mark_as_done()  # Side effect: sets completed_at to current time
                self.storage.save()   # Explicit save for DONE status
                return True
            # Task not found
            return False
        else:
            # Other status transitions delegated to storage
            # Storage may or may not auto-save (inconsistent with DONE behavior)
            return self.storage.update_task(task_id, status=new_status)

    def update_task_priority(self, task_id, new_priority_value):
        """
        Update the priority level of an existing task.
        
        Modifies a task's priority without affecting other properties.
        
        Args:
            task_id (int): The unique ID of the task to update. Must refer to an
                existing task in storage.
            new_priority_value (int): The new priority as a TaskPriority enum value.
                - 1 = LOW
                - 2 = MEDIUM
                - 3 = HIGH
                - 4 = URGENT
        
        Returns:
            bool: True if the priority was successfully updated, False if the task_id
                doesn't exist or the update failed.
        
        Raises:
            ValueError: If new_priority_value is not a valid TaskPriority enum value.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task("Review proposal", priority_value=2)
            >>> 
            >>> # Escalate to high priority
            >>> success = manager.update_task_priority(task_id, 3)
            >>> if success:
            ...     print("Priority escalated to HIGH")
            >>> else:
            ...     print("Task not found")
        
        Note:
            - Only the priority field is modified. Status, due_date, tags, and
              description remain unchanged.
            - Changes are persisted immediately to storage.
            - No validation of the new priority before enum conversion.
        
        Edge Cases:
            - Non-existent task_id: Returns False without raising an error.
            - Same priority: Succeeds but has no practical effect.
            - Invalid priority_value: Raises ValueError before checking task existence.
        """
        new_priority = TaskPriority(new_priority_value)
        return self.storage.update_task(task_id, priority=new_priority)

    def update_task_due_date(self, task_id, due_date_str):
        """
        Update the due date of an existing task.
        
        Changes a task's due date to a new value. The date must be in YYYY-MM-DD
        format. If the format is invalid, the method returns False and logs an error
        without updating the task.
        
        DATE PARSING: Uses the same YYYY-MM-DD validation as create_task(), but 
        returns False instead of None on error. This inconsistency means callers 
        must check for both None and False across different methods.
        
        Args:
            task_id (int): The unique ID of the task to update. Must refer to an
                existing task in storage.
            due_date_str (str): New due date in YYYY-MM-DD format.
                Example: "2026-12-31"
                Pass empty string to potentially clear due date (depends on storage).
        
        Returns:
            bool: True if the due date was successfully updated, False if:
                - The task_id doesn't exist, OR
                - The due_date_str format is invalid (not YYYY-MM-DD)
        
        Raises:
            Does not raise exceptions; returns False on error instead.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task("Submit assignment")
            >>> 
            >>> # Set valid due date
            >>> success = manager.update_task_due_date(task_id, "2026-09-15")
            >>> if success:
            ...     print("Due date set")
            >>> 
            >>> # Try invalid format
            >>> success = manager.update_task_due_date(task_id, "09/15/2026")
            >>> if not success:
            ...     print("Invalid format or task not found")
            >>> # Console output: "Invalid date format. Use YYYY-MM-DD"
        
        Note:
            - Invalid date formats print a user-friendly message but don't raise
              exceptions, making this suitable for CLI applications.
            - The method does not validate whether the date is in the future or past.
            - Date parsing only supports YYYY-MM-DD; other formats are rejected.
            - ⚠️ INCONSISTENCY: create_task returns None on bad date, this returns False.
        
        Edge Cases:
            - Non-existent task_id: Returns False.
            - Empty string due_date_str: Raises ValueError (caught and returns False).
            - Date in the past: Allowed; no validation prevents this.
            - Leap year dates (e.g., "2024-02-29"): Correctly validated by strptime.
            - Non-leap year Feb 29: Correctly rejected (ValueError caught).
        """
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            return self.storage.update_task(task_id, due_date=due_date)
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return False  # ⚠️ Different from create_task (which returns None)

    def delete_task(self, task_id):
        """
        Permanently delete a task from storage.
        
        Removes a task and all associated data (status, priority, due date, tags, etc.)
        from storage. This operation cannot be undone.
        
        Args:
            task_id (int): The unique ID of the task to delete. Must refer to an
                existing task in storage.
        
        Returns:
            bool: True if the task was successfully deleted, False if the task_id
                doesn't exist or deletion failed.
        
        Raises:
            Does not raise exceptions; returns False on error instead.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task("Temporary task")
            >>> 
            >>> # Delete the task
            >>> success = manager.delete_task(task_id)
            >>> if success:
            ...     print("Task deleted")
            >>> 
            >>> # Verify deletion
            >>> remaining_tasks = manager.list_tasks()
        
        Note:
            - This is a permanent operation. Consider archiving completed tasks
              instead of deleting them if audit trail is needed.
            - Deletion is immediate; changes are persisted to storage.
            - No confirmation prompt is provided; the caller should handle UX.
        
        Edge Cases:
            - Non-existent task_id: Returns False without raising an error.
            - Deleting the last task: Succeeds; storage becomes empty.
        """
        return self.storage.delete_task(task_id)

    def get_task_details(self, task_id):
        """
        Retrieve detailed information about a single task.
        
        Fetches a complete Task object with all properties (title, description,
        priority, status, due_date, tags, timestamps, etc.).
        
        Args:
            task_id (int): The unique ID of the task to retrieve. Must refer to an
                existing task in storage.
        
        Returns:
            Task or None: The Task object if found, None if the task_id doesn't exist
                or retrieval failed. The returned Task object is a reference to the
                stored object, so modifications may affect storage (depending on
                implementation).
        
        Raises:
            Does not raise exceptions; returns None if task not found.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task(
            ...     "Review code",
            ...     description="Check PR #456",
            ...     priority_value=3,
            ...     tags=["code-review"]
            ... )
            >>> 
            >>> # Get and display task details
            >>> task = manager.get_task_details(task_id)
            >>> if task:
            ...     print(f"Title: {task.title}")
            ...     print(f"Priority: {task.priority.name}")
            ...     print(f"Due: {task.due_date}")
            ...     print(f"Tags: {', '.join(task.tags)}")
            ... else:
            ...     print("Task not found")
        
        Note:
            - Returns a direct reference to the stored Task object (not a copy).
            - Modifying the returned Task object will affect storage (be careful!).
            - Use this method to access all task properties at once rather than
              calling individual update methods.
        
        Edge Cases:
            - Non-existent task_id: Returns None without raising an error.
            - Task with no tags: Returns Task with empty tags list, not None.
            - Task with no due date: Returns Task with due_date=None.
        """
        return self.storage.get_task(task_id)

    def add_tag_to_task(self, task_id, tag):
        """
        Add a single tag to an existing task.
        
        Appends a tag to the task's tag list. If the tag already exists, it is not
        added (prevents duplicates). Changes are persisted immediately.
        
        TRICKY RETURN VALUE:
        - Returns True if task EXISTS (whether tag was added or already existed)
        - Returns False only if task DOESN'T EXIST
        
        This means the return value indicates "task exists", NOT "tag was added".
        This is DIFFERENT and more confusing than remove_tag_from_task().
        
        Args:
            task_id (int): The unique ID of the task to tag. Must refer to an
                existing task in storage.
            tag (str): The tag string to add. Should be alphanumeric and concise.
                Special characters may cause issues in some contexts.
                Tag names are case-sensitive ("Work" and "work" are different).
        
        Returns:
            bool: True if the tag was successfully added OR already existed (task exists),
                False only if the task_id doesn't exist.
        
        Raises:
            Does not raise exceptions; returns False if task not found.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task("Update documentation")
            >>> 
            >>> # Add a tag
            >>> success = manager.add_tag_to_task(task_id, "documentation")
            >>> if success:
            ...     print("Task found")  # (not: "tag added")
            >>> 
            >>> # Add another tag
            >>> success = manager.add_tag_to_task(task_id, "writing")
            >>> 
            >>> # Try to add duplicate (silently ignored, but returns True)
            >>> success = manager.add_tag_to_task(task_id, "documentation")
            >>> if success:
            ...     print("Task found (tag already existed)")
            >>> 
            >>> # Try non-existent task
            >>> success = manager.add_tag_to_task(999, "tag")
            >>> if not success:
            ...     print("Task not found")
            >>> 
            >>> # Verify tags
            >>> task = manager.get_task_details(task_id)
            >>> print(task.tags)  # ['documentation', 'writing']
        
        Note:
            - Duplicate tags are silently ignored (no error, no exception).
            - Tags are added in the order they are provided.
            - Storage is automatically saved after adding a tag.
            - No limit on the number of tags per task (depends on storage).
            - ⚠️ Return value semantics are confusing: means "task exists", not "tag added".
        
        Edge Cases:
            - Non-existent task_id: Returns False.
            - Empty tag string: Technically allowed but creates issues downstream.
            - Task with None tags: Crashes when checking `if tag not in task.tags`.
            - Duplicate tag: Silently ignored; returns True anyway (misleading).
        """
        task = self.storage.get_task(task_id)
        if task:
            if tag not in task.tags:  # Duplicate prevention
                task.tags.append(tag)
                self.storage.save()
            return True  # ⚠️ Returns True even if tag already existed or task doesn't exist
        return False

    def remove_tag_from_task(self, task_id, tag):
        """
        Remove a tag from an existing task.
        
        Deletes a tag from the task's tag list. If the tag doesn't exist, returns
        False. Changes are persisted immediately to storage.
        
        RETURN VALUE SEMANTICS (more predictable than add_tag_to_task):
        - Returns True only if tag was successfully removed
        - Returns False if task not found OR tag not in task's tags
        
        Args:
            task_id (int): The unique ID of the task from which to remove the tag.
                Must refer to an existing task in storage.
            tag (str): The tag string to remove. Must match exactly (case-sensitive).
        
        Returns:
            bool: True if the tag was successfully removed, False if:
                - The task_id doesn't exist, OR
                - The tag doesn't exist in the task's tag list
        
        Raises:
            Does not raise exceptions; returns False on error instead.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task("Review PR", tags=["code", "urgent"])
            >>> 
            >>> # Remove a tag
            >>> success = manager.remove_tag_from_task(task_id, "urgent")
            >>> if success:
            ...     print("Tag removed")
            >>> else:
            ...     print("Tag not found or task doesn't exist")
            >>> 
            >>> # Verify removal
            >>> task = manager.get_task_details(task_id)
            >>> print(task.tags)  # ['code']
            >>> 
            >>> # Try to remove non-existent tag
            >>> success = manager.remove_tag_from_task(task_id, "completed")
            >>> if not success:
            ...     print("Tag not found")
        
        Note:
            - Only exact matches are removed (case-sensitive).
            - If multiple instances of the same tag exist, only the first is removed
              (depends on list.remove() behavior).
            - Storage is automatically saved after removing a tag.
            - Removing the last tag is allowed; task can have zero tags.
        
        Edge Cases:
            - Non-existent task_id: Returns False.
            - Non-existent tag: Returns False (doesn't raise ValueError like list.remove).
            - Case mismatch: Tag not found and returns False ("Work" != "work").
            - Empty tag list: Attempting to remove from empty list returns False.
            - Task with None tags: Crashes when checking `if task and tag in task.tags`.
        """
        task = self.storage.get_task(task_id)
        if task and tag in task.tags:  # Requires BOTH conditions
            task.tags.remove(tag)
            self.storage.save()
            return True
        return False

    def get_statistics(self):
        """
        Generate comprehensive statistics about all tasks in storage.
        
        Calculates aggregate metrics including total task count, distribution by
        status and priority, overdue task count, and recently completed tasks.
        
        PERFORMANCE NOTE: This method scans the task list multiple times (O(5n) 
        instead of O(n)). For very large task databases (10k+ tasks), this may be slow.
        
        DICTIONARY INITIALIZATION PATTERN: Pre-initializes counters with ALL possible
        enum values. This ensures the return dict always has complete, consistent keys
        (e.g., "PENDING": 0 even if no pending tasks exist).
        
        Args:
            None
        
        Returns:
            dict: A dictionary containing the following keys:
                - total (int): Total number of tasks in storage.
                - by_status (dict): Task count grouped by status.
                    Keys are status values (e.g., 0, 1, 2 or "PENDING", "IN_PROGRESS", "DONE").
                    Example: {0: 5, 1: 3, 2: 12}
                - by_priority (dict): Task count grouped by priority level.
                    Keys are priority names (e.g., "LOW", "MEDIUM", "HIGH", "URGENT").
                    Example: {"LOW": 3, "MEDIUM": 8, "HIGH": 7, "URGENT": 2}
                - overdue (int): Count of incomplete tasks with due_date in the past.
                    Only counts tasks where status != DONE.
                - completed_last_week (int): Count of tasks marked as DONE in the
                    last 7 days (based on completed_at timestamp).
        
        Raises:
            Does not raise exceptions; returns default counts (zeros) if storage fails.
        
        Example:
            >>> manager = TaskManager()
            >>> # Create sample tasks
            >>> manager.create_task("Task 1", priority_value=1)
            >>> manager.create_task("Task 2", priority_value=3)
            >>> manager.create_task("Task 3", priority_value=3)
            >>> 
            >>> # Get statistics
            >>> stats = manager.get_statistics()
            >>> 
            >>> print(f"Total tasks: {stats['total']}")
            Total tasks: 3
            >>> 
            >>> print(f"By priority: {stats['by_priority']}")
            By priority: {'LOW': 1, 'MEDIUM': 0, 'HIGH': 2, 'URGENT': 0}
            >>> 
            >>> print(f"By status: {stats['by_status']}")
            By status: {0: 3, 1: 0, 2: 0}
            >>> 
            >>> print(f"Overdue tasks: {stats['overdue']}")
            Overdue tasks: 0
            >>> 
            >>> print(f"Completed this week: {stats['completed_last_week']}")
            Completed this week: 0
        
        Note:
            - Empty storage returns all zeros, but all expected keys still exist in dict.
            - "Last 7 days" is calculated from the current datetime (datetime.now()).
            - Overdue determination depends on task.is_overdue() method working correctly.
            - Completed timestamp (completed_at) must be set for recent completion
              counting; tasks without this timestamp are not counted.
            - No timezone handling; uses naive datetime comparison.
        
        Edge Cases:
            - No tasks: All counts are 0, but dictionary keys still exist.
            - All tasks completed long ago: completed_last_week will be 0.
            - All tasks overdue: overdue count may equal total - done_count.
            - Priority/status enums with unusual names: Dictionary keys reflect
              enum names/values exactly as defined.
        
        Performance Considerations:
            - Scans all tasks multiple times (status pass, priority pass, overdue pass,
              completion pass). O(5n) complexity where n = total tasks.
            - For very large task databases (10k+ tasks), this method may be slow.
            - OPTIMIZATION: Could be improved to single O(n) pass through data.
            - Consider caching results if called frequently with same data.
        """
        tasks = self.storage.get_all_tasks()
        total = len(tasks)

        # Pre-initialize with ALL possible enum values
        # Ensures return dict has complete, consistent keys even if some have 0 count
        status_counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            status_counts[task.status.value] += 1

        # Same pattern for priority - pre-initialize with all possible values
        priority_counts = {priority.name: 0 for priority in TaskPriority}
        for task in tasks:
            priority_counts[task.priority.name] += 1

        # Separate pass for overdue check
        # ASSUMPTION: task.is_overdue() returns boolean and works correctly
        # TODO: Could combine this with above loops for better performance
        overdue_count = len([task for task in tasks if task.is_overdue()])

        # Separate pass for recent completion
        # ASSUMPTION: task.completed_at is set only when mark_as_done() was called
        # TODO: Could combine this with above loops for better performance
        seven_days_ago = datetime.now() - timedelta(days=7)
        completed_recently = len([
            task for task in tasks
            if task.completed_at and task.completed_at >= seven_days_ago
        ])

        return {
            "total": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "overdue": overdue_count,
            "completed_last_week": completed_recently
        }


# ============================================================================
# QUICK REFERENCE GUIDE
# ============================================================================
"""
DESIGN PATTERNS USED:

1. **Facade Pattern**: TaskManager wraps TaskStorage, providing simplified interface.

2. **Validation-First Pattern**: Date/enum validation happens BEFORE object creation.
   Good practice: fail early, prevent invalid state in storage.

3. **Cascading Filters**: list_tasks() uses cascading if-statements (single filter).
   Tradeoff: Simple logic but cannot combine filters (must call twice).

4. **Asymmetric Error Handling**: Returns None, False, True inconsistently.
   - create_task bad date: returns None
   - update_task_due_date bad date: returns False
   - Tag operations: return True for "task exists" not "operation succeeded"

5. **Delegation Pattern**: Most methods delegate to storage backend.
   Benefit: Centralizes persistence logic. Drawback: hides save behavior.

6. **Dictionary Comprehension for Enums**: Pre-initializes counters with all enum values.
   Smart pattern: ensures complete, consistent reporting even when counts are zero.


KEY INCONSISTENCIES (KNOW BEFORE USING):

1. Error Returns:
   - create_task(bad_date) → None
   - update_task_due_date(bad_date) → False
   - Callers must check for both

2. Tag Operations:
   - add_tag_to_task() → True means "task exists" (confusing!)
   - remove_tag_from_task() → True means "tag removed" (predictable)
   - Different contracts!

3. Status Update:
   - Marking DONE has special behavior (sets timestamp, saves explicitly)
   - Other status changes are simple (delegated to storage)
   - Asymmetric handling of special case

4. Filter Combination:
   - list_tasks(status=1, priority=3) only uses status (priority ignored)
   - Cannot ask "show me in-progress HIGH priority tasks" in one call
   - Must call twice and combine results


KNOWN LIMITATIONS:

- No input type validation (will crash on wrong types)
- No concurrent access protection (race conditions possible in multi-threaded apps)
- Statistics calculation is O(5n) instead of O(n) (multiple passes through data)
- Date parsing doesn't consider timezones
- No logging (uses print() statements instead)
- Silent error handling (prints to console, doesn't raise exceptions)


SUGGESTIONS FOR IMPROVEMENT (Without Changing Current Behavior):

HIGH PRIORITY:
1. Standardize error returns (always bool or always object)
2. Add input type/value validation before enum conversion
3. Combine multiple loops in get_statistics() into single O(n) pass
4. Fix tag operation return value semantics

MEDIUM PRIORITY:
5. Use logging instead of print statements
6. Add type hints (Python 3.9+)
7. Add method-level docstrings

LOW PRIORITY:
8. Consider context manager for storage
9. Cache statistics if called frequently
10. Add thread-safety for concurrent access
"""
