from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import Question, Team
from app.admin.forms import QuestionForm

@bp.route('/questions')
@login_required
def questions():
    if not current_user.is_moderator:
        flash('Access denied. Moderator privileges required.')
        return redirect(url_for('auth.login'))
    questions = Question.query.all()
    return render_template('admin/questions.html', title='Manage Questions', questions=questions)

@bp.route('/questions/add', methods=['GET', 'POST'])
@login_required
def add_question():
    if not current_user.is_moderator:
        flash('Access denied. Moderator privileges required.')
        return redirect(url_for('auth.login'))
    
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            text=form.text.data,
            type=form.type.data,
            options=form.options.data if form.type.data == 'MultipleChoice' else None,
            correct=form.correct.data,
            assigned_to=form.assigned_to.data,
            points=form.points.data
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!')
        return redirect(url_for('admin.questions'))
    
    return render_template('admin/add_question.html', title='Add Question', form=form)

@bp.route('/questions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    if not current_user.is_moderator:
        flash('Access denied. Moderator privileges required.')
        return redirect(url_for('auth.login'))
    
    question = Question.query.get_or_404(id)
    form = QuestionForm(obj=question)
    
    if form.validate_on_submit():
        question.text = form.text.data
        question.type = form.type.data
        question.options = form.options.data if form.type.data == 'MultipleChoice' else None
        question.correct = form.correct.data
        question.assigned_to = form.assigned_to.data
        question.points = form.points.data
        db.session.commit()
        flash('Question updated successfully!')
        return redirect(url_for('admin.questions'))
    
    return render_template('admin/edit_question.html', title='Edit Question', form=form)

@bp.route('/questions/<int:id>/delete', methods=['POST'])
@login_required
def delete_question(id):
    if not current_user.is_moderator:
        flash('Access denied. Moderator privileges required.')
        return redirect(url_for('auth.login'))
    
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!')
    return redirect(url_for('admin.questions')) 