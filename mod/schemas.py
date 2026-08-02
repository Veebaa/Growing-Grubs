"""
Pydantic schemas for data validation.

This module defines data validation schemas for request/response data,
user input, and internal data transfers using Pydantic.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from mod.config import VALIDATION_CONSTRAINTS


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    username: str = Field(
        ...,
        min_length=VALIDATION_CONSTRAINTS['username']['min'],
        max_length=VALIDATION_CONSTRAINTS['username']['max'],
        description="Username for the account"
    )
    first_name: str = Field(
        ...,
        min_length=VALIDATION_CONSTRAINTS['first_name']['min'],
        max_length=VALIDATION_CONSTRAINTS['first_name']['max'],
        description="User's first name"
    )
    last_name: str = Field(
        ...,
        min_length=VALIDATION_CONSTRAINTS['last_name']['min'],
        max_length=VALIDATION_CONSTRAINTS['last_name']['max'],
        description="User's last name"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class UserRegister(UserBase):
    """Schema for user registration."""
    
    email: EmailStr = Field(
        ...,
        max_length=VALIDATION_CONSTRAINTS['email']['max'],
        description="Email address"
    )
    password: str = Field(
        ...,
        min_length=VALIDATION_CONSTRAINTS['password']['min'],
        max_length=VALIDATION_CONSTRAINTS['password']['max'],
        description="Password"
    )
    confirm_password: str = Field(
        ...,
        min_length=VALIDATION_CONSTRAINTS['password']['min'],
        description="Password confirmation"
    )
    profile_image: str = Field(
        default='default.jpg',
        description="Profile image filename"
    )
    
    @model_validator(mode='after')
    def passwords_match(self) -> 'UserRegister':
        """Validate that passwords match."""
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class UserLogin(BaseModel):
    """Schema for user login."""
    
    username: str = Field(
        ...,
        min_length=VALIDATION_CONSTRAINTS['username']['min'],
        max_length=VALIDATION_CONSTRAINTS['username']['max'],
        description="Username"
    )
    password: str = Field(
        ...,
        description="Password"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    
    first_name: Optional[str] = Field(
        default=None,
        min_length=VALIDATION_CONSTRAINTS['first_name']['min'],
        max_length=VALIDATION_CONSTRAINTS['first_name']['max'],
        description="User's first name"
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=VALIDATION_CONSTRAINTS['last_name']['min'],
        max_length=VALIDATION_CONSTRAINTS['last_name']['max'],
        description="User's last name"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        max_length=VALIDATION_CONSTRAINTS['email']['max'],
        description="Email address"
    )
    profile_image: Optional[str] = Field(
        default=None,
        description="Profile image filename"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class UserResponse(UserBase):
    """Schema for user response data."""
    
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    profile_image: str = Field(..., description="Profile image filename")
    created_at: Optional[datetime] = Field(default=None, description="Account creation date")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


# ============================================================================
# Recipe Schemas
# ============================================================================

class RecipeBase(BaseModel):
    """Base recipe schema."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Recipe title"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Recipe description"
    )
    age_group: str = Field(
        ...,
        description="Age group the recipe is suitable for"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class RecipeCreate(RecipeBase):
    """Schema for creating a recipe."""
    
    ingredients: Optional[List[str]] = Field(
        default=None,
        description="List of ingredients"
    )
    instructions: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Cooking instructions"
    )


class RecipeUpdate(BaseModel):
    """Schema for updating a recipe."""
    
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Recipe title"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Recipe description"
    )
    age_group: Optional[str] = Field(
        default=None,
        description="Age group"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class RecipeResponse(RecipeBase):
    """Schema for recipe response data."""
    
    id: int = Field(..., description="Recipe ID")
    views: int = Field(default=0, description="View count")
    last_viewed: Optional[datetime] = Field(default=None, description="Last viewed time")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


# ============================================================================
# Meal Plan Schemas
# ============================================================================

class MealChoice(BaseModel):
    """Schema for a single meal choice."""
    
    day: str = Field(..., description="Day of the week")
    meal_type: str = Field(..., description="Type of meal (breakfast, lunch, dinner)")
    recipe_id: int = Field(..., description="Recipe ID")
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class MealPlanCreate(BaseModel):
    """Schema for creating a meal plan."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Meal plan name"
    )
    meals: List[MealChoice] = Field(
        ...,
        min_length=1,
        description="List of meal choices"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class MealPlanUpdate(BaseModel):
    """Schema for updating a meal plan."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Meal plan name"
    )
    meals: Optional[List[MealChoice]] = Field(
        default=None,
        min_length=1,
        description="List of meal choices"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class MealPlanResponse(BaseModel):
    """Schema for meal plan response data."""
    
    id: int = Field(..., description="Meal plan ID")
    name: str = Field(..., description="Meal plan name")
    user_id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: Optional[datetime] = Field(default=None, description="Last update date")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


# ============================================================================
# Search Schemas
# ============================================================================

class SearchQuery(BaseModel):
    """Schema for search queries."""
    
    query: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Search query"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number"
    )
    limit: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Results per page"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class SearchResult(BaseModel):
    """Schema for search results."""
    
    id: int = Field(..., description="Result ID")
    title: str = Field(..., description="Result title")
    description: Optional[str] = Field(default=None, description="Result description")
    type: str = Field(..., description="Result type")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class SearchResponse(BaseModel):
    """Schema for paginated search response."""
    
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total results count")
    page: int = Field(..., description="Current page")
    pages: int = Field(..., description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")


# ============================================================================
# Pagination Schemas
# ============================================================================

class PaginationQuery(BaseModel):
    """Schema for pagination parameters."""
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number"
    )
    per_page: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Items per page"
    )


class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    
    items: List[Dict[str, Any]] = Field(..., description="Page items")
    total: int = Field(..., description="Total items")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorDetail(BaseModel):
    """Schema for error details."""
    
    loc: List[str] = Field(..., description="Error location")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    validation_errors: Optional[List[ErrorDetail]] = Field(default=None, description="Validation errors")


# ============================================================================
# Generic Response Schemas
# ============================================================================

class SuccessResponse(BaseModel):
    """Schema for successful responses."""
    
    success: bool = Field(default=True, description="Success flag")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")


class ListResponse(BaseModel):
    """Schema for list responses."""
    
    items: List[Dict[str, Any]] = Field(..., description="List of items")
    count: int = Field(..., description="Total count")


# ============================================================================
# Favourite Schemas
# ============================================================================

class FavouriteCreate(BaseModel):
    """Schema for adding a favourite."""
    
    recipe_id: int = Field(..., description="Recipe ID to favourite")


class FavouriteResponse(BaseModel):
    """Schema for favourite response."""
    
    id: int = Field(..., description="Favourite ID")
    user_id: int = Field(..., description="User ID")
    recipe_id: int = Field(..., description="Recipe ID")
    created_at: datetime = Field(..., description="Creation date")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
