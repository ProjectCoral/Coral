"""
Permission Module
=================

A module for managing permissions and access control in the Coral framework.
"""

from .permission import (
    Permission,
    PermissionSet,
    PermissionType,
    create_permission,
)

from .perm_system import PermSystem

__all__ = [
    "Permission",
    "PermissionSet",
    "PermissionType",
    "create_permission",
    "PermSystem",
]
