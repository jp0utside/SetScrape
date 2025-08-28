import asyncio
import threading
import time
import logging
from typing import Callable, Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import queue

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BackgroundTask:
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    progress: float = 0.0

class BackgroundTaskManager:
    """Simple background task manager to replace Celery"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.tasks: Dict[str, BackgroundTask] = {}
        self.task_queue = queue.Queue()
        self.workers: List[threading.Thread] = []
        self.running = False
        self._lock = threading.Lock()
        self._task_counter = 0
    
    def start(self):
        """Start the background task manager"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"Worker-{i}")
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Background task manager started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the background task manager"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        logger.info("Background task manager stopped")
    
    def _worker_loop(self):
        """Worker thread loop"""
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.task_queue.get(timeout=1)
                self._execute_task(task)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def _execute_task(self, task: BackgroundTask):
        """Execute a background task"""
        try:
            # Update task status
            with self._lock:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow()
            
            # Execute the task
            if asyncio.iscoroutinefunction(task.func):
                # Handle async functions
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(task.func(*task.args, **task.kwargs))
                finally:
                    loop.close()
            else:
                # Handle sync functions
                result = task.func(*task.args, **task.kwargs)
            
            # Update task status
            with self._lock:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = result
                task.progress = 1.0
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            # Update task status on error
            with self._lock:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.error = str(e)
            
            logger.error(f"Task {task.id} failed: {e}")
    
    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task for execution"""
        task_id = f"task_{self._task_counter}"
        self._task_counter += 1
        
        task = BackgroundTask(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        with self._lock:
            self.tasks[task_id] = task
        
        # Add to queue
        self.task_queue.put(task)
        
        logger.info(f"Task {task_id} submitted")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[BackgroundTask]:
        """Get all tasks"""
        with self._lock:
            return list(self.tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task (only works for pending tasks)"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    return True
        return False
    
    def clear_completed_tasks(self, max_age_hours: int = 24):
        """Clear completed tasks older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self._lock:
            tasks_to_remove = [
                task_id for task_id, task in self.tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at and task.completed_at < cutoff_time
            ]
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
        
        logger.info(f"Cleared {len(tasks_to_remove)} old tasks")

# Global task manager instance
task_manager = BackgroundTaskManager()

# Decorator for background tasks
def background_task(func: Callable) -> Callable:
    """Decorator to mark a function as a background task"""
    def wrapper(*args, **kwargs):
        return task_manager.submit_task(func, *args, **kwargs)
    return wrapper

# Utility functions
def start_background_tasks():
    """Start the background task manager"""
    task_manager.start()

def stop_background_tasks():
    """Stop the background task manager"""
    task_manager.stop()

def submit_background_task(func: Callable, *args, **kwargs) -> str:
    """Submit a background task"""
    return task_manager.submit_task(func, *args, **kwargs)

def get_background_task(task_id: str) -> Optional[BackgroundTask]:
    """Get a background task by ID"""
    return task_manager.get_task(task_id)

def get_all_background_tasks() -> List[BackgroundTask]:
    """Get all background tasks"""
    return task_manager.get_all_tasks()

def cancel_background_task(task_id: str) -> bool:
    """Cancel a background task"""
    return task_manager.cancel_task(task_id)

# Example background tasks
@background_task
def example_background_task(data: str, delay: int = 5):
    """Example background task"""
    time.sleep(delay)
    return f"Processed: {data}"

@background_task
async def example_async_background_task(data: str, delay: int = 5):
    """Example async background task"""
    await asyncio.sleep(delay)
    return f"Async processed: {data}"
