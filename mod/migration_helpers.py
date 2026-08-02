"""
Helper utilities for database migrations with Alembic.

This module provides convenience functions and patterns for creating
robust and maintainable database migrations.
"""

from alembic import op
import sqlalchemy as sa
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MigrationHelper:
    """Helper class for common migration operations."""
    
    @staticmethod
    def add_column_with_index(
        table_name: str,
        column_name: str,
        column_type: sa.types.TypeEngine,
        nullable: bool = True,
        server_default: Optional[str] = None,
        index: bool = False,
        unique: bool = False
    ) -> None:
        """
        Add a column to a table with optional index and uniqueness.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to add
            column_type: SQLAlchemy column type
            nullable: Whether column allows NULL values
            server_default: Default value for existing rows
            index: Whether to create an index on this column
            unique: Whether the column should be unique
        """
        # Create column
        op.add_column(
            table_name,
            sa.Column(
                column_name,
                column_type,
                nullable=nullable,
                server_default=server_default
            )
        )
        
        # Create index if requested
        if index:
            index_name = f"ix_{table_name}_{column_name}"
            op.create_index(index_name, table_name, [column_name])
        
        # Create unique constraint if requested
        if unique:
            constraint_name = f"uq_{table_name}_{column_name}"
            op.create_unique_constraint(constraint_name, table_name, [column_name])
        
        logger.info(f"Added column {table_name}.{column_name}")
    
    @staticmethod
    def drop_column_with_index(
        table_name: str,
        column_name: str,
        index: bool = False,
        unique: bool = False
    ) -> None:
        """
        Drop a column from a table, removing associated indexes and constraints.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to drop
            index: Whether to drop index on this column
            unique: Whether to drop unique constraint
        """
        # Drop index if exists
        if index:
            index_name = f"ix_{table_name}_{column_name}"
            try:
                op.drop_index(index_name, table_name=table_name)
            except Exception:
                logger.warning(f"Index {index_name} not found")
        
        # Drop unique constraint if exists
        if unique:
            constraint_name = f"uq_{table_name}_{column_name}"
            try:
                op.drop_constraint(constraint_name, table_name)
            except Exception:
                logger.warning(f"Constraint {constraint_name} not found")
        
        # Drop column
        op.drop_column(table_name, column_name)
        logger.info(f"Dropped column {table_name}.{column_name}")
    
    @staticmethod
    def add_foreign_key(
        table_name: str,
        column_name: str,
        referenced_table: str,
        referenced_column: str = 'id',
        constraint_name: Optional[str] = None,
        index: bool = True,
        ondelete: Optional[str] = None
    ) -> None:
        """
        Add a foreign key constraint to a column.
        
        Args:
            table_name: Table containing the foreign key
            column_name: Column that references another table
            referenced_table: Table being referenced
            referenced_column: Column being referenced (default: 'id')
            constraint_name: Custom constraint name
            index: Whether to create index on foreign key
            ondelete: ON DELETE action (CASCADE, SET NULL, etc.)
        """
        if constraint_name is None:
            constraint_name = f"fk_{table_name}_{column_name}_{referenced_table}"
        
        # Create foreign key constraint
        op.create_foreign_key(
            constraint_name,
            table_name,
            referenced_table,
            [column_name],
            [referenced_column],
            ondelete=ondelete
        )
        
        # Create index for better query performance
        if index:
            index_name = f"ix_{table_name}_{column_name}"
            op.create_index(index_name, table_name, [column_name])
        
        logger.info(f"Added foreign key {table_name}.{column_name} -> {referenced_table}.{referenced_column}")
    
    @staticmethod
    def drop_foreign_key(
        table_name: str,
        column_name: str,
        constraint_name: Optional[str] = None,
        index: bool = True
    ) -> None:
        """
        Drop a foreign key constraint.
        
        Args:
            table_name: Table containing the foreign key
            column_name: Column with the foreign key
            constraint_name: Custom constraint name
            index: Whether to drop associated index
        """
        if constraint_name is None:
            constraint_name = f"fk_{table_name}_{column_name}"
        
        # Drop index if exists
        if index:
            index_name = f"ix_{table_name}_{column_name}"
            try:
                op.drop_index(index_name, table_name=table_name)
            except Exception:
                logger.warning(f"Index {index_name} not found")
        
        # Drop foreign key
        try:
            op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        except Exception:
            logger.warning(f"Constraint {constraint_name} not found")
        
        logger.info(f"Dropped foreign key {constraint_name}")
    
    @staticmethod
    def rename_column(
        table_name: str,
        old_name: str,
        new_name: str
    ) -> None:
        """
        Rename a column in a table.
        
        Args:
            table_name: Name of the table
            old_name: Current column name
            new_name: New column name
        """
        op.alter_column(table_name, old_name, new_column_name=new_name)
        logger.info(f"Renamed {table_name}.{old_name} to {new_name}")
    
    @staticmethod
    def rename_table(
        old_name: str,
        new_name: str
    ) -> None:
        """
        Rename a table.
        
        Args:
            old_name: Current table name
            new_name: New table name
        """
        op.rename_table(old_name, new_name)
        logger.info(f"Renamed table {old_name} to {new_name}")
    
    @staticmethod
    def create_table_with_timestamps(
        table_name: str,
        columns: List[tuple],
        primary_key: str = 'id'
    ) -> None:
        """
        Create a new table with standard id and timestamp columns.
        
        Args:
            table_name: Name of the table to create
            columns: List of (column_name, column_type, nullable, default) tuples
            primary_key: Name of the primary key column
        """
        table_args = [sa.Column(primary_key, sa.Integer(), nullable=False, primary_key=True)]
        
        # Add custom columns
        for col_spec in columns:
            if len(col_spec) == 2:
                col_name, col_type = col_spec
                table_args.append(sa.Column(col_name, col_type))
            elif len(col_spec) == 3:
                col_name, col_type, nullable = col_spec
                table_args.append(sa.Column(col_name, col_type, nullable=nullable))
            elif len(col_spec) == 4:
                col_name, col_type, nullable, default = col_spec
                table_args.append(sa.Column(col_name, col_type, nullable=nullable, server_default=default))
        
        # Add timestamps
        table_args.append(sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()))
        table_args.append(sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()))
        
        op.create_table(table_name, *table_args)
        logger.info(f"Created table {table_name}")
    
    @staticmethod
    def batch_update_data(
        table_name: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Generator for batch processing table data.
        
        Args:
            table_name: Table to process
            batch_size: Number of rows per batch
            
        Yields:
            Batches of rows
        """
        connection = op.get_bind()
        offset = 0
        
        while True:
            rows = connection.execute(
                sa.text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"),
                {"limit": batch_size, "offset": offset}
            ).fetchall()
            
            if not rows:
                break
            
            yield rows
            offset += batch_size


class DataMigration:
    """Base class for data migrations."""
    
    def __init__(self):
        """Initialize data migration."""
        self.connection = op.get_bind()
    
    def execute(self, query: str, params: Optional[Dict] = None) -> Any:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query result
        """
        if params:
            return self.connection.execute(sa.text(query), params)
        return self.connection.execute(sa.text(query))
    
    def fetch_all(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Fetch all rows from a query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of row dictionaries
        """
        result = self.execute(query, params)
        return [dict(row) for row in result]
    
    def fetch_one(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Fetch a single row from a query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Single row as dictionary or None
        """
        result = self.execute(query, params).fetchone()
        return dict(result) if result else None
    
    def count_rows(self, table_name: str) -> int:
        """
        Count rows in a table.
        
        Args:
            table_name: Table to count
            
        Returns:
            Number of rows
        """
        result = self.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
        return result['count'] if result else 0
    
    def log_progress(self, current: int, total: int, item_name: str = "items") -> None:
        """
        Log migration progress.
        
        Args:
            current: Current count
            total: Total count
            item_name: Name of items being migrated
        """
        percentage = (current / total * 100) if total > 0 else 0
        logger.info(f"Progress: {current}/{total} {item_name} ({percentage:.1f}%)")


class TableBuilder:
    """Helper for building table definitions for table creation."""
    
    def __init__(self, table_name: str, primary_key: str = 'id'):
        """
        Initialize table builder.
        
        Args:
            table_name: Name of the table
            primary_key: Name of the primary key column
        """
        self.table_name = table_name
        self.columns = [
            sa.Column(primary_key, sa.Integer(), nullable=False, primary_key=True)
        ]
    
    def add_column(
        self,
        name: str,
        column_type: sa.types.TypeEngine,
        nullable: bool = True,
        default: Optional[Any] = None,
        index: bool = False
    ) -> 'TableBuilder':
        """
        Add a column to the table definition.
        
        Args:
            name: Column name
            column_type: SQLAlchemy column type
            nullable: Whether column allows NULL
            default: Default value
            index: Whether to create an index
            
        Returns:
            Self for method chaining
        """
        self.columns.append(
            sa.Column(name, column_type, nullable=nullable, server_default=default)
        )
        return self
    
    def add_timestamps(self) -> 'TableBuilder':
        """
        Add created_at and updated_at timestamp columns.
        
        Returns:
            Self for method chaining
        """
        self.columns.append(sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()))
        self.columns.append(sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()))
        return self
    
    def create(self) -> None:
        """Create the table."""
        op.create_table(self.table_name, *self.columns)
        logger.info(f"Created table {self.table_name}")
    
    def drop(self) -> None:
        """Drop the table."""
        op.drop_table(self.table_name)
        logger.info(f"Dropped table {self.table_name}")
