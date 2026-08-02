"""
SQLAlchemy query builder helpers for common query patterns.

This module provides convenient helper functions for:
- Filtering queries by various criteria
- Sorting results
- Eager loading relationships
- Joining related tables
- Common aggregate operations

These helpers reduce code duplication and make queries more readable and maintainable.
"""

from typing import List, Optional, Any, Dict, Tuple, Type, Union
from sqlalchemy import desc, asc, and_, or_, func, Selectable
from sqlalchemy.orm import Query, joinedload, contains_eager, selectinload, subqueryload
from mod import db
from mod.models import Users, Recipe, Favourites, MealPlan, MealPlanDay


class QueryBuilder:
    """Helper class for building common SQLAlchemy queries with fluent interface."""
    
    def __init__(self, model: Type[db.Model]) -> None:
        """
        Initialize query builder with a model class.
        
        Args:
            model: SQLAlchemy model class to query
        """
        self.model = model
        self.query = db.session.query(model)
        self._filters: List[Any] = []
        self._eager_loads: List[Any] = []
        self._joins: List[Tuple[Type, Any]] = []
        self._order_by: List[Tuple[Any, bool]] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._distinct: bool = False
    
    def filter(self, condition: Any) -> 'QueryBuilder':
        """
        Add a filter condition to the query.
        
        Args:
            condition: SQLAlchemy filter condition
            
        Returns:
            Self for method chaining
        """
        self._filters.append(condition)
        return self
    
    def filter_by(self, **kwargs) -> 'QueryBuilder':
        """
        Add multiple filter conditions using keyword arguments.
        
        Args:
            **kwargs: Column name and value pairs to filter by
            
        Returns:
            Self for method chaining
        """
        for column, value in kwargs.items():
            if hasattr(self.model, column):
                self._filters.append(getattr(self.model, column) == value)
        return self
    
    def eager_load(self, *relationships: str) -> 'QueryBuilder':
        """
        Add eager loading for relationships.
        
        Args:
            *relationships: Relationship attribute names to eager load
            
        Returns:
            Self for method chaining
        """
        for rel in relationships:
            if hasattr(self.model, rel):
                self._eager_loads.append(joinedload(getattr(self.model, rel)))
        return self
    
    def selectin_load(self, *relationships: str) -> 'QueryBuilder':
        """
        Add selectin loading for relationships (better for one-to-many).
        
        Args:
            *relationships: Relationship attribute names to load via selectin
            
        Returns:
            Self for method chaining
        """
        for rel in relationships:
            if hasattr(self.model, rel):
                self._eager_loads.append(selectinload(getattr(self.model, rel)))
        return self
    
    def order_by(self, column: str, ascending: bool = True) -> 'QueryBuilder':
        """
        Add ordering to the query.
        
        Args:
            column: Column name to order by
            ascending: Sort in ascending order (True) or descending (False)
            
        Returns:
            Self for method chaining
        """
        if hasattr(self.model, column):
            col = getattr(self.model, column)
            # Store order_by separately to apply it during build
            if not hasattr(self, '_order_by'):
                self._order_by = []
            self._order_by.append((col, ascending))
        return self
    
    def limit(self, limit: int) -> 'QueryBuilder':
        """
        Limit the number of results.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            Self for method chaining
        """
        self._limit = limit
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        """
        Offset the results.
        
        Args:
            offset: Number of results to skip
            
        Returns:
            Self for method chaining
        """
        self._offset = offset
        return self
    
    def distinct(self) -> 'QueryBuilder':
        """
        Return only distinct results.
        
        Returns:
            Self for method chaining
        """
        self._distinct = True
        return self
    
    def build(self) -> Query:
        """
        Build and return the final query with all conditions applied.
        
        Returns:
            SQLAlchemy Query object
        """
        query = self.query
        
        # Apply filters first
        if self._filters:
            query = query.filter(and_(*self._filters))
        
        # Apply eager loads
        for eager_load in self._eager_loads:
            query = query.options(eager_load)
        
        # Apply ordering
        if hasattr(self, '_order_by'):
            for col, ascending in self._order_by:
                query = query.order_by(asc(col) if ascending else desc(col))
        
        # Apply distinct if needed
        if hasattr(self, '_distinct') and self._distinct:
            query = query.distinct()
        
        # Apply limit and offset last (after filters)
        if hasattr(self, '_limit'):
            query = query.limit(self._limit)
        if hasattr(self, '_offset'):
            query = query.offset(self._offset)
        
        return query
    
    def all(self) -> List[Any]:
        """Execute the query and return all results."""
        return self.build().all()
    
    def first(self) -> Optional[Any]:
        """Execute the query and return the first result."""
        return self.build().first()
    
    def one_or_none(self) -> Optional[Any]:
        """Execute the query and return exactly one result or None."""
        return self.build().one_or_none()
    
    def count(self) -> int:
        """Execute the query and return the count of results."""
        return self.build().count()
    
    def paginate(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Paginate the query results.
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Dictionary with paginated results and metadata
        """
        query = self.build()
        total = query.count()
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }


class RecipeQueryHelper:
    """Helper class for Recipe model queries."""
    
    @staticmethod
    def find_by_id(recipe_id: int) -> Optional[Recipe]:
        """Find a recipe by ID with eager-loaded relationships."""
        return QueryBuilder(Recipe)\
            .filter_by(id=recipe_id)\
            .eager_load('favourites')\
            .first()
    
    @staticmethod
    def search_recipes(search_term: str, age_group: Optional[str] = None,
                      limit: int = 50) -> List[Recipe]:
        """
        Search recipes by title or description.
        
        Args:
            search_term: Term to search for in title or description
            age_group: Optional age group to filter by
            limit: Maximum results to return
            
        Returns:
            List of matching recipes
        """
        builder = QueryBuilder(Recipe)\
            .filter(
                or_(
                    Recipe.title.ilike(f'%{search_term}%'),
                    Recipe.description.ilike(f'%{search_term}%')
                )
            )\
            .order_by('title', ascending=True)\
            .limit(limit)
        
        if age_group:
            builder.filter_by(age_group=age_group)
        
        return builder.all()
    
    @staticmethod
    def get_top_recipes(days: int = 7, limit: int = 10) -> List[Recipe]:
        """
        Get the most viewed recipes in the last N days.
        
        Args:
            days: Number of days to look back
            limit: Maximum results to return
            
        Returns:
            List of top recipes
        """
        from mod.datetime_utils import get_date_range
        
        start_date, end_date = get_date_range(days=days)
        
        return QueryBuilder(Recipe)\
            .filter(
                and_(
                    Recipe.last_viewed >= start_date,
                    Recipe.last_viewed <= end_date
                )
            )\
            .order_by('views', ascending=False)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_recipes_by_age_group(age_group: str, limit: int = 50) -> List[Recipe]:
        """
        Get recipes filtered by age group.
        
        Args:
            age_group: Age group to filter by
            limit: Maximum results to return
            
        Returns:
            List of recipes for the age group
        """
        return QueryBuilder(Recipe)\
            .filter_by(age_group=age_group)\
            .order_by('title', ascending=True)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_recipes_paginated(page: int = 1, per_page: int = 20,
                            age_group: Optional[str] = None) -> Dict[str, Any]:
        """
        Get paginated recipes.
        
        Args:
            page: Page number
            per_page: Items per page
            age_group: Optional age group filter
            
        Returns:
            Paginated results with metadata
        """
        builder = QueryBuilder(Recipe).order_by('title', ascending=True)
        
        if age_group:
            builder.filter_by(age_group=age_group)
        
        return builder.paginate(page=page, per_page=per_page)


class UserQueryHelper:
    """Helper class for Users model queries."""
    
    @staticmethod
    def find_by_id(user_id: int) -> Optional[Users]:
        """Find a user by ID with eager-loaded relationships."""
        return QueryBuilder(Users)\
            .filter_by(id=user_id)\
            .eager_load('favourites')\
            .first()
    
    @staticmethod
    def find_by_username(username: str) -> Optional[Users]:
        """Find a user by username."""
        return QueryBuilder(Users).filter_by(username=username).first()
    
    @staticmethod
    def find_by_email(email: str) -> Optional[Users]:
        """Find a user by email."""
        return QueryBuilder(Users).filter_by(email=email).first()
    
    @staticmethod
    def get_user_with_meal_plans(user_id: int) -> Optional[Users]:
        """Get a user with their meal plans eager-loaded."""
        return QueryBuilder(Users)\
            .filter_by(id=user_id)\
            .eager_load('meal_plans')\
            .first()


class FavouriteQueryHelper:
    """Helper class for Favourites model queries."""
    
    @staticmethod
    def get_user_favourites(user_id: int) -> List[Favourites]:
        """Get all favourites for a user."""
        user = db.session.query(Users).get(user_id)
        if not user:
            return []
        return user.favourites
    
    @staticmethod
    def user_has_favourite(user_id: int, recipe_id: int) -> bool:
        """Check if a user has a recipe as a favourite."""
        favorite = db.session.query(Favourites).filter(
            and_(
                Favourites.recipe_id == recipe_id,
                Favourites.users.any(id=user_id)
            )
        ).first()
        return favorite is not None
    
    @staticmethod
    def get_favourite_count_by_recipe(recipe_id: int) -> int:
        """Get the number of times a recipe is marked as favourite."""
        return db.session.query(func.count(Favourites.id))\
            .filter(Favourites.recipe_id == recipe_id)\
            .scalar() or 0


class MealPlanQueryHelper:
    """Helper class for MealPlan model queries."""
    
    @staticmethod
    def get_user_meal_plans(user_id: int) -> List[MealPlan]:
        """Get all meal plans for a user."""
        return QueryBuilder(MealPlan)\
            .filter_by(user_id=user_id)\
            .selectin_load('days')\
            .all()
    
    @staticmethod
    def get_meal_plan_with_recipes(meal_plan_id: int) -> Optional[MealPlan]:
        """Get a meal plan with all related recipes eager-loaded."""
        return QueryBuilder(MealPlan)\
            .filter_by(id=meal_plan_id)\
            .eager_load('days')\
            .first()
    
    @staticmethod
    def get_meal_plan_day(meal_plan_id: int, day: str) -> Optional[MealPlanDay]:
        """Get a specific day from a meal plan."""
        return db.session.query(MealPlanDay)\
            .filter(
                and_(
                    MealPlanDay.meal_plan_id == meal_plan_id,
                    MealPlanDay.day == day
                )
            )\
            .first()
    
    @staticmethod
    def get_meal_count_stats(user_id: int) -> Dict[str, int]:
        """Get statistics about a user's meal plans."""
        user = db.session.query(Users).get(user_id)
        if not user:
            return {'meal_plans': 0, 'meal_days': 0, 'recipes': 0}
        
        meal_plans = user.meal_plans
        meal_days = db.session.query(func.count(MealPlanDay.id))\
            .filter(MealPlanDay.meal_plan_id.in_([mp.id for mp in meal_plans]))\
            .scalar() or 0
        
        return {
            'meal_plans': len(meal_plans),
            'meal_days': meal_days,
            'recipes': len(set(r.id for mp in meal_plans for r in mp.recipes))
        }


# Convenience functions for common queries

def get_recipe_by_id(recipe_id: int) -> Optional[Recipe]:
    """Convenience function to get a recipe by ID."""
    return RecipeQueryHelper.find_by_id(recipe_id)


def search_recipes(search_term: str, **kwargs) -> List[Recipe]:
    """Convenience function to search recipes."""
    return RecipeQueryHelper.search_recipes(search_term, **kwargs)


def get_user_favourites(user_id: int) -> List[Favourites]:
    """Convenience function to get user's favourite recipes."""
    return FavouriteQueryHelper.get_user_favourites(user_id)


def get_user_meal_plans(user_id: int) -> List[MealPlan]:
    """Convenience function to get user's meal plans."""
    return MealPlanQueryHelper.get_user_meal_plans(user_id)


def count_user_meal_plans(user_id: int) -> int:
    """Convenience function to count a user's meal plans."""
    builder = QueryBuilder(MealPlan).filter_by(user_id=user_id)
    return builder.count()


def get_top_recipes_for_display(limit: int = 10) -> List[Recipe]:
    """Convenience function to get top recipes for homepage display."""
    return RecipeQueryHelper.get_top_recipes(days=30, limit=limit)
