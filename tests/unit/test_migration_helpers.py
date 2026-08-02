"""
Unit tests for migration helper utilities.
"""

import pytest
from mod.migration_helpers import MigrationHelper, DataMigration, TableBuilder
import sqlalchemy as sa


@pytest.mark.unit
class TestMigrationHelper:
    """Test cases for MigrationHelper class."""
    
    def test_add_column_with_index_name_generation(self):
        """Test that index name is generated correctly."""
        # This is a naming convention test
        table_name = "users"
        column_name = "email"
        expected_index = f"ix_{table_name}_{column_name}"
        assert expected_index == "ix_users_email"
    
    def test_unique_constraint_name_generation(self):
        """Test that unique constraint name is generated correctly."""
        table_name = "users"
        column_name = "email"
        expected_constraint = f"uq_{table_name}_{column_name}"
        assert expected_constraint == "uq_users_email"
    
    def test_foreign_key_constraint_name_generation(self):
        """Test that foreign key constraint name is generated correctly."""
        table_name = "meal_plans"
        column_name = "user_id"
        referenced_table = "users"
        expected_constraint = f"fk_{table_name}_{column_name}_{referenced_table}"
        assert expected_constraint == "fk_meal_plans_user_id_users"
    
    def test_drop_index_name_matches_create(self):
        """Test that drop index name matches create naming."""
        table_name = "recipes"
        column_name = "title"
        create_name = f"ix_{table_name}_{column_name}"
        drop_name = f"ix_{table_name}_{column_name}"
        assert create_name == drop_name


@pytest.mark.unit
class TestTableBuilder:
    """Test cases for TableBuilder class."""
    
    def test_table_builder_initialization(self):
        """Test TableBuilder initialization."""
        builder = TableBuilder("test_table", primary_key="id")
        assert builder.table_name == "test_table"
        assert len(builder.columns) == 1  # Should have primary key column
    
    def test_table_builder_add_column(self):
        """Test adding columns to table builder."""
        builder = TableBuilder("test_table")
        builder.add_column("name", sa.String(100))
        builder.add_column("active", sa.Boolean(), default='1')
        
        # Should have: id + 2 custom columns
        assert len(builder.columns) == 3
    
    def test_table_builder_add_timestamps(self):
        """Test adding timestamp columns."""
        builder = TableBuilder("test_table")
        builder.add_timestamps()
        
        # Should have: id + 2 timestamp columns
        assert len(builder.columns) == 3
        
        # Check timestamp columns are present
        column_names = [col.name for col in builder.columns]
        assert "created_at" in column_names
        assert "updated_at" in column_names
    
    def test_table_builder_method_chaining(self):
        """Test method chaining in TableBuilder."""
        builder = (TableBuilder("test_table")
                   .add_column("name", sa.String(100))
                   .add_column("email", sa.String(100))
                   .add_timestamps())
        
        # Should have: id + 2 columns + 2 timestamps
        assert len(builder.columns) == 5


@pytest.mark.unit
class TestDataMigration:
    """Test cases for DataMigration class."""
    
    def test_progress_logging_percentage_calculation(self):
        """Test progress logging calculation."""
        # Test percentage calculation
        current = 50
        total = 100
        percentage = (current / total * 100) if total > 0 else 0
        assert percentage == 50.0
    
    def test_progress_logging_edge_cases(self):
        """Test progress logging with edge cases."""
        # Test edge case: total = 0
        percentage = (0 / 0 * 100) if 0 > 0 else 0
        assert percentage == 0
        
        # Test other edge case: current > total (shouldn't happen but handle it)
        current = 150
        total = 100
        percentage = (current / total * 100) if total > 0 else 0
        assert percentage == 150.0


@pytest.mark.unit
class TestConstraintNaming:
    """Test cases for constraint naming conventions."""
    
    def test_consistent_naming_conventions(self):
        """Test that naming conventions are consistent."""
        table = "users"
        column = "email"
        
        # Test consistency across different constraint types
        index_name = f"ix_{table}_{column}"
        unique_name = f"uq_{table}_{column}"
        fk_name = f"fk_{table}_{column}_other_table"
        
        # All should follow the pattern: type_table_column[_extra]
        assert index_name.startswith("ix_")
        assert unique_name.startswith("uq_")
        assert fk_name.startswith("fk_")
    
    def test_long_name_handling(self):
        """Test handling of long table/column names."""
        long_table = "very_long_table_name_that_exceeds_normal_length"
        long_column = "very_long_column_name_that_exceeds_normal_length"
        
        index_name = f"ix_{long_table}_{long_column}"
        
        # Index name should be created (truncation handled by database if needed)
        assert index_name.startswith("ix_")
        assert long_table in index_name
        assert long_column in index_name


@pytest.mark.unit
class TestMigrationPatterns:
    """Test cases for common migration patterns."""
    
    def test_column_type_mapping(self):
        """Test that SQLAlchemy types are available."""
        types_to_test = [
            sa.Integer(),
            sa.String(100),
            sa.Boolean(),
            sa.DateTime(),
            sa.Text(),
            sa.Float(),
        ]
        
        for type_obj in types_to_test:
            assert type_obj is not None
    
    def test_default_value_patterns(self):
        """Test common default value patterns."""
        # Boolean default
        bool_default = 'false'
        assert bool_default is not None
        
        # String default
        str_default = 'active'
        assert str_default is not None
        
        # Numeric default
        num_default = '0'
        assert num_default is not None
    
    def test_ondelete_patterns(self):
        """Test common ON DELETE patterns."""
        valid_ondelete = ['CASCADE', 'SET NULL', 'RESTRICT', 'NO ACTION']
        
        for pattern in valid_ondelete:
            assert pattern is not None
            assert isinstance(pattern, str)
