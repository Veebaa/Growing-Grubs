"""
API client utilities with rate limiting and retry logic.

This module provides utilities for making HTTP requests to external APIs
with built-in rate limiting, retry logic, and error handling.
"""

import time
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mod.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple rate limiter with exponential backoff."""
    
    def __init__(self, requests_per_second: float = 1.0, max_retries: int = 3):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second (default: 1)
            max_retries: Maximum number of retries (default: 3)
        """
        self.min_interval = 1.0 / requests_per_second
        self.max_retries = max_retries
        self.last_request_time = 0
    
    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    @staticmethod
    def exponential_backoff(attempt: int, base_delay: float = 1.0) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: The attempt number (0-indexed)
            base_delay: Base delay in seconds
            
        Returns:
            Delay in seconds
        """
        return base_delay * (2 ** attempt)


class APIClient:
    """HTTP client with retry logic and rate limiting."""
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize the API client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry strategy.
        
        Returns:
            Configured requests.Session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        rate_limiter: Optional[RateLimiter] = None
    ) -> Optional[requests.Response]:
        """
        Make a GET request with retry logic.
        
        Args:
            url: The URL to request
            headers: Optional request headers
            params: Optional query parameters
            rate_limiter: Optional RateLimiter instance for rate limiting
            
        Returns:
            Response object, or None if all retries failed
        """
        if rate_limiter:
            rate_limiter.wait()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.debug(f"Successful API request to {url}")
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on request to {url}, attempt {attempt + 1}/{self.max_retries + 1}")
                if attempt < self.max_retries:
                    delay = RateLimiter.exponential_backoff(attempt)
                    logger.debug(f"Retrying after {delay} seconds...")
                    time.sleep(delay)
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = int(e.response.headers.get('Retry-After', RateLimiter.exponential_backoff(attempt)))
                    logger.warning(f"Rate limited on {url}, waiting {retry_after} seconds")
                    if attempt < self.max_retries:
                        time.sleep(retry_after)
                else:
                    logger.error(f"HTTP error on {url}: {e}")
                    raise
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on {url}: {e}")
                if attempt < self.max_retries:
                    delay = RateLimiter.exponential_backoff(attempt)
                    logger.debug(f"Retrying after {delay} seconds...")
                    time.sleep(delay)
                else:
                    return None
        
        logger.error(f"Failed to get response from {url} after {self.max_retries + 1} attempts")
        return None
    
    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        rate_limiter: Optional[RateLimiter] = None
    ) -> Optional[requests.Response]:
        """
        Make a POST request with retry logic.
        
        Args:
            url: The URL to request
            headers: Optional request headers
            data: Optional form data
            json: Optional JSON data
            rate_limiter: Optional RateLimiter instance for rate limiting
            
        Returns:
            Response object, or None if all retries failed
        """
        if rate_limiter:
            rate_limiter.wait()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    url,
                    headers=headers,
                    data=data,
                    json=json,
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.debug(f"Successful POST request to {url}")
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on POST to {url}, attempt {attempt + 1}/{self.max_retries + 1}")
                if attempt < self.max_retries:
                    delay = RateLimiter.exponential_backoff(attempt)
                    time.sleep(delay)
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get('Retry-After', RateLimiter.exponential_backoff(attempt)))
                    logger.warning(f"Rate limited on POST {url}, waiting {retry_after} seconds")
                    if attempt < self.max_retries:
                        time.sleep(retry_after)
                else:
                    logger.error(f"HTTP error on POST {url}: {e}")
                    raise
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on POST {url}: {e}")
                if attempt < self.max_retries:
                    delay = RateLimiter.exponential_backoff(attempt)
                    time.sleep(delay)
                else:
                    return None
        
        logger.error(f"Failed to POST to {url} after {self.max_retries + 1} attempts")
        return None
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
