"""Application factory for Peak Pulse Fitness.

Creates and configures the Flask application, binds the shared
SQLAlchemy database instance, and registers all route handlers.
"""
from flask import Flask
from config import Config
from db import db
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

import routes
