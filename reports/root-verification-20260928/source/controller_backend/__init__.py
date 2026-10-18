"""Explicitly connected, simulation-only LinuxCNC service boundary."""

from .linuxcnc_backend import BackendError, ControlRequest, LinuxCNCBackend

__all__ = ["BackendError", "ControlRequest", "LinuxCNCBackend"]
