"""
Plugin Metadata Management
==========================

Handles plugin metadata parsing, caching, and dependency graph building.
"""

import os
import ast
import hashlib
import logging
from typing import Dict, Any, Optional, List, Set
from functools import lru_cache

from .models import PluginMeta, DependencyGraph
from .exceptions import PluginMetadataError

logger = logging.getLogger(__name__)


class PluginMetadata:
    """Plugin metadata manager."""
    
    def __init__(self):
        self._meta_cache: Dict[str, PluginMeta] = {}
        self._file_hash_cache: Dict[str, str] = {}
    
    @lru_cache(maxsize=32)
    def _get_file_hash(self, filepath: str) -> str:
        """Get file hash for caching."""
        if not os.path.exists(filepath):
            return ""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute hash for {filepath}: {e}")
            return ""
    
    def get_plugin_meta(self, plugin_path: str, plugin_name: Optional[str] = None) -> Optional[PluginMeta]:
        """
        Get plugin metadata from plugin directory.
        
        Args:
            plugin_path: Path to plugin directory
            plugin_name: Optional plugin name (defaults to directory name)
            
        Returns:
            PluginMeta object or None if metadata cannot be parsed
        """
        if plugin_name is None:
            plugin_name = os.path.basename(plugin_path)
        
        init_file = os.path.join(plugin_path, "__init__.py")
        if not os.path.exists(init_file):
            return None
        
        # Check cache
        file_hash = self._get_file_hash(init_file)
        cache_key = f"{init_file}:{file_hash}"
        
        if cache_key in self._meta_cache:
            return self._meta_cache[cache_key]
        
        # Parse metadata
        meta_dict = self._parse_plugin_meta_file(init_file)
        if not meta_dict:
            return None
        
        try:
            # Create PluginMeta object
            meta = PluginMeta(
                name=meta_dict.get('name', plugin_name),
                version=meta_dict.get('version', '1.0.0'),
                author=meta_dict.get('author', 'Unknown'),
                description=meta_dict.get('description', ''),
                compatibility=int(meta_dict.get('compatibility', 250606)),
                dependencies=meta_dict.get('dependencies', []),
                requirements=meta_dict.get('requirements', []),
                path=plugin_path,
                disabled=self._is_plugin_disabled(plugin_path)
            )
            
            # Cache the result
            self._meta_cache[cache_key] = meta
            return meta
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid plugin metadata in {init_file}: {e}")
            return None
    
    def _is_plugin_disabled(self, plugin_path: str) -> bool:
        """Check if plugin is disabled by checking for .disabled suffix."""
        return plugin_path.endswith('.disabled') or os.path.basename(plugin_path).endswith('.disabled')
    
    def _parse_plugin_meta_file(self, init_file: str) -> Optional[Dict[str, Any]]:
        """Parse plugin metadata from __init__.py file."""
        if not os.path.exists(init_file):
            return None
        
        try:
            with open(init_file, "r", encoding="utf-8") as f:
                source = f.read()
            
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to parse {init_file}: {e}")
            return None
        
        # Look for __plugin_meta__ assignment
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__plugin_meta__":
                        value_node = node.value
                        if isinstance(value_node, ast.Dict):
                            return self._extract_dict_from_ast(value_node)
        
        return None
    
    def _extract_dict_from_ast(self, dict_node: ast.Dict) -> Dict[str, Any]:
        """Extract dictionary from AST Dict node."""
        result = {}
        
        for key_node, value_node in zip(dict_node.keys, dict_node.values):
            # Extract key
            if isinstance(key_node, ast.Constant):
                key = key_node.value
            elif isinstance(key_node, ast.Name):
                key = key_node.id
            elif isinstance(key_node, ast.Str):  # Python 3.7 compatibility
                key = key_node.s
            else:
                continue
            
            # Extract value
            if isinstance(value_node, ast.Constant):
                value = value_node.value
            elif isinstance(value_node, ast.Str):  # Python 3.7 compatibility
                value = value_node.s
            elif isinstance(value_node, ast.Num):  # Python 3.7 compatibility
                value = value_node.n
            elif isinstance(value_node, ast.List):
                value = []
                for item in value_node.elts:
                    if isinstance(item, ast.Constant):
                        value.append(item.value)
                    elif isinstance(item, ast.Str):  # Python 3.7 compatibility
                        value.append(item.s)
            else:
                # For other types, try to get string representation
                try:
                    value = ast.unparse(value_node) if hasattr(ast, 'unparse') else repr(value_node)
                except:
                    value = str(value_node)
            
            result[key] = value
        
        return result
    
    def build_dependency_graph(self, plugins_meta: Dict[str, PluginMeta]) -> DependencyGraph:
        """
        Build dependency graph from plugin metadata.
        
        Args:
            plugins_meta: Dictionary mapping plugin names to PluginMeta objects
            
        Returns:
            DependencyGraph object
        """
        graph = DependencyGraph()
        
        # Add all plugins to graph
        for plugin_name in plugins_meta:
            graph.add_plugin(plugin_name)
        
        # Add dependencies
        for plugin_name, meta in plugins_meta.items():
            for dep in meta.dependencies:
                if dep in plugins_meta:
                    graph.add_dependency(plugin_name, dep)
                else:
                    logger.warning(f"Plugin {plugin_name} depends on unknown plugin: {dep}")
        
        return graph
    
    def get_enabled_plugin_dirs(self, plugin_dir: str) -> List[str]:
        """
        Get list of enabled plugin directories.
        
        Args:
            plugin_dir: Base plugin directory
            
        Returns:
            List of paths to enabled plugin directories
        """
        if not os.path.exists(plugin_dir):
            return []
        
        plugin_dirs = []
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)
            
            # Skip disabled plugins (those with .disabled suffix)
            if item.endswith('.disabled'):
                continue
            
            # Check if it's a directory with __init__.py
            if os.path.isdir(item_path):
                init_file = os.path.join(item_path, "__init__.py")
                if os.path.exists(init_file):
                    plugin_dirs.append(item_path)
        
        return plugin_dirs
    
    def get_disabled_plugin_dirs(self, plugin_dir: str) -> List[str]:
        """
        Get list of disabled plugin directories.
        
        Args:
            plugin_dir: Base plugin directory
            
        Returns:
            List of paths to disabled plugin directories
        """
        if not os.path.exists(plugin_dir):
            return []
        
        disabled_dirs = []
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)
            
            # Only include disabled plugins
            if item.endswith('.disabled') and os.path.isdir(item_path):
                init_file = os.path.join(item_path, "__init__.py")
                if os.path.exists(init_file):
                    disabled_dirs.append(item_path)
        
        return disabled_dirs
    
    def clear_cache(self):
        """Clear metadata cache."""
        self._meta_cache.clear()
        self._file_hash_cache.clear()
        self._get_file_hash.cache_clear()