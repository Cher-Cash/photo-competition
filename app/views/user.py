from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import current_user, login_user, logout_user
import sqlalchemy as sa

from app.extansions import db
from app.models import Users
from app.views.forms import LoginForm, ForgotPasswordForm, RegistrationForm, ResetPasswordForm
from app.utils.email import send_password_reset_email, send_verification_email

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
        about = form.about.data


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
                role=role,
                about_user=about,
                status='pending'
            )
            new_user.generate_verification_token()
            db.session.add(new_user)
            db.session.commit()

            send_verification_email(email, f_name, new_user.verification_token)

            flash('Регистрация прошла успешно! На вашу почту отправлено письмо с подтверждением.', 'success')
            return render_template('verification_pending.html', email=email)

        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.', 'danger')
            return redirect(url_for('user.registration'))

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return render_template('registration.html', form=form)


@user_bp.route('/verify-email/<token>')
def verify_email(token):
    """Подтверждение email адреса"""
    try:
        # Ищем пользователя по токену
        user = Users.query.filter_by(verification_token=token).first()

        if not user:
            flash('Неверная ссылка подтверждения', 'danger')
            return redirect(url_for('user.registration'))

        # Проверяем срок действия токена
        if user.is_verification_token_expired():
            # Генерируем новый токен и отправляем новое письмо
            user.generate_verification_token()
            db.session.commit()

            send_verification_email(user.email, user.f_name, user.verification_token)

            flash('Ссылка подтверждения истекла. На вашу почту отправлена новая ссылка.', 'warning')
            return render_template('verification_pending.html', email=user.email)

        # Меняем статус пользователя на "активный"
        user.status = 'active'
        user.verification_token = None  # Удаляем использованный токен
        db.session.commit()

        flash('✅ Ваш email успешно подтвержден! Теперь вы можете войти в систему.', 'success')
        return redirect(url_for('user.authorization'))

    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при подтверждении email', 'danger')
        return redirect(url_for('user.registration'))


@user_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Повторная отправка письма с подтверждением"""
    email = request.form.get('email')

    if not email:
        flash('Email не указан', 'danger')
        return redirect(url_for('user.registration'))

    user = Users.query.filter_by(email=email).first()

    if not user:
        flash('Пользователь с таким email не найден', 'danger')
        return redirect(url_for('user.registration'))

    # Проверяем статус пользователя
    if user.status == 'active':
        flash('Email уже подтвержден. Вы можете войти в систему.', 'info')
        return redirect(url_for('user.authorization'))

    try:
        # Генерируем новый токен
        user.generate_verification_token()
        db.session.commit()

        # Отправляем письмо
        send_verification_email(user.email, user.f_name, user.verification_token)

        flash('Новое письмо с подтверждением отправлено на ваш email', 'success')
        return render_template('verification_pending.html', email=user.email)

    except Exception as e:
        db.session.rollback()
        flash('Ошибка при отправке письма', 'danger')
        return redirect(url_for('user.registration'))


@user_bp.route("/authorization", methods=["GET", "POST"])
def authorization():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(Users).where(Users.email == form.email.data))

        if user is None or not user.check_password(form.password.data):
            flash('Неверный email или пароль', 'danger')
            return redirect(url_for('user.authorization'))

        # Проверяем статус пользователя
        if user.status == 'pending':
            flash('Подтвердите ваш email адрес для входа в систему. Проверьте вашу почту.', 'warning')
            return render_template('verification_pending.html', email=user.email)

        elif user.status == 'banned':
            flash('Ваш аккаунт заблокирован. Обратитесь к администратору.', 'danger')
            return redirect(url_for('user.authorization'))

        elif user.status == 'inactive':
            flash('Ваш аккаунт деактивирован. Обратитесь к администратору.', 'warning')
            return redirect(url_for('user.authorization'))

        elif user.status == 'active':
            # Успешная авторизация для активного пользователя
            login_user(user, remember=form.remember_me.data)

            # Опционально: можно добавить логирование входа
            flash('Вы успешно вошли в систему!', 'success')

            # Редирект на следующую страницу или на индекс
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)

        else:
            # Для любых других статусов
            flash('Аккаунт не активирован. Обратитесь к администратору.', 'warning')
            return redirect(url_for('user.authorization'))

    return render_template('authorization.html', title='Sign In', form=form)

@user_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('user.authorization'))


@user_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()

        if user:
            # Используем универсальный метод
            reset_token = user.generate_token('password_reset')
            db.session.commit()

            send_password_reset_email(user.email, reset_token)

        flash('Если пользователь с таким email существует, ссылка для восстановления пароля будет отправлена',
              'success')
        return render_template('forgot_password.html', form=form, success=True)

    return render_template('forgot_password.html', form=form, success=False)


@user_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Страница сброса пароля по токену"""
    # Ищем пользователя по токену
    user = Users.query.filter_by(reset_password_token=token).first()

    if not user:
        flash('Неверная или устаревшая ссылка для сброса пароля', 'danger')
        return redirect(url_for('user.forgot_password'))

    # Проверяем срок действия токена
    if user.is_token_expired('password_reset', 1):
        flash('Ссылка для сброса пароля истекла. Запросите новую.', 'danger')
        return redirect(url_for('user.forgot_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        try:
            # Меняем пароль
            hashed_password = Users.set_password(form.password.data)
            user.password_hash = hashed_password

            # Очищаем токен
            user.reset_password_token = None
            user.reset_password_sent_at = None

            db.session.commit()

            # Авторизуем пользователя
            login_user(user)

            flash('Пароль успешно изменен! Вы авторизованы в системе.', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash('Ошибка при изменении пароля. Пожалуйста, попробуйте еще раз.', 'danger')
            # Важно: возвращаем render_template даже при ошибке
            return render_template('reset_password.html', form=form, token=token)

    # Возвращаем шаблон для GET запроса или невалидной формы
    return render_template('reset_password.html', form=form, token=token)



