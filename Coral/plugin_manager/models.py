"""
Plugin Manager Data Models
==========================

Data classes and models for the plugin management system.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from enum import Enum

from .exceptions import DependencyCycleError


class PluginState(Enum):
    """Plugin state enumeration."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    DISABLED = "disabled"
    ENABLED = "enabled"


class PluginLoadStatus(Enum):
    """Plugin load status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    DEPENDENCY_FAILED = "dependency_failed"


@dataclass
class PluginMetrics:
    """Plugin performance metrics."""
    load_time: float = 0.0
    total_calls: int = 0
    avg_execution_time: float = 0.0
    total_errors: int = 0
    last_error: Optional[str] = None
    last_loaded: float = field(default_factory=time.time)
    load_count: int = 0
    unload_count: int = 0
    
    def record_load(self, load_time: float):
        """Record a plugin load."""
        self.load_time = load_time
        self.last_loaded = time.time()
        self.load_count += 1
    
    def record_error(self, error: str):
        """Record a plugin error."""
        self.total_errors += 1
        self.last_error = error
    
    def record_call(self, execution_time: float):
        """Record a plugin call."""
        self.total_calls += 1
        # Update average execution time
        if self.total_calls == 1:
            self.avg_execution_time = execution_time
        else:
            self.avg_execution_time = (
                (self.avg_execution_time * (self.total_calls - 1) + execution_time) 
                / self.total_calls
            )


@dataclass
class PluginMeta:
    """Plugin metadata."""
    name: str
    version: str = "1.0.0"
    author: str = "Unknown"
    description: str = ""
    compatibility: int = 250606
    dependencies: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    path: Optional[str] = None
    disabled: bool = False
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.dependencies:
            self.dependencies = []
        if not self.requirements:
            self.requirements = []
    
    def is_compatible(self, manager_version: int = 250606) -> bool:
        """Check if plugin is compatible with the plugin manager version."""
        return self.compatibility >= manager_version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "compatibility": self.compatibility,
            "dependencies": self.dependencies,
            "requirements": self.requirements,
            "disabled": self.disabled
        }


@dataclass
class PluginInfo:
    """Complete plugin information."""
    name: str
    meta: PluginMeta
    state: PluginState
    metrics: PluginMetrics
    load_status: Optional[PluginLoadStatus] = None
    error_message: Optional[str] = None
    dependencies_met: bool = False
    
    @property
    def is_loaded(self) -> bool:
        """Check if plugin is loaded."""
        return self.state == PluginState.LOADED
    
    @property
    def is_disabled(self) -> bool:
        """Check if plugin is disabled."""
        return self.state == PluginState.DISABLED or self.meta.disabled
    
    @property
    def can_load(self) -> bool:
        """Check if plugin can be loaded."""
        return (
            not self.is_loaded 
            and not self.is_disabled 
            and self.dependencies_met
            and self.load_status != PluginLoadStatus.FAILED
        )


@dataclass
class DependencyGraph:
    """Dependency graph for plugins."""
    graph: Dict[str, Set[str]] = field(default_factory=dict)
    reverse_graph: Dict[str, Set[str]] = field(default_factory=dict)
    
    def add_plugin(self, plugin_name: str):
        """Add a plugin to the graph."""
        if plugin_name not in self.graph:
            self.graph[plugin_name] = set()
        if plugin_name not in self.reverse_graph:
            self.reverse_graph[plugin_name] = set()
    
    def add_dependency(self, plugin: str, depends_on: str):
        """Add a dependency relationship."""
        self.add_plugin(plugin)
        self.add_plugin(depends_on)
        self.graph[plugin].add(depends_on)
        self.reverse_graph[depends_on].add(plugin)
    
    def get_dependencies(self, plugin: str) -> Set[str]:
        """Get all dependencies for a plugin."""
        return self.graph.get(plugin, set())
    
    def get_dependents(self, plugin: str) -> Set[str]:
        """Get all plugins that depend on this plugin."""
        return self.reverse_graph.get(plugin, set())
    
    def has_cycle(self) -> bool:
        """Check if the graph has cycles using DFS."""
        visited = set()
        recursion_stack = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in self.graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    return True
            
            recursion_stack.remove(node)
            return False
        
        for node in self.graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def topological_sort(self) -> List[List[str]]:
        """
        Perform topological sort, returning plugins in layers.
        
        Returns:
            List of lists where each inner list contains plugins
            that can be loaded concurrently (same dependency level).
        """
        if self.has_cycle():
            raise DependencyCycleError("Circular dependency detected")
        
        # Calculate in-degrees
        in_degree = {node: 0 for node in self.graph}
        for node in self.graph:
            for neighbor in self.graph[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1
        
        # Find nodes with zero in-degree
        zero_in_degree = [node for node in self.graph if in_degree[node] == 0]
        layers = []
        
        while zero_in_degree:
            layers.append(zero_in_degree.copy())
            next_zero_in_degree = []
            
            for node in zero_in_degree:
                for neighbor in self.graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_zero_in_degree.append(neighbor)
            
            zero_in_degree = next_zero_in_degree
        
        # Check if all nodes were processed
        if len([node for node in in_degree if in_degree[node] > 0]) > 0:
            raise DependencyCycleError("Graph has cycles or missing nodes")
        
        return layers