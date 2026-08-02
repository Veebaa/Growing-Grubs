"""
Dependency Injection Container for Growing Grubs application.

This module provides a simple IoC (Inversion of Control) container for managing
application dependencies, improving testability and loose coupling.
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar
from mod.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class Container:
    """Simple dependency injection container."""
    
    def __init__(self):
        """Initialize the container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(
        self,
        name: str,
        factory: Callable,
        singleton: bool = False
    ) -> None:
        """
        Register a service factory.
        
        Args:
            name: Service name
            factory: Factory function to create the service
            singleton: If True, only one instance is created and reused
        """
        self._factories[name] = factory
        if singleton:
            self._singletons[name] = None
        logger.debug(f"Registered service: {name} (singleton={singleton})")
    
    def register_instance(self, name: str, instance: Any) -> None:
        """
        Register a pre-created instance.
        
        Args:
            name: Service name
            instance: The instance to register
        """
        self._services[name] = instance
        logger.debug(f"Registered instance: {name}")
    
    def get(self, name: str) -> Any:
        """
        Get a service instance.
        
        Args:
            name: Service name
            
        Returns:
            The service instance
            
        Raises:
            KeyError: If service is not registered
        """
        # Check if instance is already registered
        if name in self._services:
            return self._services[name]
        
        # Check if factory is registered
        if name not in self._factories:
            raise KeyError(f"Service '{name}' not registered in container")
        
        factory = self._factories[name]
        
        # Handle singletons
        if name in self._singletons:
            if self._singletons[name] is None:
                self._singletons[name] = factory()
            return self._singletons[name]
        
        # Create new instance each time
        return factory()
    
    def has(self, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: Service name
            
        Returns:
            True if registered, False otherwise
        """
        return name in self._services or name in self._factories
    
    def clear(self) -> None:
        """Clear all registered services and factories."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.debug("Container cleared")
    
    def resolve_dependencies(self, factory: Callable) -> Any:
        """
        Resolve and call a factory with its dependencies.
        
        Args:
            factory: Factory function with dependency parameters
            
        Returns:
            Result of calling the factory
        """
        import inspect
        
        sig = inspect.signature(factory)
        dependencies = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Try to resolve from container
            if self.has(param_name):
                dependencies[param_name] = self.get(param_name)
            elif param.default is not inspect.Parameter.empty:
                # Use default value if available
                dependencies[param_name] = param.default
            else:
                logger.warning(f"Could not resolve dependency: {param_name}")
        
        return factory(**dependencies)


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get the global container instance.
    
    Returns:
        The global Container instance
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


def register_service(
    name: str,
    factory: Callable,
    singleton: bool = False
) -> None:
    """
    Register a service with the global container.
    
    Args:
        name: Service name
        factory: Factory function
        singleton: Whether to use singleton pattern
    """
    get_container().register(name, factory, singleton=singleton)


def register_instance(name: str, instance: Any) -> None:
    """
    Register an instance with the global container.
    
    Args:
        name: Service name
        instance: The instance to register
    """
    get_container().register_instance(name, instance)


def get_service(name: str) -> Any:
    """
    Get a service from the global container.
    
    Args:
        name: Service name
        
    Returns:
        The service instance
    """
    return get_container().get(name)


def inject(name: str) -> Callable:
    """
    Decorator to inject dependencies into a function.
    
    Args:
        name: Service name to inject
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Inject the service if not already provided
            if name not in kwargs:
                kwargs[name] = get_service(name)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def setup_dependencies(app) -> None:
    """
    Set up all application dependencies.
    
    Args:
        app: Flask application instance
    """
    container = get_container()
    
    # Register database
    from mod import db
    register_instance('db', db)
    
    # Register services as singletons
    from mod.services import RecipeService, FavouriteService, MealPlanService, UserService
    register_service('recipe_service', lambda: RecipeService(), singleton=True)
    register_service('favourite_service', lambda: FavouriteService(), singleton=True)
    register_service('meal_plan_service', lambda: MealPlanService(), singleton=True)
    register_service('user_service', lambda: UserService(), singleton=True)
    
    # Register utilities
    from mod.pagination import PaginationHelper
    register_instance('pagination_helper', PaginationHelper())
    
    from mod.sanitizer import InputSanitizer
    register_instance('sanitizer', InputSanitizer())
    
    from mod.validators import Validator
    register_instance('validator', Validator())
    
    logger.info("Dependencies registered successfully")


class ServiceProvider:
    """Base class for service providers."""
    
    def register(self, container: Container) -> None:
        """
        Register services with the container.
        
        Args:
            container: The DI container
        """
        raise NotImplementedError
    
    def boot(self, app) -> None:
        """
        Boot the service provider.
        
        Args:
            app: Flask application instance
        """
        raise NotImplementedError


class DatabaseServiceProvider(ServiceProvider):
    """Service provider for database services."""
    
    def register(self, container: Container) -> None:
        """Register database services."""
        from mod import db
        container.register_instance('db', db)
    
    def boot(self, app) -> None:
        """Boot database services."""
        logger.info("Database service provider booted")


class RepositoryServiceProvider(ServiceProvider):
    """Service provider for repository/service classes."""
    
    def register(self, container: Container) -> None:
        """Register repository services."""
        from mod.services import RecipeService, FavouriteService, MealPlanService, UserService
        container.register('recipe_service', lambda: RecipeService(), singleton=True)
        container.register('favourite_service', lambda: FavouriteService(), singleton=True)
        container.register('meal_plan_service', lambda: MealPlanService(), singleton=True)
        container.register('user_service', lambda: UserService(), singleton=True)
    
    def boot(self, app) -> None:
        """Boot repository services."""
        logger.info("Repository service provider booted")


class UtilityServiceProvider(ServiceProvider):
    """Service provider for utility classes."""
    
    def register(self, container: Container) -> None:
        """Register utility services."""
        from mod.pagination import PaginationHelper
        from mod.sanitizer import InputSanitizer
        from mod.validators import Validator
        
        container.register_instance('pagination_helper', PaginationHelper())
        container.register_instance('sanitizer', InputSanitizer())
        container.register_instance('validator', Validator())
    
    def boot(self, app) -> None:
        """Boot utility services."""
        logger.info("Utility service provider booted")
