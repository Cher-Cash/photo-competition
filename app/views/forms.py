from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired



class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Отправить ссылку")

class SubmissionForm(FlaskForm):
    photo = FileField('Фотография', validators=[
        FileRequired(message='Пожалуйста, выберите файл'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения (jpg, jpeg, png, gif)')
    ])
    nomination_id = SelectField('Номинация',
        choices=[],  # Будет заполняться динамически
        validators=[DataRequired(message='Пожалуйста, выберите номинацию')]
    )
    description = TextAreaField('Название работы', validators=[
        DataRequired(message='Пожалуйста, напишите название работы'),
        Length(max=254, message='Название не должно превышать 254 символа')
    ])
    submit = SubmitField('Отправить заявку')