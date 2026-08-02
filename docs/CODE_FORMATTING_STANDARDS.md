# Code Formatting Standards

This document defines the code formatting standards for the Growing Grubs Flask application to ensure consistency, readability, and maintainability across the codebase.

## Overview

We follow industry-standard Python formatting practices with tools to automate enforcement. These standards ensure:
- Consistent code style across all contributors
- Improved code readability
- Reduced cognitive load during code review
- Automated enforcement via pre-commit hooks

## Tools Used

- **Black**: Uncompromising code formatter (line length: 100 characters)
- **isort**: Import statement organizer
- **Flake8**: Style guide enforcement
- **mypy**: Static type checker (optional but recommended)

## Installation

Install development dependencies:

```bash
# In virtual environment
pip install -r requirements.txt
```

Or install formatting tools individually:

```bash
pip install black isort flake8 flake8-docstrings mypy
```

## Python Code Formatting

### Line Length

Maximum line length: **100 characters**

This is enforced by Black. Lines longer than 100 characters should be broken and properly indented.

### Indentation

- Use **4 spaces** per indentation level (never tabs)
- Align continuation lines with opening delimiter

Good:
```python
result = some_function(
    argument1,
    argument2,
    argument3
)
```

Bad:
```python
result = some_function(argument1,
                       argument2,
                       argument3)
```

### Imports

Organize imports in three groups (isort conventions):

1. **Standard library** imports
2. **Third-party** imports
3. **Local application** imports

Each group should be alphabetically sorted. Separate groups with a blank line.

Good:
```python
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import pytest
from flask import Flask, render_template
from sqlalchemy import Column, Integer, String

from mod import db
from mod.models import Recipe
```

Bad:
```python
from mod.models import Recipe
import logging
from flask import Flask
from mod import db
import asyncio
from typing import Dict, List
```

Use absolute imports, not relative imports:

Good:
```python
from mod.services import RecipeService
```

Bad:
```python
from .services import RecipeService
```

### Naming Conventions

#### Variables and Functions
- Use `snake_case` for variables and function names
- Use descriptive names (avoid single letters except for loop counters)

Good:
```python
user_recipes = get_user_recipes(user_id)
total_views = sum(recipe.views for recipe in recipes)
```

Bad:
```python
ur = get_user_recipes(user_id)
tv = sum(r.views for r in recipes)
```

#### Constants
- Use `UPPER_CASE` for constants

Good:
```python
MAX_RETRIES = 3
DEFAULT_PAGE_SIZE = 20
```

Bad:
```python
max_retries = 3
default_page_size = 20
```

#### Classes
- Use `PascalCase` for class names

Good:
```python
class RecipeService:
    pass

class UserNotFoundException(Exception):
    pass
```

Bad:
```python
class recipe_service:
    pass

class user_not_found_exception(Exception):
    pass
```

#### Private Methods/Attributes
- Prefix with single underscore `_` for internal use
- Prefix with double underscore `__` for name mangling (rare)

Good:
```python
def _private_helper():
    pass

def _calculate_score():
    pass
```

Bad:
```python
def private_helper():
    pass

def calculateScore():
    pass
```

### Whitespace

#### Blank Lines

- Two blank lines between top-level definitions (classes, functions)
- One blank line between method definitions in a class
- Use blank lines sparingly within functions

Good:
```python
class Recipe(db.Model):
    """Recipe model."""

    def get_title(self):
        """Get recipe title."""
        return self.title

    def get_ingredients(self):
        """Get recipe ingredients."""
        return self.ingredients


def search_recipes(query):
    """Search for recipes."""
    pass
```

#### Spacing Around Operators

- Space around binary operators: `=`, `==`, `!=`, `<`, `>`, `+`, `-`
- No space around keyword argument `=`
- No space inside brackets: `[`, `]`, `(`, `)`

Good:
```python
x = 5
if x == 5:
    result = x + 10

function_call(arg1, kwarg=value)
list_items = [1, 2, 3]
```

Bad:
```python
x=5
if x==5:
    result=x+10

function_call(arg1, kwarg = value)
list_items = [ 1, 2, 3 ]
```

### String Formatting

Use f-strings for string formatting (Python 3.6+):

Good:
```python
name = "Alice"
age = 30
message = f"User {name} is {age} years old"
```

Acceptable (for complex formatting):
```python
message = "User {} is {} years old".format(name, age)
```

