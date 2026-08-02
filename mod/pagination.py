"""
Pagination utilities for SQLAlchemy queries.

This module provides reusable pagination classes and utilities for paginating
database query results consistently across the application.
"""

from typing import List, Dict, Any, Optional, TypeVar, Generic
from math import ceil
from flask import request
from sqlalchemy.orm import Query
from mod.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class Paginator(Generic[T]):
    """Generic paginator for database queries."""
    
    def __init__(
        self,
        query: Query,
        page: int = 1,
        per_page: int = 15,
        max_per_page: int = 100
    ):
        """
        Initialize paginator.
        
        Args:
            query: SQLAlchemy Query object
            page: Page number (1-indexed)
            per_page: Items per page
            max_per_page: Maximum items per page to prevent DoS
        """
        self.query = query
        self.page = max(1, page)  # Ensure page is at least 1
        self.per_page = min(per_page, max_per_page)  # Limit per_page
        self.max_per_page = max_per_page
        
        # Validate inputs
        if self.per_page < 1:
            self.per_page = 15
    
    @property
    def total(self) -> int:
        """Get total count of items."""
        return self.query.count()
    
    @property
    def pages(self) -> int:
        """Get total number of pages."""
        if self.total == 0:
            return 1
        return ceil(self.total / self.per_page)
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.pages
    
    @property
    def previous_page(self) -> Optional[int]:
        """Get previous page number."""
        if self.has_previous:
            return self.page - 1
        return None
    
    @property
    def next_page(self) -> Optional[int]:
        """Get next page number."""
        if self.has_next:
            return self.page + 1
        return None
    
    def items(self) -> List[T]:
        """
        Get items for current page.
        
        Returns:
            List of items for current page
        """
        offset = (self.page - 1) * self.per_page
        return self.query.offset(offset).limit(self.per_page).all()
    
    def iter_pages(self, left_edge: int = 1, left_cursor: int = 1,
                   right_cursor: int = 5, right_edge: int = 2) -> List[Optional[int]]:
        """
        Get list of page numbers to display in pagination controls.
        
        Args:
            left_edge: Pages to show at the beginning
            left_cursor: Pages to show to the left of current page
            right_cursor: Pages to show to the right of current page
            right_edge: Pages to show at the end
            
        Returns:
            List of page numbers (None represents gaps)
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                (self.page - left_cursor <= num <= self.page + right_cursor) or
                num > self.pages - right_edge):
                
                if last + 1 != num:
                    yield None
                yield num
                last = num
    
    def to_dict(self, items_converter=None) -> Dict[str, Any]:
        """
        Convert paginated results to dictionary.
        
        Args:
            items_converter: Optional function to convert items to dict
            
        Returns:
            Dictionary with pagination data
        """
        items = self.items()
        
        if items_converter:
            items = [items_converter(item) for item in items]
        elif hasattr(items[0] if items else None, 'to_dict'):
            items = [item.to_dict() for item in items]
        else:
            items = [item for item in items]
        
        return {
            'items': items,
            'total': self.total,
            'page': self.page,
            'per_page': self.per_page,
            'pages': self.pages,
            'has_next': self.has_next,
            'has_previous': self.has_previous,
            'next_page': self.next_page,
            'previous_page': self.previous_page,
        }


class PaginationHelper:
    """Helper class for pagination operations."""
    
    @staticmethod
    def get_page_from_request(default: int = 1) -> int:
        """
        Get page number from request arguments.
        
        Args:
            default: Default page if not provided
            
        Returns:
            Page number
        """
        try:
            page = int(request.args.get('page', default))
            return max(1, page)  # Ensure at least 1
        except (ValueError, TypeError):
            logger.warning(f"Invalid page parameter: {request.args.get('page')}")
            return default
    
    @staticmethod
    def get_per_page_from_request(default: int = 15, max_per_page: int = 100) -> int:
        """
        Get per_page from request arguments.
        
        Args:
            default: Default per_page if not provided
            max_per_page: Maximum allowed per_page
            
        Returns:
            Items per page
        """
        try:
            per_page = int(request.args.get('per_page', default))
            return min(max(1, per_page), max_per_page)  # Between 1 and max_per_page
        except (ValueError, TypeError):
            logger.warning(f"Invalid per_page parameter: {request.args.get('per_page')}")
            return default
    
    @staticmethod
    def paginate_query(
        query: Query,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        max_per_page: int = 100
    ) -> Paginator:
        """
        Paginate a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy Query object
            page: Page number (from request if not provided)
            per_page: Items per page (from request if not provided)
            max_per_page: Maximum items per page
            
        Returns:
            Paginator object
        """
        if page is None:
            page = PaginationHelper.get_page_from_request()
        
        if per_page is None:
            per_page = PaginationHelper.get_per_page_from_request(max_per_page=max_per_page)
        
        return Paginator(query, page=page, per_page=per_page, max_per_page=max_per_page)
    
    @staticmethod
    def create_pagination_response(
        paginator: Paginator,
        items_converter=None
    ) -> Dict[str, Any]:
        """
        Create a standard pagination response.
        
        Args:
            paginator: Paginator object
            items_converter: Optional function to convert items
            
        Returns:
            Pagination response dictionary
        """
        return paginator.to_dict(items_converter=items_converter)


class CursorPaginator(Generic[T]):
    """Cursor-based paginator for efficient pagination of large datasets."""
    
    def __init__(
        self,
        query: Query,
        cursor_field,
        cursor: Optional[str] = None,
        limit: int = 15,
        max_limit: int = 100,
        reverse: bool = False
    ):
        """
        Initialize cursor-based paginator.
        
        Args:
            query: SQLAlchemy Query object
            cursor_field: The field to use for cursor (usually ID or timestamp)
            cursor: Current cursor value
            limit: Items to return
            max_limit: Maximum items to return
            reverse: If True, paginate in reverse order
        """
        self.query = query
        self.cursor_field = cursor_field
        self.cursor = cursor
        self.limit = min(limit, max_limit)
        self.max_limit = max_limit
        self.reverse = reverse
    
    def items(self) -> List[T]:
        """
        Get items for current cursor page.
        
        Returns:
            List of items
        """
        q = self.query
        
        # Apply cursor filtering
        if self.cursor:
            try:
                if self.reverse:
                    q = q.filter(self.cursor_field < self.cursor)
                else:
                    q = q.filter(self.cursor_field > self.cursor)
            except Exception as e:
                logger.warning(f"Error applying cursor filter: {e}")
        
        # Order and limit
        if self.reverse:
            q = q.order_by(self.cursor_field.desc())
        else:
            q = q.order_by(self.cursor_field.asc())
        
        # Request one extra to determine if there's a next page
        items = q.limit(self.limit + 1).all()
        
        self.has_more = len(items) > self.limit
        if self.has_more:
            items = items[:self.limit]
        
        return items
    
    def next_cursor(self, items: List[T]) -> Optional[str]:
        """
        Get cursor value for next page.
        
        Args:
            items: Current page items
            
        Returns:
            Cursor value for next page, or None if no more items
        """
        if not items or not self.has_more:
            return None
        
        last_item = items[-1]
        # Get the cursor field value from the last item
        cursor_value = getattr(last_item, self.cursor_field.key, None)
        return str(cursor_value) if cursor_value is not None else None
    
    def to_dict(self, items_converter=None) -> Dict[str, Any]:
        """
        Convert cursor paginated results to dictionary.
        
        Args:
            items_converter: Optional function to convert items
            
        Returns:
            Dictionary with cursor pagination data
        """
        items = self.items()
        
        if items_converter:
            items = [items_converter(item) for item in items]
        elif hasattr(items[0] if items else None, 'to_dict'):
            items = [item.to_dict() for item in items]
        
        return {
            'items': items,
            'next_cursor': self.next_cursor(items),
            'has_more': self.has_more,
            'limit': self.limit,
        }


class SearchPaginator:
    """Specialized paginator for search results."""
    
    def __init__(
        self,
        query: Query,
        search_term: str,
        page: int = 1,
        per_page: int = 15,
        max_per_page: int = 100
    ):
        """
        Initialize search paginator.
        
        Args:
            query: SQLAlchemy Query object
            search_term: The search term used
            page: Page number
            per_page: Items per page
            max_per_page: Maximum items per page
        """
        self.query = query
        self.search_term = search_term
        self.paginator = Paginator(query, page=page, per_page=per_page, max_per_page=max_per_page)
    
    def to_dict(self, items_converter=None) -> Dict[str, Any]:
        """
        Convert search results to dictionary.
        
        Args:
            items_converter: Optional function to convert items
            
        Returns:
            Search results response dictionary
        """
        result = self.paginator.to_dict(items_converter=items_converter)
        result['search_term'] = self.search_term
        result['query_string'] = f"?q={self.search_term}&page={self.paginator.page}&per_page={self.paginator.per_page}"
        return result


# Helper functions
def paginate(query: Query, page: int = 1, per_page: int = 15, max_per_page: int = 100) -> Paginator:
    """Convenience function to create a paginator."""
    return Paginator(query, page=page, per_page=per_page, max_per_page=max_per_page)


def paginate_from_request(query: Query, max_per_page: int = 100) -> Paginator:
    """Convenience function to paginate from request parameters."""
    return PaginationHelper.paginate_query(query, max_per_page=max_per_page)


def get_pagination_params() -> Dict[str, int]:
    """Get pagination parameters from request."""
    return {
        'page': PaginationHelper.get_page_from_request(),
        'per_page': PaginationHelper.get_per_page_from_request(),
    }
