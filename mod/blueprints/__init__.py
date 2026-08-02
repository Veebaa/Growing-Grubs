"""
Blueprints package for Growing Grubs application.

This package contains all Flask blueprints organized by functionality.
"""

from mod.blueprints.auth import auth_bp
from mod.blueprints.recipes import recipes_bp
from mod.blueprints.meal_planning import meal_planning_bp
from mod.blueprints.health import health_bp
from mod.blueprints.debug import debug_bp

__all__ = [
    'auth_bp',
    'recipes_bp',
    'meal_planning_bp',
    'health_bp',
    'debug_bp',
]
