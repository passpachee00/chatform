"""
Base classes for tool management in chat service

Provides abstract base class for tool handlers and a registry for managing tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ToolHandler(ABC):
    """Base class for all tool handlers"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAI function schema"""
        pass

    @abstractmethod
    async def execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute the tool with given arguments

        Args:
            arguments: Parsed tool arguments from OpenAI
            context: Optional context (red_flag, app_data, etc.)

        Returns:
            Formatted result string for LLM consumption
        """
        pass


class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        self._tools: Dict[str, ToolHandler] = {}

    def register(self, tool: ToolHandler) -> None:
        """Register a tool handler"""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolHandler]:
        """Get tool handler by name"""
        return self._tools.get(name)

    def get_schemas(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get OpenAI schemas for specified tools (or all if None)

        Args:
            tool_names: List of tool names to include, or None for all

        Returns:
            List of OpenAI function schemas
        """
        if tool_names is None:
            tools = self._tools.values()
        else:
            tools = [self._tools[name] for name in tool_names if name in self._tools]

        return [
            {
                "type": "function",
                "function": tool.get_schema()
            }
            for tool in tools
        ]

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute a tool by name"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")

        return await tool.execute(arguments, context)
