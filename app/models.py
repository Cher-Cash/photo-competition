import pytz
from datetime import datetime, timedelta
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
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

    verification_token = db.Column(db.String(100), unique=True)
    verification_sent_at = db.Column(db.DateTime)

    reset_password_token = db.Column(db.String(100), unique=True)
    reset_password_sent_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.now(pytz.UTC))

    def generate_token(self, token_type='verification', status='pending'):
        """
        Универсальный метод генерации токена

        :param token_type: 'verification' или 'password_reset'
        :param status: статус для установки (только для verification)
        """
        import secrets
        token = secrets.token_urlsafe(32)
        current_time = datetime.now(pytz.UTC)

        if token_type == 'verification':
            self.verification_token = token
            self.verification_sent_at = current_time
            self.status = status
        elif token_type == 'password_reset':
            self.reset_password_token = token
            self.reset_password_sent_at = current_time

        return token

    def is_token_expired(self, token_type='verification', hours=1):
        """
        Универсальный метод проверки истечения срока действия токена

        :param token_type: 'verification' или 'password_reset'
        :param hours: количество часов для проверки
        """
        if token_type == 'verification':
            sent_at = self.verification_sent_at
        elif token_type == 'password_reset':
            sent_at = self.reset_password_sent_at
        else:
            return True

        if not sent_at:
            return True

        # Если время без временной зоны, добавляем её
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=pytz.UTC)

        expiry_time = sent_at + timedelta(hours=hours)
        return datetime.now(pytz.UTC) > expiry_time

    # Старые методы для обратной совместимости
    def generate_verification_token(self):
        """Совместимость со старым кодом"""
        return self.generate_token('verification', 'pending')

    def is_verification_token_expired(self):
        """Совместимость со старым кодом"""
        return self.is_token_expired('verification', 1)

    # Новые методы для сброса пароля
    def generate_password_reset_token(self):
        return self.generate_token('password_reset')

    def is_password_reset_token_expired(self):
        return self.is_token_expired('password_reset', 1)

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
    status = Column(String(20))

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

    nominations = relationship("Nominations", backref="competition")


class Ratings(db.Model):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True)
    rate = Column(Integer)
    work_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    juri_id = Column(Integer, ForeignKey("users.id"), nullable=False)
