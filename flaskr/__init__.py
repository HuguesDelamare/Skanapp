from flask import Flask
from flask_migrate import Migrate
from flaskr.models import db
import os

# Create the Flask application
app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='your_secret_key',
    SQLALCHEMY_DATABASE_URI='sqlite:///site.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# Initialize the database
db.init_app(app)

# Initialize the migration engine
migrate = Migrate(app, db)

with app.app_context():
    os.makedirs('flaskr/uploads', exist_ok=True)

from flaskr import routes
