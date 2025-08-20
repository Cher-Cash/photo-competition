from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_admin import Admin

db = SQLAlchemy()
admin_ext = Admin(template_mode="bootstrap3")
migrate_ext = Migrate()
login_manager: LoginManager = LoginManager()