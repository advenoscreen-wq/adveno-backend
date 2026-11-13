"""Operational health routes."""

from fastapi import APIRouter

from drivers.routers.health.routes import router

__all__ = ["router"]
