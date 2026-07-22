"""Shared deterministic operation service for CLI and agent transports."""

from .registry import OperationRegistry, execute_request

__all__ = ["OperationRegistry", "execute_request"]
