from flask import url_for, render_template
from flask_mail import Message
from app import create_app, mail


def send_email(subject, recipients, text_body=None, html_body=None, sender=None):
    """
    Основная функция отправки email через Flask-Mail
    """
    # Если recipients - строка, преобразуем в список
    if isinstance(recipients, str):
        recipients = [recipients]

    # Создаем Flask приложение
    app = create_app()

    # Работаем в контексте приложения
    with app.app_context():
        # Создаем сообщение
        msg = Message(
            subject=subject,
            recipients=recipients,
            sender=sender or app.config.get('MAIL_DEFAULT_SENDER')
        )

        if text_body:
            msg.body = text_body
        if html_body:
            msg.html = html_body

        # Отправляем через Flask-Mail
        mail.send(msg)

        return True, "Email sent successfully"


def send_verification_email(user_email, user_name, verification_token):
    """Отправка письма для подтверждения email"""
    # Создаем Flask приложение
    app = create_app()

    with app.app_context():
        subject = "Подтверждение email - Фотоконкурс"

        # Генерируем URL
        verification_url = url_for(
            'user.verify_email',
            token=verification_token,
            _external=True
        )



        # HTML версия через шаблон
        html_body = render_template(
            'emails/email_verification.html',
            user_name=user_name,
            verification_url=verification_url
        )

        # Отправляем письмо
        return send_email(subject, user_email, html_body=html_body)


def send_password_reset_email(user_email, reset_token):
    """Отправка письма для сброса пароля"""
    app = create_app()

    with app.app_context():
        subject = "Восстановление пароля - Фотоконкурс"

        reset_link = f"http://localhost:5000/user/reset-password/{reset_token}"

        text_body = f"""
Для восстановления пароля перейдите по ссылке:
{reset_link}
Если вы не запрашивали сброс пароля, проигнорируйте это письмо.

С уважением,
Команда Фотоконкурса
"""

        html_body = render_template('emails/password_reset.html',
                                    reset_link=reset_link)

        return send_email(subject, user_email, text_body, html_body)