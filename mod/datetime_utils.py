"""Datetime utilities for the Growing Grubs application."""

from datetime import datetime, timedelta, date
from typing import Optional, Tuple


def get_utc_now() -> datetime:
    """
    Get the current UTC datetime.
    
    Returns:
        datetime: Current UTC datetime
    """
    return datetime.utcnow()


def get_utc_today() -> date:
    """
    Get today's date in UTC.
    
    Returns:
        date: Today's date
    """
    return datetime.utcnow().date()


def get_yesterday_date() -> date:
    """
    Get yesterday's date in UTC.
    
    Returns:
        date: Yesterday's date
    """
    return (datetime.utcnow() - timedelta(days=1)).date()


def get_date_range(days_back: int = 1) -> Tuple[date, date]:
    """
    Get a date range from N days ago to today.
    
    Args:
        days_back: Number of days to look back (default: 1 for yesterday)
    
    Returns:
        Tuple[date, date]: Tuple of (start_date, end_date)
    """
    end_date = get_utc_today()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date


def format_datetime(dt: Optional[datetime], fmt: str = '%Y-%m-%d %H:%M:%S') -> Optional[str]:
    """
    Format a datetime object to a string.
    
    Args:
        dt: Datetime object to format
        fmt: Format string (default: '%Y-%m-%d %H:%M:%S')
    
    Returns:
        str: Formatted datetime string, or None if dt is None
    """
    if dt is None:
        return None
    return dt.strftime(fmt)


def format_date(d: Optional[date], fmt: str = '%Y-%m-%d') -> Optional[str]:
    """
    Format a date object to a string.
    
    Args:
        d: Date object to format
        fmt: Format string (default: '%Y-%m-%d')
    
    Returns:
        str: Formatted date string, or None if d is None
    """
    if d is None:
        return None
    return d.strftime(fmt)
