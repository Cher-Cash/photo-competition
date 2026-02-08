from functools import wraps
from flask import session, redirect, url_for, flash
from flask_login import current_user, logout_user


def active_user_required(f):
    """
    Декоратор для проверки статуса пользователя.
    Если статус не 'active', пользователь разлогинивается.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if not current_user.is_authenticated:
            return f(*args, **kwargs)

        # Проверяем статус пользователя
        if hasattr(current_user, 'status') and current_user.status != 'active':
            # Сохраняем email для возможного отображения сообщения
            user_email = current_user.email if hasattr(current_user, 'email') else None

            # Разлогиниваем пользователя
            logout_user()

            # Очищаем сессию, если нужно
            session.clear()

            # Показываем сообщение в зависимости от статуса
            if hasattr(current_user, 'status'):
                if current_user.status == 'pending':
                    flash('Ваш аккаунт ожидает подтверждения email. Пожалуйста, завершите регистрацию.', 'warning')
                elif current_user.status == 'blocked':
                    flash('Ваш аккаунт заблокирован. Обратитесь к администратору.', 'error')
                elif current_user.status == 'suspended':
                    flash('Ваш аккаунт временно приостановлен.', 'warning')
                else:
                    flash('Ваш аккаунт неактивен. Пожалуйста, обратитесь к администратору.', 'error')
            else:
                flash('Ошибка доступа к аккаунту. Пожалуйста, войдите снова.', 'error')

            # Перенаправляем на страницу входа
            return redirect(url_for('user.authorization'))

        if not current_user.email_confirmed:
            flash('Ваш аккаунт ожидает подтверждения email. Пожалуйста, завершите регистрацию.')


        return f(*args, **kwargs)

    return decorated_function
