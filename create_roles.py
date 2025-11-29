from app import create_app, db
from app.models import Roles


def create_initial_roles():
    app = create_app()
    with app.app_context():
        # Проверяем, есть ли уже роли
        if Roles.query.first() is None:
            roles = [
                Roles(title='participant', display_name='Участник', access=True),
                Roles(title='jury_candidate', display_name='Член жюри', access=True),
                Roles(title='jury', display_name='Подтвержденный член жюри', access=False),
            ]

            for role in roles:
                db.session.add(role)

            db.session.commit()
            print("Роли успешно созданы!")
        else:
            print("Роли уже существуют")


if __name__ == '__main__':
    create_initial_roles()