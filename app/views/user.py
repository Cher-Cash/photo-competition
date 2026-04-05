from flask import Blueprint, request, redirect, url_for, flash, render_template, abort
from flask_login import current_user, login_user, logout_user
from redis import Redis
from rq import Queue
import sqlalchemy as sa

from app.extensions import db
from app.models import Users, Roles
from app.views.forms import LoginForm, ForgotPasswordForm, RegistrationForm, ResetPasswordForm, EditProfileForm
from app.tasks import send_verification_email, send_password_reset_email
from app.utils.user_verification import active_user_required
from app.services.user_service import NewUser, UserService, UserExist, UserDbError

user_bp = Blueprint("user", __name__)
q = Queue(connection=Redis())


@user_bp.route("/registration", methods=["GET", "POST"])
def registration():
    form = RegistrationForm()

    if form.validate_on_submit():
        new_user = NewUser(
        email = form.email.data,
        password = form.password.data,
        f_name = form.name.data,
        s_name = form.second_name.data,
        age = form.age.data,
        role_id = form.role_id.data,
        about = form.about.data
        )
        user_service = UserService(db)
        try:
            user = user_service.create_user(new_user)
        except UserExist:
            flash('Пользователь с таким email уже зарегистрирован', 'danger')
            return redirect(url_for('user.registration'))
        except UserDbError:
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.', 'danger')
            return redirect(url_for('user.registration'))

        q.enqueue(send_verification_email, user.email, user.f_name, user.verification_token)
        flash('Регистрация прошла успешно! На вашу почту отправлено письмо с подтверждением.', 'success')
        return render_template('verification_pending.html', email=user.email)



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

            q.enqueue(send_verification_email, user.email, user.f_name, user.verification_token)

            flash('Ссылка подтверждения истекла. На вашу почту отправлена новая ссылка.', 'warning')
            return render_template('verification_pending.html', email=user.email)

        # Меняем статус пользователя на "активный"
        user.status = 'active'
        user.email_confirmed = True
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
        q.enqueue(send_verification_email, user.email, user.f_name, user.verification_token)


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
            sa.select(Users).where(form.email.data == Users.email))

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

            q.enqueue(send_password_reset_email, user.email, reset_token)

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


@user_bp.route("/profile", methods=["GET"])
@active_user_required
def profile():
    if not current_user.is_authenticated:
        abort(403)
    user = Users.query.filter_by(id=current_user.id).first()
    role = Roles.query.filter_by(id=user.role_id).first()
    return render_template('user_profile.html', user=user, role=role.display_name)


@user_bp.route("/edit-profile", methods=["GET", "POST"])
@active_user_required
def edit_profile():
    form = EditProfileForm()
    if not current_user.is_authenticated:
        abort(403)
    if request.method == 'GET':
        form.f_name.data = current_user.f_name
        form.s_name.data = current_user.s_name
        form.age.data = current_user.age
        form.email.data = current_user.email

    if form.validate_on_submit():
        try:
            email_changed = form.email.data != current_user.email

            # Обновляем данные
            current_user.f_name = form.f_name.data
            current_user.s_name = form.s_name.data
            current_user.age = form.age.data
            current_user.about_user = request.form.get('about_user', '').strip()

            if email_changed:
                # Логика смены email с подтверждением
                current_user.email = form.email.data
                current_user.email_confirmed = False
                current_user.generate_verification_token()

                q.enqueue(send_verification_email, current_user.email, current_user.f_name, current_user.verification_token)
                flash('Email изменен. На новый адрес отправлено письмо для подтверждения.', 'warning')
            else:
                flash('Профиль успешно обновлен!', 'success')

            db.session.commit()
            return redirect(url_for('user.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'error')

    return render_template('edit_profile.html', form=form)
