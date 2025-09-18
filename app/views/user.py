from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import current_user, login_user, logout_user
import sqlalchemy as sa

from app.extansions import db
from app.models import Users
from app.views.forms import LoginForm, ForgotPasswordForm, RegistrationForm

user_bp = Blueprint("user", __name__)


@user_bp.route("/registration", methods=["GET", "POST"])
def registration():
    form = RegistrationForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        f_name = form.name.data
        s_name = form.second_name.data
        age = form.age.data
        role = form.role.data


        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash('Пользователь с таким email уже зарегистрирован', 'danger')
            return redirect(url_for('user.registration'))

        try:
            hashed_password = Users.set_password(password)

            new_user = Users(
                email=email,
                password_hash=hashed_password,
                f_name=f_name,
                s_name=s_name,
                age=age,
                role=role
            )

            db.session.add(new_user)
            db.session.commit()

            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('user.authorization'))

        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.', 'danger')
            return redirect(url_for('user.registration'))

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return render_template('registration.html', form=form)


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
            return redirect(url_for('user.authorization'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('authorization.html', title='Sign In', form=form)

@user_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('user.authorization'))

@user_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        # Здесь должна быть логика отправки email
        # Например: send_password_reset_email(form.email.data)
        # отправлять на почту ссылку на вход без пароля - ссылка сразу на лк смену пароля, просто голым текстом, красоту потом можно сделать

        flash('Ссылка для восстановления пароля отправлена на вашу почту', 'success')
        return render_template('forgot_password.html', form=form, success=True)

    return render_template('forgot_password.html', form=form, success=False)




