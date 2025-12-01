import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for scheduling automatic news collection."""
    
    _instance: Optional['SchedulerService'] = None
    _scheduler: Optional[AsyncIOScheduler] = None
    _collect_callback: Optional[Callable[[], Awaitable[None]]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._scheduler = AsyncIOScheduler()
        return cls._instance
    
    def set_collect_callback(self, callback: Callable[[], Awaitable[None]]):
        """Set the callback function for news collection."""
        self._collect_callback = callback
    
    def start(self, interval_minutes: int = 60):
        """Start the scheduler with specified interval."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            self._scheduler = AsyncIOScheduler()
        
        # Add job
        self._scheduler.add_job(
            self._run_collection,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='news_collection',
            replace_existing=True,
            max_instances=1
        )
        
        try:
            self._scheduler.start()
            logger.info(f"Scheduler started with {interval_minutes} minute interval")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._scheduler is not None and self._scheduler.running
    
    def get_next_run(self) -> Optional[str]:
        """Get the next scheduled run time."""
        if not self._scheduler or not self._scheduler.running:
            return None
        
        job = self._scheduler.get_job('news_collection')
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None
    
    def update_interval(self, interval_minutes: int):
        """Update the collection interval."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.reschedule_job(
                'news_collection',
                trigger=IntervalTrigger(minutes=interval_minutes)
            )
            logger.info(f"Scheduler interval updated to {interval_minutes} minutes")
    
    async def _run_collection(self):
        """Run the collection callback."""
        if self._collect_callback:
            try:
                logger.info("Running scheduled news collection...")
                await self._collect_callback()
                logger.info("Scheduled collection completed")
            except Exception as e:
                logger.error(f"Scheduled collection failed: {e}")
        else:
            logger.warning("No collection callback set")
    
    async def run_now(self):
        """Trigger an immediate collection."""
        await self._run_collection()
