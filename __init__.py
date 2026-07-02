"""Application factory for Peak Pulse Fitness.

Creates and configures the Flask application, binds the shared
SQLAlchemy database instance, and registers all route handlers.
"""
from flask import Flask
from config import Config
from db import db
from flask_migrate import Migrate

app = Flask(__name__, static_folder='statics/plots')
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

# Make Python's enumerate available inside all Jinja2 templates
app.jinja_env.globals['enumerate'] = enumerate

with app.app_context():
    import routes
    routes.app = app
