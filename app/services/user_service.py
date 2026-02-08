from dataclasses import dataclass
from app.models import Users



class UserServiceException(Exception):
    pass

class UserExist(UserServiceException):
    pass

class UserDbError(UserServiceException):
    pass


@dataclass()
class NewUser:
    email: str
    password: str
    f_name: str
    s_name: str
    age: int
    role_id: int
    about: str
    password_hash: str | None=None
    verification_token: str | None=None

class UserService:
    def __init__(self, db):
        self.db = db


    def create_user(self, user: NewUser) -> NewUser:
        self.is_user_exist(user.email)
        user.password_hash = Users.set_password(user.password)
        new_user = Users(
            email=user.email,
            password_hash=user.password_hash,
            f_name=user.f_name,
            s_name=user.f_name,
            age=user.age,
            role_id=user.role_id,
            about_user=user.about,
            status='pending'
        )
        new_user.generate_verification_token()
        user.verification_token = new_user.verification_token

        try:
            self.db.session.add(new_user)
            self.db.session.commit()
            return user
        except Exception:
            self.db.session.rollback()
            raise UserDbError()




    def is_user_exist(self, email: str):
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            raise UserExist()
