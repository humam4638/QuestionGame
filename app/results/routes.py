from flask import render_template, redirect, url_for
from flask_login import login_required
from app import db
from app.results import bp
from app.models import Team, AnswerLog

@bp.route('/show')
@login_required
def show():
    teams = Team.query.all()
    # Get the winning team
    winning_team = max(teams, key=lambda x: x.score)
    
    # Get answer statistics
    total_questions = AnswerLog.query.count()
    correct_answers = AnswerLog.query.filter_by(is_correct=True).count()
    
    return render_template('results/show.html',
                         title='Quiz Results',
                         teams=teams,
                         winning_team=winning_team,
                         total_questions=total_questions,
                         correct_answers=correct_answers)

@bp.route('/reset', methods=['POST'])
@login_required
def reset():
    # Reset all team scores
    teams = Team.query.all()
    for team in teams:
        team.score = 0
    db.session.commit()
    
    # Clear answer logs
    AnswerLog.query.delete()
    db.session.commit()
    
    return redirect(url_for('quiz.index')) 