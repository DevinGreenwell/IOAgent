"""Async tasks package for IOAgent."""

from src.celery_app import celery_app

__all__ = ['celery_app']