Bad:
```python
message = "User %s is %d years old" % (name, age)
message = "User " + name + " is " + str(age) + " years old"
```

### Comments and Docstrings

#### Comments

- Use `#` for inline comments
- Separate inline comments from code with two spaces
- Keep comments updated with code changes

Good:
```python
x = x + 1  # Increment counter

# This is a block comment that explains
# the logic that follows
result = calculate_value()
```

Bad:
```python
x = x + 1  #increment counter
result = calculate_value()  # todo: fix this
```

#### Docstrings

Use Google-style docstrings for all public functions, methods, and classes:

Good:
```python
def search_recipes(query: str, limit: int = 50) -> List[Recipe]:
    """
    Search for recipes by query string.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of Recipe objects matching the query
        
    Raises:
        ValueError: If query is empty
    """
    if not query:
        raise ValueError("Query cannot be empty")
    return Recipe.query.filter(...).limit(limit).all()
```

## Running Formatters

### Format All Python Files

```bash
# Format with Black
black .

# Sort imports with isort
isort .

# Run both together
black . && isort .
```

### Format Specific Directory

```bash
black mod/
isort mod/
```

### Check Formatting Without Modifying

```bash
black --check .
isort --check-only .
```

### View Diffs

```bash
black --diff .
isort --diff .
```

## Linting

### Run Flake8

```bash
# Check all Python files
flake8

# Check specific directory
flake8 mod/

# Show statistics
flake8 --statistics
```

### Type Checking with mypy

```bash
# Type check all files
mypy mod/

# Type check specific file
mypy mod/models.py
```

## Configuration Files

### pyproject.toml

Black and isort configuration:

```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | __pycache__
  | \.pytest_cache
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_mode = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

### .flake8

Flake8 configuration:

```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,.venv,build,dist,.pytest_cache
ignore = E203,W503
docstring-convention = google
```

## Pre-commit Hooks

Setup automatic formatting on commit:

```bash
pip install pre-commit

# Install the pre-commit hooks
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/ambv/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
```

## IDE Configuration

### VS Code

Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--max-line-length=100"
  ],
  "python.linting.pylintEnabled": false,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  }
}
```

### PyCharm

Settings → Editor → Code Style → Python:
- Line length: 100
- Imports: Automatic grouping, Sort imports
- Tabs and Indents: Use spaces, 4 spaces per indent

## Common Issues and Solutions

### Issue: Black and isort Conflict

Sometimes Black and isort have different opinions on import formatting. Solution:

```bash
# Run isort first, then Black
isort .
black .
```

Or use compatible configurations (included in pyproject.toml above).

### Issue: Long Import Lines

If an import line exceeds 100 characters:

Good:
```python
from module import (
    function1,
    function2,
    function3,
    function4,
)
```

Bad:
```python
from module import function1, function2, function3, function4
```

### Issue: Long Function Definitions

If function signature exceeds 100 characters:

Good:
```python
def create_meal_plan(
    user_id: int,
    plan_name: str,
    recipes: List[Recipe],
    start_date: datetime,
) -> MealPlan:
    """Create a new meal plan."""
    pass
```

Bad:
```python
def create_meal_plan(user_id: int, plan_name: str, recipes: List[Recipe], start_date: datetime) -> MealPlan:
    """Create a new meal plan."""
    pass
```

## Code Review Checklist

When reviewing code, check:

- [ ] Line length doesn't exceed 100 characters
- [ ] Imports are properly organized and sorted
- [ ] Naming follows conventions (snake_case, PascalCase, UPPER_CASE)
- [ ] Indentation is consistent (4 spaces)
- [ ] Docstrings follow Google style
- [ ] No trailing whitespace
- [ ] Proper spacing around operators
- [ ] Comments are clear and necessary
- [ ] No commented-out code (unless explaining something)

## Continuous Integration

The repository runs formatters and linters in CI/CD:

```bash
# Code formatting check
black --check .
isort --check-only .

# Linting
flake8

# Type checking (optional)
mypy mod/
```

Failing checks will block pull requests.

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

## Exception Approval

Code that doesn't follow these standards requires explicit approval:

1. Add `# noqa` inline to suppress warnings (use sparingly)
2. Add `# type: ignore` for type checking exceptions
3. Add `# fmt: off` and `# fmt: on` to exclude from Black formatting

Example:
```python
# fmt: off
some_badly_formatted_dict = {
    'key1': 'value1',
    'key2': 'value2',
}
# fmt: on
```

Use exceptions sparingly and document the reason.
