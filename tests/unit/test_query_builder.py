"""
Unit tests for SQLAlchemy query builder helpers.
"""

import pytest
from mod.models import Users, Recipe, MealPlan, MealPlanDay
from mod.query_builder import (
    QueryBuilder, RecipeQueryHelper, UserQueryHelper, 
    FavouriteQueryHelper, MealPlanQueryHelper,
    get_recipe_by_id, search_recipes, get_user_favourites,
    get_user_meal_plans, count_user_meal_plans, get_top_recipes_for_display
)
from mod import db


@pytest.mark.unit
class TestQueryBuilder:
    """Test cases for QueryBuilder class."""
    
    def test_query_builder_initialization(self, app):
        """Test QueryBuilder initialization."""
        with app.app_context():
            builder = QueryBuilder(Recipe)
            assert builder.model == Recipe
            assert builder.query is not None
    
    def test_filter_by(self, app):
        """Test filter_by method."""
        with app.app_context():
            recipe = Recipe(title='Test Recipe', description='Test', age_group='1-3 years', method='Mix')
            db.session.add(recipe)
            db.session.commit()
            recipe_id = recipe.id
            
            builder = QueryBuilder(Recipe).filter_by(id=recipe_id)
            result = builder.first()
            assert result is not None
            assert result.id == recipe_id
    
    def test_order_by_ascending(self, app):
        """Test order_by method in ascending order."""
        with app.app_context():
            # Create multiple recipes
            r1 = Recipe(title='Apple Pie', description='Test', age_group='1-3 years', method='Mix and bake')
            r2 = Recipe(title='Banana Bread', description='Test', age_group='1-3 years', method='Mix and bake')
            db.session.add_all([r1, r2])
            db.session.commit()
            
            builder = QueryBuilder(Recipe).order_by('title', ascending=True)
            results = builder.all()
            assert results[0].title == 'Apple Pie'
            assert results[1].title == 'Banana Bread'
    
    def test_order_by_descending(self, app):
        """Test order_by method in descending order."""
        with app.app_context():
            # Create multiple recipes
            r1 = Recipe(title='Apple Pie', description='Test', age_group='1-3 years', method='Mix and bake')
            r2 = Recipe(title='Banana Bread', description='Test', age_group='1-3 years', method='Mix and bake')
            db.session.add_all([r1, r2])
            db.session.commit()
            
            builder = QueryBuilder(Recipe).order_by('title', ascending=False)
            results = builder.all()
            assert results[0].title == 'Banana Bread'
            assert results[1].title == 'Apple Pie'
    
    def test_limit(self, app):
        """Test limit method."""
        with app.app_context():
            for i in range(5):
                recipe = Recipe(title=f'Recipe {i}', description='Test', age_group='1-3 years', method='Mix')
                db.session.add(recipe)
            db.session.commit()
            
            builder = QueryBuilder(Recipe).limit(2)
            results = builder.all()
            assert len(results) == 2
    
    def test_offset(self, app):
        """Test offset method."""
        with app.app_context():
            for i in range(5):
                recipe = Recipe(title=f'Recipe {i}', description='Test', age_group='1-3 years', method='Mix')
                db.session.add(recipe)
            db.session.commit()
            
            builder = QueryBuilder(Recipe)\
                .order_by('id', ascending=True)\
                .offset(2)\
                .limit(2)
            results = builder.all()
            assert len(results) == 2
    
    def test_count(self, app):
        """Test count method."""
        with app.app_context():
            for i in range(5):
                recipe = Recipe(title=f'Recipe {i}', description='Test', age_group='1-3 years', method='Mix')
                db.session.add(recipe)
            db.session.commit()
            
            builder = QueryBuilder(Recipe)
            count = builder.count()
            assert count == 5
    
    def test_paginate(self, app):
        """Test paginate method."""
        with app.app_context():
            for i in range(10):
                recipe = Recipe(title=f'Recipe {i}', description='Test', age_group='1-3 years', method='Mix')
                db.session.add(recipe)
            db.session.commit()
            
            builder = QueryBuilder(Recipe)
            result = builder.paginate(page=1, per_page=3)
            assert result['page'] == 1
            assert result['per_page'] == 3
            assert result['total'] == 10
            assert len(result['items']) == 3


@pytest.mark.unit
class TestRecipeQueryHelper:
    """Test cases for RecipeQueryHelper class."""
    
    def test_find_by_id(self, app):
        """Test find_by_id method."""
        with app.app_context():
            recipe = Recipe(title='Test Recipe', description='Test', age_group='1-3 years', method='Mix')
            db.session.add(recipe)
            db.session.commit()
            recipe_id = recipe.id
            
            result = RecipeQueryHelper.find_by_id(recipe_id)
            assert result is not None
            assert result.id == recipe_id
    
    def test_search_recipes(self, app):
        """Test search_recipes method."""
        with app.app_context():
            r1 = Recipe(title='Healthy Apple Pie', description='Nutritious', age_group='1-3 years', method='Bake')
            r2 = Recipe(title='Banana Bread', description='Test', age_group='1-3 years', method='Bake')
            db.session.add_all([r1, r2])
            db.session.commit()
            
            results = RecipeQueryHelper.search_recipes('apple')
            assert len(results) > 0
            assert any('apple' in r.title.lower() for r in results)
    
    def test_get_recipes_by_age_group(self, app):
        """Test get_recipes_by_age_group method."""
        with app.app_context():
            r1 = Recipe(title='Baby Food', description='Test', age_group='0-1 years', method='Blend')
            r2 = Recipe(title='Toddler Food', description='Test', age_group='1-3 years', method='Blend')
            db.session.add_all([r1, r2])
            db.session.commit()
            
            results = RecipeQueryHelper.get_recipes_by_age_group('1-3 years')
            assert all(r.age_group == '1-3 years' for r in results)
    
    def test_get_recipes_paginated(self, app):
        """Test get_recipes_paginated method."""
        with app.app_context():
            for i in range(25):
                recipe = Recipe(title=f'Recipe {i}', description='Test', age_group='1-3 years', method='Mix')
                db.session.add(recipe)
            db.session.commit()
            
            result = RecipeQueryHelper.get_recipes_paginated(page=1, per_page=10)
            assert result['page'] == 1
            assert result['per_page'] == 10
            assert result['total'] == 25
            assert len(result['items']) == 10


