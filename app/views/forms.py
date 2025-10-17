import re
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired



class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")




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


class CustomPasswordValidator:
    def __init__(self):
        self.messages = []

    def __call__(self, form, field):
        password = field.data

        if not password:
            return

        self.messages = []

        # Проверка минимальной длины
        if len(password) < 8:
            self.messages.append('Минимум 8 символов')

        # Проверка наличия заглавных букв
        if not re.search(r'[A-ZА-Я]', password):
            self.messages.append('Хотя бы одна заглавная буква')

        # Проверка наличия строчных букв
        if not re.search(r'[a-zа-я]', password):
            self.messages.append('Хотя бы одна строчная буква')

        # Проверка наличия цифр
        if not re.search(r'\d', password):
            self.messages.append('Хотя бы одна цифра')

        # Проверка наличия специальных символов
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            self.messages.append('Хотя бы один специальный символ (!@#$%^&*(),.?":{}|<>)')

        # Если есть ошибки - показываем все сразу
        if self.messages:
            raise ValidationError('Пароль должен содержать: ' + ', '.join(self.messages))


class RegistrationForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(message='Имя обязательно')])
    second_name = StringField('Фамилия', validators=[DataRequired(message='Фамилия обязательна')])
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email адрес')
    ])
    age = IntegerField('Возраст', validators=[
        DataRequired(message='Возраст обязателен'),
        NumberRange(min=1, max=150, message='Введите корректный возраст (1-150 лет)')
    ])
    role = SelectField('Роль', choices=[
        ('', '-- Выберите роль --'),
        ('participant', 'Участник'),
        ('judge', 'Судья'),
        ('admin', 'Администратор')
    ], validators=[DataRequired(message='Выберите роль')])
    about = TextAreaField('О себе', validators=[
        Length(max=900, message='Описание не должно превышать 900 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен'),
        CustomPasswordValidator()
    ])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(message='Подтверждение пароля обязательно'),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    agree_terms = BooleanField('Согласие с правилами', validators=[
        DataRequired(message='Необходимо согласие с правилами')
    ])


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Отправить ссылку")

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Новый пароль', validators=[
        DataRequired(message='Пароль обязателен'),
        CustomPasswordValidator()
    ])
    confirm_password = PasswordField('Подтвердите новый пароль', validators=[
        DataRequired(message='Подтверждение пароля обязательно'),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Изменить пароль')