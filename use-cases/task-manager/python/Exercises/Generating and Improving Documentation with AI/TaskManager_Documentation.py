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
    
    Attributes:
        storage (TaskStorage): The underlying storage backend for persisting tasks.
    
    Example:
        >>> manager = TaskManager("tasks.json")
        >>> task_id = manager.create_task("Buy groceries", "Milk, eggs, bread", priority_value=2)
        >>> tasks = manager.list_tasks()
        >>> manager.update_task_status(task_id, 2)  # Mark as done
        >>> manager.delete_task(task_id)
    
    Note:
        All date operations expect YYYY-MM-DD format. Invalid dates will log an error
        and return None/False without raising exceptions, allowing graceful degradation
        in CLI applications.
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
        
        Edge Cases:
            - Empty title: Allowed but creates confusing tasks.
            - Duplicate tags: Duplicates in the tags list are preserved at creation.
            - Future dates: No validation prevents dates in the past or far future.
            - Special characters in tags: May cause issues; it's recommended to use
              alphanumeric characters and hyphens only.
        """
        priority = TaskPriority(priority_value)
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
                return None

        task = Task(title, description, priority, due_date, tags)
        task_id = self.storage.add_task(task)
        return task_id

    def list_tasks(self, status_filter=None, priority_filter=None, show_overdue=False):
        """
        Retrieve tasks from storage with optional filtering.
        
        Fetches tasks based on specified filters. Only one filter is applied at a
        time (in order of precedence: show_overdue, status_filter, priority_filter).
        If no filters are specified, all tasks are returned.
        
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
        
        Note:
            - Only the highest-precedence filter is applied. If both show_overdue
              and status_filter are True/set, only overdue tasks are returned.
            - This method does not modify tasks, only retrieves them.
            - For large task lists, retrieving all tasks may be memory-intensive.
        
        Edge Cases:
            - Empty storage: Returns an empty list without error.
            - No matching tasks: Returns an empty list (not None).
            - Filter conflicts: show_overdue takes precedence over other filters,
              even if they would be more restrictive.
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
            >>> 
            >>> # Mark task as done (automatically sets completed_at timestamp)
            >>> success = manager.update_task_status(task_id, 2)
            >>> 
            >>> # Check if update succeeded
            >>> if success:
            ...     print("Task status updated")
            ... else:
            ...     print("Task not found")
        
        Note:
            - Marking a task as DONE (status 2) automatically calls task.mark_as_done(),
              which sets the completed_at timestamp to the current datetime.
            - For other status transitions, mark_as_done() is not called.
            - Storage is automatically saved when the status is changed.
        
        Edge Cases:
            - Non-existent task_id: Returns False without raising an error.
            - Same status: Technically succeeds but has no effect.
            - Transitioning from DONE back to another status: Allowed, but completed_at
              is not reset (this may be a design consideration).
        """
        new_status = TaskStatus(new_status_value)
        if new_status == TaskStatus.DONE:
            task = self.storage.get_task(task_id)
            if task:
                task.mark_as_done()
                self.storage.save()
                return True
        else:
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
            >>> 
            >>> if not success:
            ...     print("Task not found")
        
        Note:
            - Only the priority field is modified. Status, due_date, tags, and
              description remain unchanged.
            - Changes are persisted immediately to storage.
        
        Edge Cases:
            - Non-existent task_id: Returns False without raising an error.
            - Same priority: Succeeds but has no practical effect.
        """
        new_priority = TaskPriority(new_priority_value)
        return self.storage.update_task(task_id, priority=new_priority)

    def update_task_due_date(self, task_id, due_date_str):
        """
        Update the due date of an existing task.
        
        Changes a task's due date to a new value. The date must be in YYYY-MM-DD
        format. If the format is invalid, the method returns False and logs an error
        without updating the task.
        
        Args:
            task_id (int): The unique ID of the task to update. Must refer to an
                existing task in storage.
            due_date_str (str): New due date in YYYY-MM-DD format.
                Example: "2026-12-31"
                Pass empty string or None to clear the due date (not recommended;
                use a special method if available).
        
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
            >>> # Set due date
            >>> success = manager.update_task_due_date(task_id, "2026-09-15")
            >>> 
            >>> if success:
            ...     print("Due date updated")
            ... else:
            ...     print("Invalid date or task not found")
            >>> 
            >>> # Attempt invalid format
            >>> manager.update_task_due_date(task_id, "09/15/2026")  # Invalid
            >>> # Prints: "Invalid date format. Use YYYY-MM-DD"
            >>> # Returns: False
        
        Note:
            - Invalid date formats print a user-friendly message but don't raise
              exceptions, making this suitable for CLI applications.
            - The method does not validate whether the date is in the future or past.
            - Parsing only supports YYYY-MM-DD; other formats are rejected.
        
        Edge Cases:
            - Non-existent task_id: Returns False.
            - Empty string due_date_str: Raises ValueError (caught and returns False).
            - Date in the past: Allowed; no validation prevents this.
            - Leap year dates (e.g., "2024-02-29"): Correctly validated by strptime.
        """
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            return self.storage.update_task(task_id, due_date=due_date)
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return False

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
            >>> 
            >>> if success:
            ...     print("Task deleted")
            ... else:
            ...     print("Task not found")
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
        
        Args:
            task_id (int): The unique ID of the task to tag. Must refer to an
                existing task in storage.
            tag (str): The tag string to add. Should be alphanumeric and concise.
                Special characters may cause issues in some contexts.
                Tag names are case-sensitive ("Work" and "work" are different).
        
        Returns:
            bool: True if the tag was successfully added or already existed, False if
                the task_id doesn't exist.
        
        Raises:
            Does not raise exceptions; returns False if task not found.
        
        Example:
            >>> manager = TaskManager()
            >>> task_id = manager.create_task("Update documentation")
            >>> 
            >>> # Add a tag
            >>> success = manager.add_tag_to_task(task_id, "documentation")
            >>> 
            >>> # Add another tag
            >>> success = manager.add_tag_to_task(task_id, "writing")
            >>> 
            >>> # Try to add duplicate (silently ignored)
            >>> manager.add_tag_to_task(task_id, "documentation")  # No effect
            >>> 
            >>> # Verify tags
            >>> task = manager.get_task_details(task_id)
            >>> print(task.tags)  # ['documentation', 'writing']
        
        Note:
            - Duplicate tags are silently ignored (no error, no exception).
            - Tags are added in the order they are provided.
            - Storage is automatically saved after adding a tag.
            - No limit on the number of tags per task (depends on storage).
        
        Edge Cases:
            - Non-existent task_id: Returns False.
            - Empty tag string: Technically allowed but creates issues downstream.
            - Task already has maximum tags: No validation; behavior depends on storage.
            - Duplicate tag: Silently ignored; returns True anyway.
        """
        task = self.storage.get_task(task_id)
        if task:
            if tag not in task.tags:
                task.tags.append(tag)
                self.storage.save()
            return True
        return False

    def remove_tag_from_task(self, task_id, tag):
        """
        Remove a tag from an existing task.
        
        Deletes a tag from the task's tag list. If the tag doesn't exist, returns
        False. Changes are persisted immediately to storage.
        
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
            >>> 
            >>> if success:
            ...     print("Tag removed")
            ... else:
            ...     print("Tag not found or task doesn't exist")
            >>> 
            >>> # Verify removal
            >>> task = manager.get_task_details(task_id)
            >>> print(task.tags)  # ['code']
            >>> 
            >>> # Try to remove non-existent tag
            >>> success = manager.remove_tag_from_task(task_id, "completed")  # False
        
        Note:
            - Only exact matches are removed (case-sensitive).
            - If multiple instances of the same tag exist, only the first is removed
              (depends on list.remove() behavior).
            - Storage is automatically saved after removing a tag.
            - Removing the last tag is allowed; task can have zero tags.
        
        Edge Cases:
            - Non-existent task_id: Returns False.
            - Non-existent tag: Returns False (doesn't raise ValueError).
            - Case mismatch: Tag not found and returns False ("Work" != "work").
            - Empty tag list: Attempting to remove from empty list returns False.
        """
        task = self.storage.get_task(task_id)
        if task and tag in task.tags:
            task.tags.remove(tag)
            self.storage.save()
            return True
        return False

    def get_statistics(self):
        """
        Generate comprehensive statistics about all tasks in storage.
        
        Calculates aggregate metrics including total task count, distribution by
        status and priority, overdue task count, and recently completed tasks.
        
        Args:
            None
        
        Returns:
            dict: A dictionary containing the following keys:
                - total (int): Total number of tasks in storage.
                - by_status (dict): Task count grouped by status.
                    Keys are status names/values (e.g., "pending", "in_progress", "done").
                    Example: {"pending": 5, "in_progress": 3, "done": 12}
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
            By status: {'pending': 3, 'in_progress': 0, 'done': 0}
            >>> 
            >>> print(f"Overdue tasks: {stats['overdue']}")
            Overdue tasks: 0
            >>> 
            >>> print(f"Completed this week: {stats['completed_last_week']}")
            Completed this week: 0
        
        Note:
            - Empty storage returns all zeros.
            - "Last 7 days" is calculated from the current datetime (datetime.now()).
            - Overdue determination depends on task.is_overdue() method.
            - Completed timestamp (completed_at) must be set for recent completion
              counting; tasks without this timestamp are not counted.
        
        Edge Cases:
            - No tasks: All counts are 0, but dictionary keys still exist.
            - All tasks completed long ago: completed_last_week will be 0.
            - All tasks overdue: overdue count may equal total - done_count.
            - Priority/status enums with unusual names: Dictionary keys reflect
              enum names/values exactly as defined.
        
        Performance Considerations:
            - Scans all tasks multiple times (counts by status, priority, and
              checks overdue/recent). O(n) complexity where n = total tasks.
            - For very large task databases (10k+ tasks), this method may be slow.
            - Consider caching results if called frequently.
        """
        tasks = self.storage.get_all_tasks()
        total = len(tasks)

        # Count by status
        status_counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            status_counts[task.status.value] += 1

        # Count by priority
        priority_counts = {priority.name: 0 for priority in TaskPriority}
        for task in tasks:
            priority_counts[task.priority.name] += 1

        # Count overdue
        overdue_count = len([task for task in tasks if task.is_overdue()])

        # Count completed in last 7 days
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