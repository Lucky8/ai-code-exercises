# TaskManager Code Analysis & Documentation

## Annotated Code with Strategic Comments

```python
import argparse
from datetime import datetime, timedelta

from models import TaskPriority, Task, TaskStatus
from storage import TaskStorage


class TaskManager:
    """High-level task management interface that bridges user operations and storage."""
    
    def __init__(self, storage_path="tasks.json"):
        self.storage = TaskStorage(storage_path)

    def create_task(self, title, description="", priority_value=2,
                   due_date_str=None, tags=None):
        priority = TaskPriority(priority_value)
        due_date = None
        
        # VALIDATION POINT: Date parsing happens BEFORE Task creation
        # If date is invalid, entire task creation fails (returns None)
        # This prevents invalid Task objects from being created
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
                return None  # ⚠️ NOTE: Returns None, not False (inconsistent with other methods)

        task = Task(title, description, priority, due_date, tags)
        task_id = self.storage.add_task(task)
        return task_id

    def list_tasks(self, status_filter=None, priority_filter=None, show_overdue=False):
        """
        FILTER PRECEDENCE (cascading if-statements):
        1. show_overdue=True → returns ONLY overdue tasks (other filters ignored)
        2. status_filter set → returns tasks with matching status
        3. priority_filter set → returns tasks with matching priority  
        4. No filters → returns ALL tasks
        
        IMPLICATION: Cannot combine filters (e.g., "show me overdue HIGH priority tasks")
        Only one filter applies per call. If you need multiple filters, must call twice.
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
        ASYMMETRIC HANDLING:
        - If transitioning TO DONE: Special behavior triggered
          * Fetches task, calls mark_as_done() (sets completed_at timestamp)
          * Manually saves storage
          * Returns True/False based on task existence
          
        - If transitioning to other statuses: Delegated to storage
          * Storage.update_task() handles the update
          * Caller doesn't control save behavior
          
        CONSEQUENCE: DONE status is a special "completion" event, other status changes
        are just state transitions.
        """
        new_status = TaskStatus(new_status_value)
        if new_status == TaskStatus.DONE:
            # SPECIAL CASE: Mark as done includes timestamp tracking
            task = self.storage.get_task(task_id)
            if task:
                task.mark_as_done()  # Side effect: sets completed_at
                self.storage.save()   # Explicit save for DONE status
                return True
        else:
            # Other status transitions delegated to storage
            # Storage may or may not auto-save (inconsistent with DONE behavior)
            return self.storage.update_task(task_id, status=new_status)

    def update_task_priority(self, task_id, new_priority_value):
        new_priority = TaskPriority(new_priority_value)
        return self.storage.update_task(task_id, priority=new_priority)

    def update_task_due_date(self, task_id, due_date_str):
        """
        SAME DATE PARSING LOGIC as create_task, but different error handling:
        - Returns False on invalid date (vs None in create_task)
        ⚠️ INCONSISTENCY: Callers need to check for both None and False
        """
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            return self.storage.update_task(task_id, due_date=due_date)
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return False  # ⚠️ NOTE: Different from create_task (which returns None)

    def delete_task(self, task_id):
        return self.storage.delete_task(task_id)

    def get_task_details(self, task_id):
        return self.storage.get_task(task_id)

    def add_tag_to_task(self, task_id, tag):
        """
        TRICKY RETURN VALUE:
        - Returns True if task EXISTS (whether tag was added or already existed)
        - Returns False only if task DOESN'T EXIST
        
        This means: add_tag_to_task(123, "urgent") returns True even if task 123
        doesn't exist in storage! (The check is inverted)
        
        ASSUMPTION: caller wants to know "did the task exist?", not "was tag added?"
        """
        task = self.storage.get_task(task_id)
        if task:
            if tag not in task.tags:  # Duplicate prevention
                task.tags.append(tag)
                self.storage.save()
            return True  # ⚠️ Returns True even if tag already existed
        return False

    def remove_tag_from_task(self, task_id, tag):
        """
        RETURN VALUE: True only if tag was successfully removed
        - Task not found → False
        - Tag not in task.tags → False  
        - Tag removed → True
        
        CONTRAST with add_tag_to_task: This one is more predictable/correct.
        """
        task = self.storage.get_task(task_id)
        if task and tag in task.tags:  # Requires BOTH conditions
            task.tags.remove(tag)
            self.storage.save()
            return True
        return False

    def get_statistics(self):
        """
        PERFORMANCE: Scans task list multiple times (not efficient)
        
        Step-by-step:
        1. Fetch ALL tasks (single call)
        2. Initialize status_counts dict with ALL enum values (even 0-count ones)
        3. Loop tasks → count by status
        4. Initialize priority_counts dict with ALL enum values
        5. Loop tasks → count by priority
        6. Loop tasks again → count overdue (separate pass!)
        7. Loop tasks again → count recently completed (another separate pass!)
        
        OPTIMIZATION: Could be single O(n) pass instead of O(5n).
        
        DICTIONARY INITIALIZATION TRICK:
        status_counts = {status.value: 0 for status in TaskStatus}
        This pre-initializes counters for ALL statuses (even if 0 tasks with that status).
        Result: Return dict always has complete keys like "PENDING": 0 even if no pending tasks.
        """
        tasks = self.storage.get_all_tasks()
        total = len(tasks)

        # Pre-initialize with ALL possible enum values
        # Ensures return dict has complete, consistent keys
        status_counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            status_counts[task.status.value] += 1

        # Same pattern for priority
        priority_counts = {priority.name: 0 for priority in TaskPriority}
        for task in tasks:
            priority_counts[task.priority.name] += 1

        # Separate pass for overdue check
        # ASSUMPTION: task.is_overdue() returns boolean and works correctly
        overdue_count = len([task for task in tasks if task.is_overdue()])

        # Separate pass for recent completion
        # ASSUMPTION: task.completed_at is set only when mark_as_done() was called
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
```

