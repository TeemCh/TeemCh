"""
Rate limiting utility to avoid overwhelming social media platforms
"""

import time
import random
from typing import Optional


class RateLimiter:
    """Rate limiter with configurable delays and jitter"""
    
    def __init__(self, delay: float = 2.0, jitter: float = 0.5, max_delay: float = 10.0):
        """
        Initialize rate limiter
        
        Args:
            delay: Base delay between requests in seconds
            jitter: Random jitter to add/subtract from delay (0.0 to 1.0)
            max_delay: Maximum delay allowed
        """
        self.base_delay = delay
        self.jitter = jitter
        self.max_delay = max_delay
        self.last_request_time = 0
    
    def wait(self):
        """Wait for the appropriate amount of time before next request"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate delay with jitter
        jitter_amount = random.uniform(-self.jitter, self.jitter) * self.base_delay
        delay = self.base_delay + jitter_amount
        delay = min(delay, self.max_delay)  # Cap at max_delay
        delay = max(delay, 0.1)  # Minimum 0.1 seconds
        
        # Sleep if needed
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def set_delay(self, delay: float):
        """Update the base delay"""
        self.base_delay = delay
    
    def reset(self):
        """Reset the rate limiter"""
        self.last_request_time = 0


class AdaptiveRateLimiter(RateLimiter):
    """Rate limiter that adapts based on success/failure rates"""
    
    def __init__(self, initial_delay: float = 2.0, min_delay: float = 1.0, 
                 max_delay: float = 30.0, adaptation_factor: float = 1.5):
        """
        Initialize adaptive rate limiter
        
        Args:
            initial_delay: Initial delay between requests
            min_delay: Minimum delay allowed
            max_delay: Maximum delay allowed
            adaptation_factor: Factor to multiply/divide delay by
        """
        super().__init__(delay=initial_delay)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.adaptation_factor = adaptation_factor
        self.success_count = 0
        self.failure_count = 0
        self.total_requests = 0
    
    def on_success(self):
        """Call this when a request succeeds"""
        self.success_count += 1
        self.total_requests += 1
        
        # Decrease delay if we have enough successful requests
        if self.success_count % 10 == 0:  # Every 10 successes
            self.base_delay = max(
                self.min_delay,
                self.base_delay / self.adaptation_factor
            )
    
    def on_failure(self):
        """Call this when a request fails (rate limited, blocked, etc.)"""
        self.failure_count += 1
        self.total_requests += 1
        
        # Increase delay on failure
        self.base_delay = min(
            self.max_delay,
            self.base_delay * self.adaptation_factor
        )
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            'total_requests': self.total_requests,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.get_success_rate(),
            'current_delay': self.base_delay
        }


class BurstRateLimiter:
    """Rate limiter that allows bursts of requests with cooldown periods"""
    
    def __init__(self, burst_size: int = 5, burst_delay: float = 1.0, 
                 cooldown_delay: float = 10.0):
        """
        Initialize burst rate limiter
        
        Args:
            burst_size: Number of requests allowed in a burst
            burst_delay: Delay between requests within a burst
            cooldown_delay: Delay after a burst is complete
        """
        self.burst_size = burst_size
        self.burst_delay = burst_delay
        self.cooldown_delay = cooldown_delay
        self.current_burst = 0
        self.last_request_time = 0
        self.last_burst_end = 0
    
    def wait(self):
        """Wait with burst and cooldown logic"""
        current_time = time.time()
        
        # Check if we're in cooldown period
        if (self.current_burst >= self.burst_size and 
            current_time - self.last_burst_end < self.cooldown_delay):
            sleep_time = self.cooldown_delay - (current_time - self.last_burst_end)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.current_burst = 0
        
        # Normal burst delay
        elif self.current_burst > 0:
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.burst_delay:
                time.sleep(self.burst_delay - time_since_last)
        
        # Update counters
        self.current_burst += 1
        self.last_request_time = time.time()
        
        # Mark end of burst
        if self.current_burst >= self.burst_size:
            self.last_burst_end = time.time()
    
    def reset_burst(self):
        """Reset the current burst counter"""
        self.current_burst = 0


class BackoffRateLimiter:
    """Rate limiter with exponential backoff"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, 
                 backoff_factor: float = 2.0):
        """
        Initialize backoff rate limiter
        
        Args:
            base_delay: Base delay for first attempt
            max_delay: Maximum delay allowed
            backoff_factor: Factor to multiply delay by on each failure
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.current_delay = base_delay
        self.failure_count = 0
    
    def wait(self):
        """Wait with current delay"""
        time.sleep(self.current_delay)
    
    def on_success(self):
        """Reset delay on success"""
        self.current_delay = self.base_delay
        self.failure_count = 0
    
    def on_failure(self):
        """Increase delay on failure"""
        self.failure_count += 1
        self.current_delay = min(
            self.max_delay,
            self.base_delay * (self.backoff_factor ** self.failure_count)
        )
    
    def get_current_delay(self) -> float:
        """Get current delay value"""
        return self.current_delay