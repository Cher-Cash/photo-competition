from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


from app.extansions import db, login_manager


@login_manager.user_loader
def load_user(id):
    return db.session.get(Users, int(id))


class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    f_name = Column(String(20), nullable=False)
    s_name = Column(String(20), nullable=False)
    age = Column(Integer, nullable=False)
    about_user = Column(String(900))
    email = Column(String(254), nullable=False)
    password_hash = Column(db.String(256), nullable=False)
    role = Column(String(20), nullable=False)
    status = Column(String(20), nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def set_password(password):
        password_hash = generate_password_hash(password)
        return password_hash


class Artworks(db.Model):
    __tablename__ = "artworks"
    id = Column(Integer, primary_key=True)
    file = Column(String(254))
    file_name = Column(String(254))
    status = Column(String(20))

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nomination_id = Column(Integer, ForeignKey("nominations.id"), nullable=False)


class Nominations(db.Model):
    __tablename__ = "nominations"
    id = Column(Integer, primary_key=True)
    title = Column(String(254))

    winner_work_id = Column(Integer, ForeignKey("artworks.id"), nullable=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)


class Competitions(db.Model):
    __tablename__ = "competitions"
    id = Column(Integer, primary_key=True)
    title = Column(String(254))
    status = Column(String(20))
    start_of_accepting = Column(DateTime)
    end_of_accepting = Column(DateTime)
    summing_up = Column(DateTime)

    nomination_id = Column(Integer, ForeignKey("nominations.id"), nullable=False)


class Ratings(db.Model):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True)
    rate = Column(Integer)
    work_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    juri_id = Column(Integer, ForeignKey("users.id"), nullable=False)
