"""
Business logic services for Growing Grubs.

This module contains service classes that encapsulate domain-specific business logic,
separating it from Flask route handlers for better testability and reusability.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import func, or_
from mod import db
from mod.models import Recipe, MealPlan, MealPlanDay, Favourites, Users
from mod.logging_config import get_logger
from mod.config import RECIPES_PER_PAGE

logger = get_logger(__name__)


class RecipeService:
    """Service for recipe-related operations."""
    
    @staticmethod
    def get_top_recipe_from_yesterday() -> Optional[Recipe]:
        """
        Get the most viewed recipe from yesterday.
        
        Falls back to the most viewed recipe of all time if none were viewed yesterday.
        
        Returns:
            Recipe: The top recipe, or None if no recipes exist
        """
        from mod.datetime_utils import get_yesterday_date
        
        yesterday_date = get_yesterday_date()
        top_recipe = Recipe.query.filter(
            func.date(Recipe.last_viewed) == yesterday_date
        ).order_by(Recipe.views.desc()).first()

        if not top_recipe:
            top_recipe = Recipe.query.order_by(Recipe.views.desc()).first()

        return top_recipe
    
    @staticmethod
    def increment_recipe_views(recipe: Recipe) -> None:
        """
        Increment the view count for a recipe.
        
        Args:
            recipe: The recipe to update
        """
        recipe.log_view()
        db.session.commit()
        logger.debug(f"Recipe {recipe.id} view count incremented")
    
    @staticmethod
    def search_recipes(keywords: List[str], page: int = 1) -> Dict[str, Any]:
        """
        Search recipes by keywords and return paginated results.
        
        Args:
            keywords: List of keywords to search for
            page: Page number for pagination
            
        Returns:
            Dict containing recipes and pagination info
        """
        recipes_query = Recipe.query
        
        if keywords:
            recipes_query = recipes_query.filter(
                or_(*(Recipe.age_group.ilike(f"%{kw}%") for kw in keywords))
            )
        
        pagination = recipes_query.order_by(Recipe.title.asc()).paginate(
            page=page, per_page=RECIPES_PER_PAGE, error_out=False
        )
        
        return {
            'recipes': pagination.items,
            'next_page': pagination.next_num if pagination.has_next else None,
            'prev_page': pagination.prev_num if pagination.has_prev else None,
            'current_page': page,
            'total_pages': pagination.pages,
        }


class FavouriteService:
    """Service for favorite recipe management."""
    
    @staticmethod
    def add_favourite(user: Users, recipe: Recipe) -> bool:
        """
        Add a recipe to user's favorites.
        
        Args:
            user: The user adding the favorite
            recipe: The recipe to favorite
            
        Returns:
            bool: True if successful, False if already favorited
        """
        # Check if already favorited
        existing = Favourites.query.filter_by(
            recipe_id=recipe.id
        ).first()
        
        if existing:
            logger.warning(f"Recipe {recipe.id} already in favorites for user {user.id}")
            return False
        
        try:
            favourite = Favourites(
                recipe_id=recipe.id,
                recipe_title=recipe.title,
                recipe_image=recipe.image_url or 'default.jpg'
            )
            user.favourites.append(favourite)
            db.session.commit()
            logger.info(f"Recipe {recipe.id} added to favorites for user {user.id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding favorite: {e}", exc_info=True)
            raise
    
    @staticmethod
    def remove_favourite(user: Users, recipe: Recipe) -> bool:
        """
        Remove a recipe from user's favorites.
        
        Args:
            user: The user removing the favorite
            recipe: The recipe to unfavorite
            
        Returns:
            bool: True if successful, False if not found
        """
        favourite = Favourites.query.filter_by(recipe_id=recipe.id).first()
        
        if not favourite:
            logger.warning(f"Favorite not found for recipe {recipe.id}")
            return False
        
        try:
            user.favourites.remove(favourite)
            db.session.commit()
            logger.info(f"Recipe {recipe.id} removed from favorites for user {user.id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing favorite: {e}", exc_info=True)
            raise


class MealPlanService:
    """Service for meal plan management."""
    
    @staticmethod
    def create_meal_plan(user: Users, name: str, meals_data: Dict[str, Dict[str, Any]]) -> MealPlan:
        """
        Create a new meal plan for a user.
        
        Args:
            user: The user creating the meal plan
            name: Name for the meal plan
            meals_data: Dictionary of meals organized by day and type
            
        Returns:
            MealPlan: The created meal plan
            
        Raises:
            ValueError: If meal plan creation fails
        """
        try:
            meal_plan = MealPlan(name=name, user=user)
            db.session.add(meal_plan)
            db.session.flush()
            
            # Collect all recipe IDs
            recipe_ids = set()
            for day_meals in meals_data.values():
                for meal_type in ['breakfast', 'lunch', 'dinner']:
                    if day_meals.get(meal_type):
                        recipe_ids.add(day_meals[meal_type])
            
            # Fetch recipes efficiently
            if recipe_ids:
                recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).all()
                for recipe in recipes:
                    meal_plan.recipes.append(recipe)
            
            # Create meal plan days
            for day_name, day_meals in meals_data.items():
                meal_plan_day = MealPlanDay(
                    day=day_name,
                    meal_plan_id=meal_plan.id,
                    breakfast_id=day_meals.get('breakfast'),
                    lunch_id=day_meals.get('lunch'),
                    dinner_id=day_meals.get('dinner')
                )
                db.session.add(meal_plan_day)
            
            db.session.commit()
            logger.info(f"Meal plan '{name}' created for user {user.id}")
            return meal_plan
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating meal plan: {e}", exc_info=True)
            raise ValueError(f"Failed to create meal plan: {str(e)}")
    
    @staticmethod
    def delete_meal_plan(meal_plan: MealPlan, user: Users) -> bool:
        """
        Delete a meal plan.
        
        Args:
            meal_plan: The meal plan to delete
            user: The user deleting the meal plan (for authorization)
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If user is not the owner
        """
        if meal_plan.user_id != user.id:
            logger.warning(f"Unauthorized meal plan deletion attempt by user {user.id}")
            raise ValueError("You do not have permission to delete this meal plan")
        
        try:
            db.session.delete(meal_plan)
            db.session.commit()
            logger.info(f"Meal plan {meal_plan.id} deleted by user {user.id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting meal plan: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_user_meal_plans(user: Users) -> List[MealPlan]:
        """
        Get all meal plans for a user with eager loading.
        
        Args:
            user: The user to get meal plans for
            
        Returns:
            List[MealPlan]: List of user's meal plans with related data loaded
        """
        return MealPlan.query.options(
            db.joinedload(MealPlan.days).joinedload(MealPlanDay.breakfast),
            db.joinedload(MealPlan.days).joinedload(MealPlanDay.lunch),
            db.joinedload(MealPlan.days).joinedload(MealPlanDay.dinner)
        ).filter_by(user_id=user.id).all()


class UserService:
    """Service for user-related operations."""
    
    @staticmethod
    def update_profile(user: Users, data: Dict[str, str]) -> None:
        """
        Update user profile information.
        
        Args:
            user: The user to update
            data: Dictionary containing updated profile fields
            
        Raises:
            ValueError: If update fails
        """
        try:
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.email = data.get('email', user.email)
            user.profile_image = data.get('profile_image', user.profile_image)
            
            db.session.commit()
            logger.info(f"Profile updated for user {user.id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile for user {user.id}: {e}", exc_info=True)
            raise ValueError(f"Failed to update profile: {str(e)}")
    
    @staticmethod
    def delete_account(user: Users) -> None:
        """
        Delete a user account.
        
        Args:
            user: The user account to delete
            
        Raises:
            ValueError: If deletion fails
        """
        try:
            db.session.delete(user)
            db.session.commit()
            logger.info(f"Account deleted for user {user.id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting account for user {user.id}: {e}", exc_info=True)
            raise ValueError(f"Failed to delete account: {str(e)}")
