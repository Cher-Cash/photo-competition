import os
from flask import Blueprint, redirect, url_for, flash, render_template, current_app, abort, request, jsonify
from flask_login import current_user
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from datetime import datetime


from app.extansions import db
from app.models import Nominations, Roles, Ratings, Artworks, Competitions
from app.views.forms import SubmissionForm

application_bp = Blueprint("application", __name__)


@application_bp.route("/participate/<int:competition_id>", methods=["GET", "POST"])
def participate(competition_id):
    current_user_role = Roles.query.filter_by(id=current_user.role_id).first()
    if current_user_role.title != 'participant':
        abort(403)

    # Проверяем существование конкурса
    competition = Competitions.query.filter_by(id=competition_id, status="active").filter(
        Competitions.end_of_accepting > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).first()
    if not competition:
        flash('Конкурс не найден или не активен', 'error')
        return redirect(url_for('index'))

    form = SubmissionForm()

    # Получаем номинации только для этого конкурса
    nominations = Nominations.query.filter_by(
        competition_id=competition_id,
        status="active"
    ).all()

    form.nomination_id.choices = [(str(n.id), n.title) for n in nominations]

    if not nominations:
        flash('В выбранном конкурсе нет доступных номинаций', 'warning')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        nomination_id = int(form.nomination_id.data)

        # Проверяем, существует ли выбранная номинация и принадлежит ли она конкурсу
        nomination = Nominations.query.filter_by(
            id=nomination_id,
            competition_id=competition_id,
            status="active"
        ).first()

        if not nomination:
            flash('Выбранная номинация недоступна', 'error')
            return render_template('participate.html', form=form, competition=competition, nominations=nominations)

        # Проверяем, не превысил ли пользователь лимит заявок для этой номинации
        existing_submissions = Artworks.query.filter_by(
            user_id=current_user.id,
            nomination_id=nomination_id
        ).count()

        if existing_submissions >= 3:
            flash('Вы уже подали максимальное количество работ (3) для этой номинации', 'error')
            return render_template('participate.html', form=form, competition=competition, nominations=nominations)

        # Сохраняем файл
        photo = form.photo.data
        filename = secure_filename(photo.filename)
        upload_folder = os.getenv('UPLOAD_FOLDER', 'artworks')
        abs_upload_folder = os.path.join(current_app.root_path, upload_folder)
        if not os.path.exists(abs_upload_folder):
            os.makedirs(abs_upload_folder)

        file_path = os.path.join(abs_upload_folder, filename)

        if not os.access(abs_upload_folder, os.W_OK):
            flash('Ошибка доступа к папке для загрузки', 'error')
            return render_template('participate.html', form=form, competition=competition, nominations=nominations)

        photo.save(file_path)

        # Создаем заявку
        submission = Artworks(
            user_id=current_user.id,
            nomination_id=nomination_id,
            file=str(file_path),
            file_name=form.description.data,
            status='for moderation'
        )
        db.session.add(submission)
        db.session.commit()

        flash('Ваша заявка успешно отправлена на модерацию!', 'success')
        return redirect(url_for('index'))

    return render_template('participate.html', form=form, competition=competition, nominations=nominations)

@application_bp.route("/vote", methods=["GET", "POST"])
def jury_voting():
    current_user_role = Roles.query.filter_by(id=current_user.role_id).first()
    if current_user_role.title != 'jury':
        abort(403)

        # Получаем все работы для оценки с загрузкой связанных данных
    artworks = Artworks.query.options(
        joinedload(Artworks.author),
        joinedload(Artworks.nomination)
    ).filter_by(status="active").filter(Competitions.summing_up > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()

    # Получаем оценки текущего жюри
    user_ratings = Ratings.query.filter_by(juri_id=current_user.id).all()
    ratings_dict = {rating.work_id: rating for rating in user_ratings}

    # Добавляем информацию о оценках пользователя к работам
    for artwork in artworks:
        artwork.user_rating = ratings_dict.get(artwork.id)

    # Статистика
    total_artworks = len(artworks)
    rated_artworks = len(user_ratings)
    remaining_artworks = total_artworks - rated_artworks
    progress_percentage = round((rated_artworks / total_artworks) * 100) if total_artworks > 0 else 0

    return render_template('jury_voting.html',
                           artworks=artworks,
                           total_artworks=total_artworks,
                           rated_artworks=rated_artworks,
                           remaining_artworks=remaining_artworks,
                           progress_percentage=progress_percentage)


@application_bp.route("/jury/rate", methods=["GET", "POST"])
def rate_artwork():
    current_user_role = Roles.query.filter_by(id=current_user.role_id).first()
    if current_user_role.title != 'jury':
        abort(403)

    data = request.get_json()
    artwork_id = data.get('artwork_id')
    rating = data.get('rating')

    if not artwork_id or not rating:
        return jsonify({'success': False, 'message': 'Неверные данные'}), 400

    # Проверяем существование работы
    artwork = Artworks.query.get(artwork_id)
    if not artwork:
        return jsonify({'success': False, 'message': 'Работа не найдена'}), 404

    # Проверяем диапазон оценки
    if rating < 1 or rating > 10:
        return jsonify({'success': False, 'message': 'Оценка должна быть от 1 до 10'}), 400

    # Ищем существующую оценку
    existing_rating = Ratings.query.filter_by(
        work_id=artwork_id,
        juri_id=current_user.id
    ).first()

    if existing_rating:
        # Обновляем существующую оценку
        existing_rating.rate = rating
        message = 'Оценка обновлена'
    else:
        # Создаем новую оценку
        new_rating = Ratings(
            work_id=artwork_id,
            juri_id=current_user.id,
            rate=rating
        )
        db.session.add(new_rating)
        message = 'Оценка сохранена'

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Ошибка базы данных'}), 500
