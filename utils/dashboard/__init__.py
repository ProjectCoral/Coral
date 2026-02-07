"""
Coral Dashboard - 模块化重构版本

这是一个现代化的、模块化的dashboard实现，用于监控和管理Coral框架。
"""

__version__ = "1.0.0"
__author__ = "Coral Framework Team"

from .main import dashboard, run_dashboard

__all__ = ["dashboard", "run_dashboard"]