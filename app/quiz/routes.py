from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.quiz import bp
from app.models import Question, Team, AnswerLog
from app.quiz.forms import AnswerForm
from thefuzz import fuzz

@bp.route('/')
@login_required
def index():
    if not current_user.is_moderator:
        flash('Access denied. Moderator privileges required.')
        return redirect(url_for('auth.login'))
    return render_template('quiz/index.html', title='Quiz Dashboard')

@bp.route('/question/<int:id>', methods=['GET', 'POST'])
@login_required
def question(id):
    if not current_user.is_moderator:
        flash('Access denied. Moderator privileges required.')
        return redirect(url_for('auth.login'))
    
    question = Question.query.get_or_404(id)
    form = AnswerForm()
    
    if form.validate_on_submit():
        team = Team.query.get(question.assigned_to)
        is_correct = False
        
        if question.type == 'TrueFalse':
            is_correct = form.answer.data == question.correct
        elif question.type == 'MultipleChoice':
            is_correct = form.answer.data == question.correct
        else:  # OpenEnded
            # Use fuzzy matching for open-ended questions
            similarity = fuzz.ratio(form.answer.data.lower(), question.correct.lower())
            is_correct = similarity >= 80  # 80% similarity threshold
        
        if is_correct:
            team.score += question.points
            db.session.commit()
        
        # Log the answer
        answer_log = AnswerLog(
            question_id=question.id,
            team_id=team.id,
            answer_text=form.answer.data,
            is_correct=is_correct
        )
        db.session.add(answer_log)
        db.session.commit()
        
        # Get next question
        next_question = Question.query.filter(Question.id > id).first()
        if next_question:
            return redirect(url_for('quiz.question', id=next_question.id))
        else:
            return redirect(url_for('results.show'))
    
    return render_template('quiz/question.html', 
                         title=f'Question {id}',
                         question=question,
                         form=form)

@bp.route('/scoreboard')
@login_required
def scoreboard():
    teams = Team.query.all()
    return render_template('quiz/scoreboard.html', title='Scoreboard', teams=teams)

@bp.route('/api/scoreboard')
def api_scoreboard():
    teams = Team.query.all()
    return jsonify([{
        'id': team.id,
        'name': team.name,
        'score': team.score
    } for team in teams]) 