---

## Key Patterns Identified

### **1. Validation-First Pattern**
Date strings are validated **before** creating/updating, not after. This is good practice—fail early, don't persist invalid data.

### **2. Cascading Filters**
`list_tasks()` uses cascading if-statements, not a single combined filter. This limits flexibility but simplifies logic.

### **3. Asymmetric Error Handling**
- Returns `None`, `False`, and `True` inconsistently across methods
- Makes error handling unpredictable for callers
- No exception raising (all errors are silent via print)

### **4. Delegation Pattern**
Most methods delegate to storage, except CRUD on a single property. This keeps logic centralized but hides save behavior.

### **5. Dictionary Comprehension for Enum Counts**
Pre-initializes with all enum values so return dict is always complete. Smart pattern for reporting.

---

## Potential Improvements (Without Changing Functionality)

### **High Priority**

1. **Standardize error returns**
   ```python
   # Before: None vs False inconsistency
   # After: Always return (success: bool, result: any)
   return (False, None)  # consistent pattern
   ```

2. **Add exception handling**
   ```python
   try:
       priority = TaskPriority(priority_value)
   except ValueError:
       print(f"Invalid priority: {priority_value}. Use 1-4.")
       return None
   ```

3. **Optimize statistics to single pass**
   ```python
   for task in tasks:
       status_counts[task.status.value] += 1
       priority_counts[task.priority.name] += 1
       if task.is_overdue():
           overdue_count += 1
       # ... etc, all in one loop
   ```

4. **Fix tag operation inconsistency**
   ```python
   # add_tag_to_task should return (tag_added: bool) not (task_exists: bool)
   def add_tag_to_task(self, task_id, tag):
       task = self.storage.get_task(task_id)
       if not task:
           return False
       if tag in task.tags:
           return False  # Already exists
       task.tags.append(tag)
       self.storage.save()
       return True
   ```

### **Medium Priority**

5. **Use logging instead of print**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.error("Invalid date format: %s", due_date_str)
   ```

6. **Add type hints**
   ```python
   def create_task(self, title: str, description: str = "", 
                  priority_value: int = 2, due_date_str: str | None = None,
                  tags: list[str] | None = None) -> int | None:
   ```

7. **Validate enum values before using**
   ```python
   if priority_value not in [1, 2, 3, 4]:
       print(f"Invalid priority: {priority_value}")
       return None
   ```

### **Low Priority**

8. **Add docstrings** with parameter descriptions
9. **Consider context manager** for storage (with statement)
10. **Cache statistics results** if called frequently with same data

---

## Summary

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Correctness** | ✅ Good | Core logic is sound |
| **Consistency** | ⚠️ Fair | Error handling is inconsistent |
| **Error Handling** | ⚠️ Fair | Silent failures; no exceptions |
| **Performance** | ⚠️ Fair | Multiple redundant scans |
| **Maintainability** | ✅ Good | Clear intent, simple logic |
| **Robustness** | ⚠️ Fair | No validation of inputs |
| **Documentation** | ❌ Poor | No docstrings or comments |

