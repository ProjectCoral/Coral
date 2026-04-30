"""
Dependency Injection Module
===========================

Provides a DI container for managing component lifecycle.
"""

from .container import Container, Lifetime, ServiceDescriptor

__all__ = [
    "Container",
    "Lifetime",
    "ServiceDescriptor",
]
