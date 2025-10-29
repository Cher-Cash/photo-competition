import os
from flask import Blueprint, redirect, url_for, flash, render_template, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename


from app.extansions import db
from app.models import Artworks, Nominations, Roles
from app.views.forms import SubmissionForm

application_bp = Blueprint("application", __name__)


@application_bp.route("/participate", methods=["GET", "POST"])
def participate():
    current_user_role = Roles.query.filter_by(id=current_user.role_id).first()
    if current_user_role.title != 'participant':
        flash('Только участники могут подавать заявки', 'error')
        return redirect(url_for('index'))

    form = SubmissionForm()

    nominations = Nominations.query.filter_by(status="active").all()
    form.nomination_id.choices = [(str(n.id), n.title) for n in nominations]

    if not nominations:
        flash('В настоящее время нет доступных номинаций для участия', 'warning')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        nomination = Nominations.query.get(int(form.nomination_id.data))
        if not nomination:
            flash('Выбранная номинация недоступна', 'error')
            return render_template('participate.html', form=form)

        photo = form.photo.data
        filename = secure_filename(photo.filename)
        upload_folder = os.getenv('UPLOAD_FOLDER', 'artworks')
        abs_upload_folder = os.path.join(current_app.root_path, upload_folder)
        if not os.path.exists(abs_upload_folder):
            os.makedirs(abs_upload_folder)

        file_path = os.path.join(abs_upload_folder, filename)

        if not os.access(abs_upload_folder, os.W_OK):
            return render_template('submit_work.html', form=form)

        photo.save(file_path)
        submission = Artworks(
            user_id=current_user.id,
            nomination_id=int(form.nomination_id.data),
            file=str(file_path),
            file_name=form.description.data,
            status='for moderation'
        )
        db.session.add(submission)
        db.session.commit()

        flash('Ваша заявка успешно отправлена на модерацию!', 'success')
        return redirect(url_for('index'))

    return render_template('participate.html', form=form, nominations=nominations)
