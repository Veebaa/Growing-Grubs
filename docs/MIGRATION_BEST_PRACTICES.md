# Database Migration Best Practices

This document outlines best practices for managing database migrations in the Growing Grubs application using Alembic with Flask-Migrate.

## Overview

Database migrations allow you to version control changes to your database schema. This guide covers how to create, manage, and deploy migrations safely and effectively.

## Prerequisites

- Flask-Migrate (included in requirements.txt)
- Alembic (installed as dependency of Flask-Migrate)
- SQLAlchemy models defined in `mod/models.py`

## Creating Migrations

### Auto-generating Migrations

The recommended approach is to use Alembic's autogenerate feature:

```bash
# In the project root directory:
flask db migrate -m "descriptive message about the change"
```

This will:
1. Compare your current models with the database schema
2. Auto-generate a migration script with the detected changes
3. Save it in `migrations/versions/`

### Example: Adding a New Column

```python
# models.py
class Recipe(db.Model):
    # ... existing columns ...
    is_featured = db.Column(db.Boolean, default=False, index=True)  # New column
```

Generate migration:
```bash
flask db migrate -m "Add is_featured column to recipes"
```

### Manual Migrations

For complex changes that autogenerate doesn't handle well:

```bash
flask db revision --autogenerate -m "complex schema change"
```

Then manually edit the generated file in `migrations/versions/`.

## Migration File Structure

A typical migration file looks like:

```python
"""Add is_featured column to recipes.

Revision ID: 123abc456def
Revises: 789ghi012jkl
Create Date: 2024-08-01 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '123abc456def'
down_revision = '789ghi012jkl'
branch_labels = None
depends_on = None


def upgrade():
    """Apply the migration (forward)."""
    # Add new column
    op.add_column('recipes', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'))
    # Add index
    op.create_index('ix_recipes_is_featured', 'recipes', ['is_featured'])


def downgrade():
    """Undo the migration (backward)."""
    # Drop index
    op.drop_index('ix_recipes_is_featured', table_name='recipes')
    # Remove column
    op.drop_column('recipes', 'is_featured')
```

## Key Components

### Revision ID
- Unique identifier for each migration
- Auto-generated (e.g., `123abc456def`)
- Don't modify manually

### Dependencies
- `revision`: ID of this migration
- `down_revision`: ID of the previous migration
- Alembic uses this chain to determine order

### upgrade() Function
- Applied when running `flask db upgrade`
- Contains schema changes to apply
- Must be idempotent (safe to run multiple times)

### downgrade() Function
- Applied when running `flask db downgrade`
- Reverses the upgrade changes
- Allow rollback capability

## Running Migrations

### Apply All Pending Migrations

```bash
flask db upgrade
```

### Apply Specific Number of Migrations

```bash
# Apply next 2 migrations
flask db upgrade +2

# Downgrade to previous state
flask db downgrade -1
```

### Get Current Migration Status

```bash
flask db current
```

### View Migration History

```bash
flask db history
```

## Best Practices

### 1. **Write Clear Migration Messages**

Good:
```bash
flask db migrate -m "Add email_verified column and index to users table"
```

Bad:
```bash
flask db migrate -m "changes"
```

### 2. **Keep Migrations Focused**

Each migration should address one logical change:

```python
# Good: One migration per feature
# migration_001: Add user preferences table
# migration_002: Add email notifications column

# Avoid: Multiple unrelated changes in one migration
```

### 3. **Use Server Defaults for New Columns**

When adding non-nullable columns with existing data:

```python
def upgrade():
    op.add_column(
        'recipes',
        sa.Column('featured', sa.Boolean(), nullable=False, server_default='0')
    )
    # After data population, remove server_default in next migration
```

### 4. **Make Migrations Reversible**

Always implement both `upgrade()` and `downgrade()`:

```python
def upgrade():
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('new_table')
```

### 5. **Handle Data Migrations Carefully**

For migrations that involve data transformation:

```python
def upgrade():
    # Create new column
    op.add_column('users', sa.Column('full_name', sa.String(200)))
    
    # Populate from existing data
    connection = op.get_bind()
    connection.execute(
        text("UPDATE users SET full_name = CONCAT(first_name, ' ', last_name)")
    )
    
    # Now safe to make NOT NULL
    op.alter_column('users', 'full_name', nullable=False)

def downgrade():
    op.drop_column('users', 'full_name')
```

### 6. **Test Migrations Locally**

Before committing:

```bash
# Test upgrade
flask db upgrade

# Test downgrade
flask db downgrade

# Test upgrade again
flask db upgrade
```

### 7. **Index New Foreign Keys**

Always add indexes to foreign keys for performance:

