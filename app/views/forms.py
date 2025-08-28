from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email



class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Отправить ссылку")