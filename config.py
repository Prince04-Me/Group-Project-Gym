"""Application configuration for Peak Pulse Fitness.

Reads settings from environment variables where available,
falling back to sensible development defaults.
"""
import os

"""basedir is defined outside the class because it's used to build the database path, 
and it needs to resolve at import time relative to wherever config.py sits on disk. os.
"""

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Flask application configuration.

    Attributes:
        SQLALCHEMY_DATABASE_URI:        Path to the SQLite database file.
        SQLALCHEMY_TRACK_MODIFICATIONS: Disabled to suppress deprecation warnings.
        SECRET_KEY:                     Used by Flask-WTF for CSRF protection.
    """

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL')
        or 'sqlite:///' + os.path.join(basedir, '5_gym_fitness', '5_gym_fitness.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-fallback-key'
