"""Adveno API entry point."""

from drivers.http.app import create_app

app = create_app()