@pytest.mark.unit
class TestUserQueryHelper:
    """Test cases for UserQueryHelper class."""
    
    def test_find_by_id(self, app):
        """Test find_by_id method."""
        with app.app_context():
            user = Users(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                profile_image='default.jpg'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            result = UserQueryHelper.find_by_id(user_id)
            assert result is not None
            assert result.id == user_id
    
    def test_find_by_username(self, app):
        """Test find_by_username method."""
        with app.app_context():
            user = Users(
                username='queryuser',
                email='query@example.com',
                first_name='Query',
                last_name='User',
                profile_image='default.jpg'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            result = UserQueryHelper.find_by_username('queryuser')
            assert result is not None
            assert result.username == 'queryuser'
    
    def test_find_by_email(self, app):
        """Test find_by_email method."""
        with app.app_context():
            user = Users(
                username='emailuser',
                email='email@example.com',
                first_name='Email',
                last_name='User',
                profile_image='default.jpg'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            result = UserQueryHelper.find_by_email('email@example.com')
            assert result is not None
            assert result.email == 'email@example.com'


@pytest.mark.unit
class TestMealPlanQueryHelper:
    """Test cases for MealPlanQueryHelper class."""
    
    def test_get_user_meal_plans(self, app):
        """Test get_user_meal_plans method."""
        with app.app_context():
            user = Users(
                username='mealuser',
                email='meal@example.com',
                first_name='Meal',
                last_name='User',
                profile_image='default.jpg'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()
            user_id = user.id
            
            recipe = Recipe(title='Test Recipe', description='Test', age_group='1-3 years', method='Mix')
            db.session.add(recipe)
            db.session.flush()
            
            mp = MealPlan(name='Test Plan', user_id=user_id)
            db.session.add(mp)
            db.session.flush()
            
            mpd = MealPlanDay(day='Monday', meal_plan_id=mp.id, breakfast_id=recipe.id)
            db.session.add(mpd)
            db.session.commit()
            
            results = MealPlanQueryHelper.get_user_meal_plans(user_id)
            assert len(results) > 0
            assert results[0].user_id == user_id
    
    def test_get_meal_count_stats(self, app):
        """Test get_meal_count_stats method."""
        with app.app_context():
            user = Users(
                username='statsuser',
                email='stats@example.com',
                first_name='Stats',
                last_name='User',
                profile_image='default.jpg'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()
            user_id = user.id
            
            recipe = Recipe(title='Test Recipe', description='Test', age_group='1-3 years', method='Mix')
            db.session.add(recipe)
            db.session.flush()
            
            mp = MealPlan(name='Test Plan', user_id=user_id)
            db.session.add(mp)
            db.session.flush()
            
            mpd = MealPlanDay(day='Monday', meal_plan_id=mp.id, breakfast_id=recipe.id)
            db.session.add(mpd)
            db.session.commit()
            
            stats = MealPlanQueryHelper.get_meal_count_stats(user_id)
            assert stats['meal_plans'] > 0
            assert stats['meal_days'] > 0


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def test_get_recipe_by_id(self, app):
        """Test get_recipe_by_id function."""
        with app.app_context():
            recipe = Recipe(title='Test Recipe', description='Test', age_group='1-3 years', method='Mix')
            db.session.add(recipe)
            db.session.commit()
            recipe_id = recipe.id
            
            result = get_recipe_by_id(recipe_id)
            assert result is not None
            assert result.id == recipe_id
    
    def test_search_recipes_function(self, app):
        """Test search_recipes convenience function."""
        with app.app_context():
            recipe = Recipe(title='Test Recipe', description='Healthy', age_group='1-3 years', method='Mix')
            db.session.add(recipe)
            db.session.commit()
            
            results = search_recipes('test')
            assert len(results) > 0
    
    def test_count_user_meal_plans(self, app):
        """Test count_user_meal_plans function."""
        with app.app_context():
            user = Users(
                username='countuser',
                email='count@example.com',
                first_name='Count',
                last_name='User',
                profile_image='default.jpg'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            recipe = Recipe(title='Test Recipe', description='Test', age_group='1-3 years', method='Mix')
            db.session.add(recipe)
            db.session.commit()
            
            mp = MealPlan(name='Test Plan', user_id=user_id)
            db.session.add(mp)
            db.session.commit()
            
            count = count_user_meal_plans(user_id)
            assert count > 0
