"""
Nitter Instance Manager
Handles health checking, rotation, and fallback for Nitter instances.
"""

import asyncio
import time
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import httpx
from loguru import logger

from .instances import NITTER_INSTANCES


class NitterInstance:
    """Represents a single Nitter instance with health status."""

    def __init__(self, url: str):
        self.url = url.rstrip('/')
        self.is_healthy = True
        self.last_check = None
        self.response_time = None
        self.failure_count = 0
        self.success_count = 0
        self.last_used = None

    def mark_success(self, response_time: float):
        """Mark instance as successful."""
        self.is_healthy = True
        self.response_time = response_time
        self.success_count += 1
        self.failure_count = 0
        self.last_check = datetime.now()
        self.last_used = datetime.now()

    def mark_failure(self):
        """Mark instance as failed."""
        self.failure_count += 1
        self.last_check = datetime.now()

        # Mark as unhealthy after 3 consecutive failures
        if self.failure_count >= 3:
            self.is_healthy = False

    def __repr__(self):
        return f"NitterInstance(url={self.url}, healthy={self.is_healthy}, response_time={self.response_time})"


class NitterInstanceManager:
    """
    Manages Nitter instances with automatic health checking and rotation.
    """

    def __init__(
        self,
        instances: Optional[List[str]] = None,
        health_check_interval: int = 300,  # 5 minutes
        request_timeout: int = 30
    ):
        """
        Initialize the Nitter instance manager.

        Args:
            instances: List of Nitter instance URLs. Uses default list if None.
            health_check_interval: Seconds between health checks
            request_timeout: Timeout for HTTP requests in seconds
        """
        instance_urls = instances or NITTER_INSTANCES
        self.instances = [NitterInstance(url) for url in instance_urls]
        self.health_check_interval = health_check_interval
        self.request_timeout = request_timeout
        self.current_index = 0
        self._health_check_task = None
        self._lock = asyncio.Lock()

        logger.info(f"Initialized NitterInstanceManager with {len(self.instances)} instances")

    async def start(self):
        """Start the health check background task."""
        await self._initial_health_check()
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Health check loop started")

    async def stop(self):
        """Stop the health check background task."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Health check loop stopped")

    async def _initial_health_check(self):
        """Perform initial health check on all instances."""
        logger.info("Performing initial health check on all instances...")
        await self._check_all_instances()
        healthy_count = sum(1 for inst in self.instances if inst.is_healthy)
        logger.info(f"Initial health check complete: {healthy_count}/{len(self.instances)} instances healthy")

    async def _health_check_loop(self):
        """Background task that periodically checks all instances."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_all_instances()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    async def _check_all_instances(self):
        """Check health of all instances concurrently."""
        tasks = [self._check_instance(instance) for instance in self.instances]
        await asyncio.gather(*tasks, return_exceptions=True)

        healthy_count = sum(1 for inst in self.instances if inst.is_healthy)
        logger.info(f"Health check: {healthy_count}/{len(self.instances)} instances healthy")

    async def _check_instance(self, instance: NitterInstance) -> bool:
        """
        Check if a single instance is healthy.

        Args:
            instance: The NitterInstance to check

        Returns:
            True if healthy, False otherwise
        """
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                # Try to fetch the instance homepage
                response = await client.get(f"{instance.url}/")

                if response.status_code == 200:
                    response_time = time.time() - start_time
                    instance.mark_success(response_time)
                    logger.debug(f"✓ {instance.url} is healthy (response time: {response_time:.2f}s)")
                    return True
                else:
                    instance.mark_failure()
                    logger.warning(f"✗ {instance.url} returned status {response.status_code}")
                    return False

        except Exception as e:
            instance.mark_failure()
            logger.warning(f"✗ {instance.url} health check failed: {e}")
            return False

    def get_healthy_instances(self) -> List[NitterInstance]:
        """Get list of all healthy instances, sorted by response time."""
        healthy = [inst for inst in self.instances if inst.is_healthy]
        # Sort by response time (fastest first), then by least recently used
        healthy.sort(key=lambda x: (x.response_time or 999, x.last_used or datetime.min))
        return healthy

    async def get_instance(self) -> Optional[NitterInstance]:
        """
        Get the next healthy instance using round-robin rotation.

        Returns:
            A healthy NitterInstance, or None if no instances are available
        """
        async with self._lock:
            healthy_instances = self.get_healthy_instances()

            if not healthy_instances:
                logger.error("No healthy Nitter instances available!")
                return None

            # Use round-robin selection among healthy instances
            instance = healthy_instances[self.current_index % len(healthy_instances)]
            self.current_index = (self.current_index + 1) % len(healthy_instances)

            instance.last_used = datetime.now()
            return instance

    async def get_instance_with_fallback(self, max_retries: int = 3) -> Optional[NitterInstance]:
        """
        Get a healthy instance with automatic fallback.

        Args:
            max_retries: Maximum number of instances to try

        Returns:
            A healthy NitterInstance, or None if all retries failed
        """
        healthy_instances = self.get_healthy_instances()

        if not healthy_instances:
            logger.error("No healthy instances available for fallback")
            return None

        # Try up to max_retries different instances
        for i in range(min(max_retries, len(healthy_instances))):
            instance = await self.get_instance()
            if instance:
                return instance

        return None

    def get_stats(self) -> Dict:
        """Get statistics about instance health."""
        healthy = [inst for inst in self.instances if inst.is_healthy]
        unhealthy = [inst for inst in self.instances if not inst.is_healthy]

        avg_response_time = None
        if healthy:
            response_times = [inst.response_time for inst in healthy if inst.response_time]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)

        return {
            "total_instances": len(self.instances),
            "healthy_instances": len(healthy),
            "unhealthy_instances": len(unhealthy),
            "avg_response_time": avg_response_time,
            "health_percentage": (len(healthy) / len(self.instances)) * 100 if self.instances else 0,
            "healthy_urls": [inst.url for inst in healthy],
            "unhealthy_urls": [inst.url for inst in unhealthy]
        }

    async def force_health_check(self):
        """Force an immediate health check of all instances."""
        logger.info("Forcing immediate health check...")
        await self._check_all_instances()
