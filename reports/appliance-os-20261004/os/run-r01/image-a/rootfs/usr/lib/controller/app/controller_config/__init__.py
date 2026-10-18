"""Disconnected configuration prototype; this package never controls a machine."""

from .model import ConfigurationError, capabilities, configuration_schema, profile
from .service import ConfigurationService, RuntimeState

__all__ = ["ConfigurationError", "ConfigurationService", "RuntimeState",
           "capabilities", "configuration_schema", "profile"]
