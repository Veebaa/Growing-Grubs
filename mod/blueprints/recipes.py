"""
Recipe-related routes.

This module contains routes for viewing, searching, and managing recipes.
"""

from flask import Blueprint
from mod.logging_config import get_logger

logger = get_logger(__name__)

# Create recipes blueprint
recipes_bp = Blueprint(
    'recipes',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)


# Recipe routes would be implemented here
# This is a placeholder for the blueprint structure