```python
def upgrade():
    op.add_column('meal_plans', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_meal_plans_user_id', 'meal_plans', 'users', ['user_id'], ['id'])
    op.create_index('ix_meal_plans_user_id', 'meal_plans', ['user_id'])

def downgrade():
    op.drop_index('ix_meal_plans_user_id', table_name='meal_plans')
    op.drop_constraint('fk_meal_plans_user_id', 'meal_plans', type_='foreignkey')
    op.drop_column('meal_plans', 'user_id')
```

### 8. **Avoid Breaking Changes**

Try to make changes backwards compatible:

```python
# Good: Add optional column first
op.add_column('recipes', sa.Column('rating', sa.Float(), nullable=True))

# Later: Add index
# Even later: Make NOT NULL if needed (with default)

# Avoid: Removing columns that might be used
```

### 9. **Use Batch Operations for SQLite**

SQLite has limited ALTER TABLE support:

```python
from alembic import op
from sqlalchemy import String

def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email', existing_type=String(100), type_=String(200))

def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email', existing_type=String(200), type_=String(100))
```

### 10. **Add Comments to Complex Migrations**

```python
def upgrade():
    """
    This migration reorganizes the meal_plan_day table structure.
    
    Changes:
    - Moves meal type columns from wide to normal form
    - Creates new meal_item table for better normalization
    - Maintains data integrity through careful sequence
    """
    # Migration code...
```

## Common Migration Patterns

### Adding a New Table

```python
def upgrade():
    op.create_table('preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(20), default='light'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_preferences_user_id', 'preferences', ['user_id'])

def downgrade():
    op.drop_index('ix_preferences_user_id', table_name='preferences')
    op.drop_table('preferences')
```

### Adding a Column with Constraint

```python
def upgrade():
    op.add_column('recipes', sa.Column('category', sa.String(50), nullable=False, server_default='general'))
    op.create_index('ix_recipes_category', 'recipes', ['category'])

def downgrade():
    op.drop_index('ix_recipes_category', table_name='recipes')
    op.drop_column('recipes', 'category')
```

### Renaming a Column

```python
def upgrade():
    op.alter_column('users', 'email_addr', new_column_name='email')

def downgrade():
    op.alter_column('users', 'email', new_column_name='email_addr')
```

## Troubleshooting

### Issue: "Could not locate the target database"

Solution: Ensure database connection is configured in `.env`:
```bash
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### Issue: "Alembic stamp command errors"

If migrations are out of sync:
```bash
# View current stamp
flask db current

# Reset to specific migration
flask db stamp 123abc456def
```

### Issue: "Migration conflicts"

When working in teams with conflicting migrations:

1. Identify the conflicting migrations
2. Rename one with higher ID
3. Update dependencies
4. Test thoroughly

### Issue: "Data lost after downgrade"

Always implement proper `downgrade()` functions. For destructive changes, consider:
- Creating backups before deployment
- Having a separate data archive table
- Testing downgrades in staging first

## Migration Workflow

### For Development

```bash
# Make model changes
# Create migration
flask db migrate -m "descriptive message"

# Review generated migration file
cat migrations/versions/[new_migration].py

# Test migration
flask db upgrade
flask db downgrade
flask db upgrade

# Commit changes
git add mod/models.py migrations/versions/[new_migration].py
git commit -m "Add [feature] with migration"
```

### For Staging/Production

```bash
# Pull latest code
git pull

# Review pending migrations
flask db history

# Create backup
pg_dump dbname > backup_$(date +%Y%m%d_%H%M%S).sql

# Apply migrations
flask db upgrade

# Verify migration success
flask db current

# Run application tests
pytest
```

## Emergency: Rollback a Migration

```bash
# View migration history
flask db history

# Downgrade to previous migration
flask db downgrade -1

# Or downgrade to specific migration
flask db downgrade 123abc456def
```

## Performance Considerations

### Indexes on Large Tables

```python
# Add index concurrently on PostgreSQL
op.execute('CREATE INDEX CONCURRENTLY idx_name ON table_name (column_name);')
```

### Large Data Migrations

For tables with millions of rows:

```python
# Use batch processing to avoid locking
def upgrade():
    connection = op.get_bind()
    
    # Process in chunks
    batch_size = 1000
    offset = 0
    
    while True:
        rows = connection.execute(
            text("SELECT id FROM large_table LIMIT :limit OFFSET :offset"),
            {"limit": batch_size, "offset": offset}
        )
        
        if not rows:
            break
        
        # Process batch...
        offset += batch_size
```

## Version Control

### DO

- Commit migration files with model changes
- Use descriptive commit messages
- Tag releases that include migrations
- Document migration breaking changes

### DON'T

- Manually edit migration files after application runs
- Delete migration files
- Modify revision IDs
- Run migrations outside version control

## See Also

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [SQLAlchemy Migrations](https://docs.sqlalchemy.org/en/latest/orm/examples.html)
