from flask_mail import Message
from flask import current_app, render_template, url_for
from threading import Thread
from app import mail


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print("Письмо успешно отправлено")
        except Exception as e:
            print(f"Ошибка отправки письма: {str(e)}")


def send_email(subject, recipients, text_body=None, html_body=None, sender=None):
    """
    Основная функция отправки email

    :param subject: Тема письма
    :param recipients: Список получателей или один получатель
    :param text_body: Текстовая версия письма
    :param html_body: HTML версия письма
    :param sender: Отправитель (если не указан, используется default)
    """
    app = current_app._get_current_object()

    # Если recipients - строка, преобразуем в список
    if isinstance(recipients, str):
        recipients = [recipients]

    msg = Message(
        subject=subject,
        recipients=recipients,
        sender=sender or current_app.config['MAIL_DEFAULT_SENDER']
    )

    if text_body:
        msg.body = text_body
    if html_body:
        msg.html = html_body

    # Запускаем в отдельном потоке для асинхронной отправки
    thread = Thread(target=send_async_email, args=[app, msg])
    thread.start()

    return thread


def send_verification_email(user_email, user_name, verification_token):
    """Отправка письма для подтверждения email"""
    subject = "Подтверждение email - Фотоконкурс"

    verification_url = url_for('user.verify_email', token=verification_token, _external=True)

    text_body = f"""
    Здравствуйте, {user_name}!

    Для подтверждения вашего email адреса перейдите по ссылке:
    {verification_url}

    Ссылка действительна в течение 60 минут.

    Если вы не регистрировались на нашем сайте, проигнорируйте это письмо.

    С уважением,
    Команда Фотоконкурса
    """

    html_body = render_template('emails/email_verification.html',
                                user_name=user_name,
                                verification_url=verification_url)

    send_email(subject, user_email, text_body, html_body)


def send_password_reset_email(user_email, reset_token):
    """Отправка письма для сброса пароля"""
    subject = "Восстановление пароля - Фотоконкурс"

    reset_link = f"https://yourdomain.com/user/reset-password/{reset_token}"

    text_body = f"""
    Для восстановления пароля перейдите по ссылке:
    {reset_link}

    Если вы не запрашивали сброс пароля, проигнорируйте это письмо.

    С уважением,
    Команда Фотоконкурса
    """

    html_body = render_template('emails/password_reset.html',
                                reset_link=reset_link)

    send_email(subject, user_email, text_body, html_body)


def send_contact_email(name, email, message):
    """Отправка письма из формы обратной связи"""
    subject = f"Новое сообщение от {name}"

    text_body = f"""
    Имя: {name}
    Email: {email}

    Сообщение:
    {message}
    """

    # Отправляем себе копию сообщения
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@yourdomain.com')
    send_email(subject, admin_email, text_body)