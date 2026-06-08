"""Shared SQLAlchemy database instance.

Defined here — separate from the Flask app — so that models can import
it without triggering a circular import with __init__.py.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
