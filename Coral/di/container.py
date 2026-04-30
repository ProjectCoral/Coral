"""
Dependency Injection Container
===============================

A thread-safe DI container for managing component lifecycle.
"""

from enum import Enum
from typing import Callable, Type, TypeVar, Generic, Optional, Any, Dict, List

T = TypeVar("T")


class Lifetime(Enum):
    """Service lifetime options."""

    SINGLETON = "singleton"  # One instance per container
    TRANSIENT = "transient"  # New instance each time


class ServiceDescriptor:
    """Descriptor for a registered service."""

    __slots__ = ("service_type", "implementation", "factory", "lifetime", "instance")

    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable[..., Any]] = None,
        lifetime: Lifetime = Lifetime.SINGLETON,
    ):
        self.service_type = service_type
        self.implementation = implementation if implementation else service_type
        self.factory = factory
        self.lifetime = lifetime
        self.instance: Optional[Any] = None


class Container:
    """
    A thread-safe dependency injection container.

    Supports SINGLETON (one instance per container) and TRANSIENT
    (new instance each time) lifetimes.
    """

    __slots__ = ("_services", "_parent")

    def __init__(self, parent: Optional["Container"] = None):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._parent = parent

    def register(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[["Container"], T]] = None,
        lifetime: Lifetime = Lifetime.SINGLETON,
    ) -> None:
        """
        Register a service type.

        Args:
            service_type: The type to register
            implementation: The concrete implementation type (if different)
            factory: A factory function that takes container and returns instance
            lifetime: SINGLETON or TRANSIENT
        """
        if service_type in self._services:
            raise ValueError(f"Service {service_type.__name__} is already registered")

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation or service_type,
            factory=factory,
            lifetime=lifetime,
        )
        self._services[service_type] = descriptor

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register an existing instance as a singleton."""
        if service_type in self._services:
            raise ValueError(f"Service {service_type.__name__} is already registered")

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=type(instance),
            factory=None,
            lifetime=Lifetime.SINGLETON,
        )
        descriptor.instance = instance
        self._services[service_type] = descriptor

    def register_singleton(
        self, service_type: Type[T], factory: Callable[["Container"], T]
    ) -> None:
        """Register a singleton using a factory function."""
        self.register(service_type, factory=factory, lifetime=Lifetime.SINGLETON)

    def register_transient(
        self, service_type: Type[T], factory: Callable[["Container"], T]
    ) -> None:
        """Register a transient service using a factory function."""
        self.register(service_type, factory=factory, lifetime=Lifetime.TRANSIENT)

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service by type.

        Args:
            service_type: The type to resolve

        Returns:
            An instance of the requested type

        Raises:
            KeyError: If the service is not registered
        """
        # Check local registration first
        if service_type in self._services:
            descriptor = self._services[service_type]
            return self._resolve_descriptor(descriptor)

        # Check parent container
        if self._parent is not None:
            return self._parent.resolve(service_type)

        raise KeyError(f"Service {service_type.__name__} is not registered")

    def _resolve_descriptor(self, descriptor: ServiceDescriptor) -> Any:
        """Resolve a service from its descriptor."""
        # Thread-safe singleton resolution
        if descriptor.lifetime == Lifetime.SINGLETON:
            if descriptor.instance is not None:
                return descriptor.instance

            # Check if we have a factory or need to instantiate
            if descriptor.factory is not None:
                instance = descriptor.factory(self)
            else:
                # Auto-instantiate with constructor injection
                instance = self._create_instance(descriptor.implementation)

            descriptor.instance = instance
            return instance

        else:  # TRANSIENT
            if descriptor.factory is not None:
                return descriptor.factory(self)
            return self._create_instance(descriptor.implementation)

    def _create_instance(self, implementation: Type) -> Any:
        """
        Create an instance using constructor injection.
        Resolves constructor parameters from the container.
        """
        import inspect

        # Get constructor
        init_method = getattr(implementation, "__init__", None)
        if init_method is None:
            return implementation()

        # Get parameter names and types
        try:
            sig = inspect.signature(init_method)
        except (ValueError, TypeError):
            # Can't inspect, try no-args constructor
            return implementation()

        # Resolve each parameter
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Try to get annotation first, otherwise use parameter name to guess type
            param_type = param.annotation
            if param_type is inspect.Parameter.empty:
                # Try to infer from type hints if available
                type_hints = getattr(init_method, "__type_params__", None)
                if type_hints is None:
                    type_hints = getattr(implementation, "__annotations__", {})

            if param_type is not inspect.Parameter.empty and param_type is not None:
                try:
                    kwargs[param_name] = self.resolve(param_type)
                except KeyError:
                    if param.default is inspect.Parameter.empty:
                        raise RuntimeError(
                            f"Cannot resolve parameter '{param_name}' for {implementation.__name__}"
                        )
            else:
                if param.default is inspect.Parameter.empty:
                    raise RuntimeError(
                        f"Cannot resolve parameter '{param_name}' for {implementation.__name__}"
                    )

        return implementation(**kwargs)

    def resolve_many(self, service_type: Type[T]) -> List[T]:
        """
        Resolve all services registered for a type.
        Currently returns a single instance if registered.
        """
        return [self.resolve(service_type)]

    def create_scope(self) -> "Container":
        """Create a child container scope."""
        return Container(parent=self)

    def dispose(self) -> None:
        """Dispose all singleton instances."""
        for descriptor in self._services.values():
            if (
                descriptor.lifetime == Lifetime.SINGLETON
                and descriptor.instance is not None
            ):
                dispose_method = getattr(descriptor.instance, "dispose", None)
                if dispose_method is not None:
                    dispose_method()
                shutdown_method = getattr(descriptor.instance, "shutdown", None)
                if shutdown_method is not None:
                    import asyncio

                    try:
                        asyncio.get_event_loop().run_until_complete(shutdown_method())
                    except RuntimeError:
                        pass
                descriptor.instance = None

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        if service_type in self._services:
            return True
        if self._parent is not None:
            return self._parent.is_registered(service_type)
        return False
