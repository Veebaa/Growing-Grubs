"""
Health and main application routes.

This module contains the main application routes including home, health check,
and other general-purpose pages.
"""

from typing import Optional, Dict, Any, List
from flask import Blueprint, render_template, current_app
from flask_login import current_user

from mod.logging_config import get_logger
from mod.services import RecipeService
from mod.config import NHS_ARTICLES_TO_FETCH, NHS_API_PARAMS
from mod.api_client import APIClient, RateLimiter
import os

logger = get_logger(__name__)

# Create health blueprint
health_bp = Blueprint(
    'health',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)


@health_bp.route('/healthz')
def health_check():
    """
    Health check endpoint.
    
    Returns:
        OK status
    """
    return "OK", 200


@health_bp.route('/')
def index():
    """
    Display home page with featured recipe.
    
    Returns:
        Rendered index template
    """
    try:
        # Get top recipe from yesterday
        recipe = RecipeService.get_top_recipe_from_yesterday()
        
        # Get health topics
        topics = get_topics_logic()
        
        return render_template(
            'index.html',
            title='Home',
            recipe=recipe,
            topics=topics,
            user=current_user
        )
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return render_template('index.html', title='Home', recipe=None, topics=[], user=current_user)


@health_bp.route('/sitemap')
def sitemap():
    """
    Display site map.
    
    Returns:
        Rendered site map template
    """
    return render_template('site_map.html', title='Site Map')


@health_bp.route('/404')
def not_found_error(e):
    """
    Handle 404 errors.
    
    Args:
        e: Exception object
        
    Returns:
        404 error template
    """
    logger.warning(f"404 Not Found: {e}")
    return render_template('404.html'), 404


def get_topics_logic() -> List[Dict[str, str]]:
    """
    Fetch health topics from NHS API with rate limiting and retries.
    
    Returns:
        List of health topics or empty list on error
    """
    api_key = os.getenv('NHS_API_KEY')
    if not api_key:
        logger.error("NHS_API_KEY is missing!")
        return []

    endpoint = "https://sandbox.api.service.nhs.uk/nhs-website-content/conditions"

    headers = {
        "accept": "application/json",
        "apikey": api_key
    }

    try:
        # Use APIClient with rate limiting
        rate_limiter = RateLimiter(requests_per_second=1.0, max_retries=3)
        
        with APIClient(timeout=10, max_retries=3) as client:
            response = client.get(
                endpoint,
                headers=headers,
                params=NHS_API_PARAMS,
                rate_limiter=rate_limiter
            )
        
        if not response:
            logger.error("Failed to get response from NHS API after retries")
            return []
        
        data = response.json()

        logger.info(f"Keys in API Response: {data.keys()}")

        # Extract articles from response
        articles = []
        for item in data.get("significantLink", []):
            name = item.get("name", "No Title")
            description = item.get("description", "No Description")
            url = item.get("url", "#")
            articles.append({"name": name, "description": description, "url": url})

        logger.info(f"Fetched {len(articles)} articles from NHS API.")

        import random
        return random.sample(articles, NHS_ARTICLES_TO_FETCH) if len(articles) >= NHS_ARTICLES_TO_FETCH else articles

    except Exception as e:
        logger.error(f"Error fetching data from NHS API: {e}", exc_info=True)
        return []
