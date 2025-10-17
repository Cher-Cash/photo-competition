import os
import typing

from dotenv import load_dotenv
from flask_mail import Mail
from flask import Flask, jsonify, render_template
from flask_admin.contrib.sqla import ModelView
from flask_cors import CORS


from app.extansions import db, admin_ext, login_manager, migrate_ext
from app.models import Users, Artworks, Nominations, Competitions, Ratings


mail = Mail()


def configure_extensions(app):
    db.init_app(app)
    admin_ext.init_app(app)
    migrate_ext.init_app(app, db)
    login_manager.init_app(app=app)
    login_manager.login_view = "user.authorization"  # type: ignore


def create_app(testing=False):  # noqa: FBT002
    load_dotenv()
    new_app = Flask(__name__)

    if testing:
        new_app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_TEST")
    else:
        new_app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_REAL")

    new_app.secret_key = os.getenv("SECRET_KEY")
    new_app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'artworks')
    new_app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024))
    new_app.config["CORS_HEADERS"] = "Content-Type"

    new_app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    new_app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    new_app.config['MAIL_USE_TLS'] = True
    new_app.config['MAIL_USE_SSL'] = False
    new_app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    new_app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    new_app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    mail.init_app(new_app)

    configure_extensions(new_app)
    CORS(new_app, resources={r"/*": {"origins": "*"}})

    @new_app.route("/ping")
    def init_route():
        return jsonify({"status": "ok"})

    @new_app.route("/index")
    def index():
        return render_template('index.html')

    from app.views.user import user_bp
    from app.views.application import application_bp

    new_app.register_blueprint(application_bp, url_prefix="/")
    new_app.register_blueprint(user_bp, url_prefix="/user")
    return new_app


class MyModelView(ModelView):
    column_hide_backrefs = False


class UsersView(MyModelView):
    column_list = ("id", "f_name", "s_name", "age", "about_user", "email", "role", "status", )
    form_columns: typing.ClassVar = ["f_name", "s_name", "age", "about_user", "email", "role", "status"]


class ArtworksView(MyModelView):
    column_list = ["id", "file", "file_name", "status", "user_id", "nomination_id"]
    form_columns: typing.ClassVar = ["file", "file_name", "status", "user_id", "nomination_id"]


class NominationsView(MyModelView):
    column_list = ["id", "title", "winner_work_id", "competition_id", "status"]
    form_columns: typing.ClassVar = ["title", "winner_work_id", "competition_id", "status"]


class CompetitionsView(MyModelView):
    column_list = ["id", "title", "status", "start_of_accepting", "end_of_accepting", "summing_up"]
    form_columns: typing.ClassVar = ["title", "status", "start_of_accepting", "end_of_accepting", "summing_up"]


class RatingsView(MyModelView):
    column_list = ["id", "rate", "work_id", "juri_id"]
    form_columns: typing.ClassVar = ["rate", "work_id", "juri_id"]


admin_ext.add_view(UsersView(Users, db.session))
admin_ext.add_view(ArtworksView(Artworks, db.session))
admin_ext.add_view(NominationsView(Nominations, db.session))
admin_ext.add_view(CompetitionsView(Competitions, db.session))
admin_ext.add_view(RatingsView(Ratings, db.session))
