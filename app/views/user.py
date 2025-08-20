from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import current_user, login_user, logout_user
import sqlalchemy as sa

from app.extansions import db
from app.models import Users

user_bp = Blueprint("user", __name__)


@user_bp.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == 'POST':
        # Получаем данные из формы
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        f_name = request.form.get('name')
        s_name = request.form.get('second_name')
        age = int(request.form.get('age'))
        role = request.form.get('role')
        print({"email": email, "password":password, "f_name":f_name, "s_name":s_name, "age":age, "role": role})


        # Валидация данных
        errors = []

        # Проверка заполненности полей
        if not email:
            errors.append("Email обязателен для заполнения")
        if not password:
            errors.append("Пароль обязателен для заполнения")
        if password != confirm_password:
            errors.append("Пароли не совпадают")

        # Проверка формата email
        if email and '@' not in email:
            errors.append("Некорректный email")

        # Проверка длины пароля
        if password and len(password) < 8:
            errors.append("Пароль должен содержать минимум 8 символов")

        # Если есть ошибки - показываем их
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('user.registration'))

        # Проверяем, не зарегистрирован ли уже пользователь
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash('Пользователь с таким email уже зарегистрирован', 'danger')
            return redirect(url_for('user.registration'))

        try:
            # Хешируем пароль перед сохранением
            hashed_password = Users.set_password(password)
            print(hashed_password)

            # Создаем нового пользователя
            new_user = Users(
                email=email,
                password_hash=hashed_password,
                f_name=f_name,
                s_name=s_name,
                age=age,
                role=role
            )

            # Добавляем в базу
            db.session.add(new_user)
            db.session.commit()

            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('user.authorization'))

        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.', 'danger')
            return redirect(url_for('user.registration'))

        # Если GET запрос - просто отображаем форму
    return render_template('registration.html')


@user_bp.route("/authorization", methods=["GET", "POST"])
def authorization():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(Users).where(Users.email == form.email.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('user_bp.registration'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('authorization.html', title='Sign In', form=form)

@user_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))






