from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime
import os
import json
import random

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)

# Models
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    type = db.Column(db.Enum('TrueFalse', 'MultipleChoice', 'OpenEnded'), nullable=False)
    options = db.Column(db.JSON)  # for MultipleChoice
    correct = db.Column(db.String(500), nullable=False)
    assigned_to = db.Column(db.Enum('Team1', 'Team2'), nullable=True)
    points = db.Column(db.Integer, default=1)

class Team(db.Model):
    id = db.Column(db.Enum('Team1', 'Team2'), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    score = db.Column(db.Integer, default=0)

class AnswerLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    team_id = db.Column(db.Enum('Team1', 'Team2'), db.ForeignKey('team.id'), nullable=False)
    answer_text = db.Column(db.String(500))
    is_correct = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Forms
class QuestionForm(FlaskForm):
    text = TextAreaField('Question Text', validators=[DataRequired()])
    type = SelectField('Question Type', 
                      choices=[('TrueFalse', 'True/False'),
                              ('MultipleChoice', 'Multiple Choice'),
                              ('OpenEnded', 'Open-ended')],
                      validators=[DataRequired()])
    options = StringField('Options (comma-separated for Multiple Choice)')
    correct = StringField('Correct Answer', validators=[DataRequired()])
    assigned_to = SelectField('Assigned Team',
                            choices=[('Team1', 'Team 1'),
                                    ('Team2', 'Team 2')],
                            validators=[DataRequired()])
    points = IntegerField('Points', 
                         validators=[DataRequired(),
                                   NumberRange(min=1, max=10)],
                         default=1)
    submit = SubmitField('Save Question')

class AnswerForm(FlaskForm):
    answer = StringField('Your Answer', validators=[DataRequired()])
    submit = SubmitField('Submit Answer')

# Routes
@app.route('/')
def index():
    return redirect(url_for('quiz_dashboard'))

@app.route('/quiz')
def quiz_dashboard():
    questions = Question.query.all()
    teams = Team.query.all()
    return render_template('quiz_dashboard.html', title='Quiz Dashboard', 
                         questions=questions, teams=teams)

@app.route('/questions')
def manage_questions():
    questions = Question.query.all()
    return render_template('manage_questions.html', title='Manage Questions', questions=questions)

@app.route('/questions/add', methods=['GET', 'POST'])
def add_question():
    form = QuestionForm()
    if form.validate_on_submit():
        options = None
        if form.type.data == 'MultipleChoice' and form.options.data:
            options = [opt.strip() for opt in form.options.data.split(',')]
        
        question = Question(
            text=form.text.data,
            type=form.type.data,
            options=options,
            correct=form.correct.data
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('manage_questions'))
    
    return render_template('add_question.html', title='Add Question', form=form)

@app.route('/questions/<int:id>/edit', methods=['GET', 'POST'])
def edit_question(id):
    question = Question.query.get_or_404(id)
    form = QuestionForm(obj=question)
    
    if form.validate_on_submit():
        options = None
        if form.type.data == 'MultipleChoice' and form.options.data:
            options = [opt.strip() for opt in form.options.data.split(',')]
        
        question.text = form.text.data
        question.type = form.type.data
        question.options = options
        question.correct = form.correct.data
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('manage_questions'))
    
    return render_template('edit_question.html', title='Edit Question', form=form)

@app.route('/questions/<int:id>/delete', methods=['POST'])
def delete_question(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('manage_questions'))

@app.route('/quiz/question/<int:index>', methods=['GET', 'POST'])
def question(index):
    quiz_questions = session.get('quiz_questions', [])
    if not quiz_questions:
        flash('Quiz session not found. Please start a new quiz.', 'danger')
        return redirect(url_for('quiz_dashboard'))
    if index >= len(quiz_questions):
        return redirect(url_for('results'))
    
    question_id = quiz_questions[index]
    question = Question.query.get_or_404(question_id)
    form = AnswerForm()
    teams = Team.query.all()

    # Determine team and phase
    if index < 10:
        current_team = 'Team1'
        round_name = "Multiple Choice"
        timer_seconds = session.get('timer_mc', 180)
    elif index < 20:
        current_team = 'Team2'
        round_name = "Multiple Choice"
        timer_seconds = session.get('timer_mc', 180)
    elif index < 30:
        current_team = 'Team1'
        round_name = "True/False"
        timer_seconds = session.get('timer_tf', 180)
    elif index < 40:
        current_team = 'Team2'
        round_name = "True/False"
        timer_seconds = session.get('timer_tf', 180)
    elif index < 45:
        current_team = 'Team1'
        round_name = "Open-Ended"
        timer_seconds = session.get('timer_oe', 180)
    else:
        current_team = 'Team2'
        round_name = "Open-Ended"
        timer_seconds = session.get('timer_oe', 180)

    # Update the question's assigned_to field to match the current team
    question.assigned_to = current_team
    db.session.commit()

    # Handle moderator action BEFORE form validation
    if request.method == 'POST' and request.form.get('mod_action') == 'incorrect':
        team = Team.query.get(current_team)
        answer_log = AnswerLog(
            question_id=question.id,
            team_id=team.id,
            answer_text='[MODERATOR MARKED INCORRECT]',
            is_correct=False
        )
        db.session.add(answer_log)
        db.session.commit()
        session['quiz_index'] = index + 1
        if index + 1 < len(quiz_questions):
            return redirect(url_for('question', index=index+1))
        else:
            return redirect(url_for('results'))

    if form.validate_on_submit():
        team = Team.query.get(current_team)
        is_correct = False
        if question.type == 'TrueFalse':
            is_correct = form.answer.data.lower() == question.correct.lower()
        elif question.type == 'MultipleChoice':
            is_correct = form.answer.data == question.correct
        else:  # OpenEnded
            from thefuzz import fuzz
            similarity = fuzz.ratio(form.answer.data.lower(), question.correct.lower())
            is_correct = similarity >= 80
        if is_correct:
            team.score += 1
            db.session.commit()
        answer_log = AnswerLog(
            question_id=question.id,
            team_id=team.id,
            answer_text=form.answer.data,
            is_correct=is_correct
        )
        db.session.add(answer_log)
        db.session.commit()
        session['quiz_index'] = index + 1
        if index + 1 < len(quiz_questions):
            return redirect(url_for('question', index=index+1))
        else:
            return redirect(url_for('results'))
    
    return render_template('question.html', 
                         title=f'Question {index+1}',
                         question=question,
                         form=form,
                         teams=teams,
                         current_team=current_team,
                         round_name=round_name,
                         question_number=index+1,
                         total_questions=len(quiz_questions),
                         timer_seconds=timer_seconds)

@app.route('/scoreboard')
def scoreboard():
    teams = Team.query.all()
    return render_template('scoreboard.html', title='Scoreboard', teams=teams)

@app.route('/api/scoreboard')
def api_scoreboard():
    teams = Team.query.all()
    return jsonify([{
        'id': team.id,
        'name': team.name,
        'score': team.score
    } for team in teams])

@app.route('/results')
def results():
    teams = Team.query.all()
    # Get the winning team
    winning_team = max(teams, key=lambda x: x.score)
    
    # Get answer statistics
    total_questions = AnswerLog.query.count()
    correct_answers = AnswerLog.query.filter_by(is_correct=True).count()
    
    return render_template('results.html',
                         title='Quiz Results',
                         teams=teams,
                         winning_team=winning_team,
                         total_questions=total_questions,
                         correct_answers=correct_answers)

@app.route('/reset', methods=['POST'])
def reset():
    # Reset all team scores
    teams = Team.query.all()
    for team in teams:
        team.score = 0
    # Clear answer logs
    AnswerLog.query.delete()
    db.session.commit()
    flash('Quiz has been reset!', 'success')
    return redirect(url_for('quiz_dashboard'))

@app.route('/populate_questions')
def populate_questions():
    # First, clear existing questions
    Question.query.delete()
    db.session.commit()
    
    # Read the JSON file
    with open('full_quiz_data_complete.json', 'r', encoding='utf-8') as file:
        quiz_data = json.load(file)
    
    questions_added = {'MultipleChoice': 0, 'TrueFalse': 0, 'OpenEnded': 0}
    
    # Iterate through each lecture/section
    for section, content in quiz_data.items():
        # Handle Multiple Choice questions
        if 'Multiple Choice' in content:
            for q in content['Multiple Choice']:
                question = Question(
                    text=q['question'],
                    type='MultipleChoice',
                    options=q['options'],
                    correct=q['answer']
                )
                db.session.add(question)
                questions_added['MultipleChoice'] += 1
        
        # Handle True/False questions
        for tf_key in ['True or False', 'True or False Set 1', 'True or False Set 2']:
            if tf_key in content:
                for q in content[tf_key]:
                    question = Question(
                        text=q['statement'],
                        type='TrueFalse',
                        options=['True', 'False'],
                        correct=str(q['answer']).lower()
                    )
                    db.session.add(question)
                    questions_added['TrueFalse'] += 1
        
        # Handle Open-ended questions
        if 'Open Ended Questions' in content:
            # Get all open-ended questions from different categories
            open_ended_questions = []
            for category in content['Open Ended Questions'].values():
                if isinstance(category, list):
                    open_ended_questions.extend(category)
            
            for q in open_ended_questions:
                question = Question(
                    text=q['سؤال'] if 'سؤال' in q else q['question'],
                    type='OpenEnded',
                    options=None,
                    correct=q['جواب'] if 'جواب' in q else q['answer']
                )
                db.session.add(question)
                questions_added['OpenEnded'] += 1
    
    # Commit all questions to database
    db.session.commit()
    
    total_questions = sum(questions_added.values())
    flash(f'Successfully imported {total_questions} questions ({questions_added["MultipleChoice"]} Multiple Choice, {questions_added["TrueFalse"]} True/False, {questions_added["OpenEnded"]} Open-ended)!', 'success')
    
    return redirect(url_for('quiz_dashboard'))

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    # Reset all team scores
    teams = Team.query.all()
    for team in teams:
        team.score = 0
    db.session.commit()

    # Get questions by type
    mc_questions = Question.query.filter_by(type='MultipleChoice').all()
    tf_questions = Question.query.filter_by(type='TrueFalse').all()
    oe_questions = Question.query.filter_by(type='OpenEnded').all()

    # Check if we have enough questions
    if len(mc_questions) < 20 or len(tf_questions) < 20 or len(oe_questions) < 10:
        flash('Not enough questions of each type to start the quiz. Please add more questions.', 'danger')
        return redirect(url_for('quiz_dashboard'))

    # Shuffle questions
    random.shuffle(mc_questions)
    random.shuffle(tf_questions)
    random.shuffle(oe_questions)

    # Assign questions to teams
    team1_mc = mc_questions[:10]
    team2_mc = mc_questions[10:20]
    team1_tf = tf_questions[:10]
    team2_tf = tf_questions[10:20]
    team1_oe = oe_questions[:5]
    team2_oe = oe_questions[5:10]

    # Create ordered list of question IDs
    ordered_questions = (
        [q.id for q in team1_mc] +
        [q.id for q in team2_mc] +
        [q.id for q in team1_tf] +
        [q.id for q in team2_tf] +
        [q.id for q in team1_oe] +
        [q.id for q in team2_oe]
    )

    # Clear any existing quiz session
    session.pop('quiz_questions', None)
    session.pop('quiz_index', None)
    session.pop('quiz_team_scores', None)

    # Initialize new quiz session
    session['quiz_questions'] = ordered_questions
    session['quiz_index'] = 0
    session['quiz_team_scores'] = {'Team1': 0, 'Team2': 0}

    # Clear answer logs
    AnswerLog.query.delete()
    db.session.commit()

    flash('Quiz has been started with 50 random questions!', 'success')
    return redirect(url_for('question', index=0))

@app.route('/recreate_db')
def recreate_db():
    # Drop all tables
    db.drop_all()
    # Create all tables
    db.create_all()
    
    # Create default teams
    team1 = Team(id='Team1', name='Team 1')
    team2 = Team(id='Team2', name='Team 2')
    db.session.add(team1)
    db.session.add(team2)
    db.session.commit()
    
    flash('Database has been recreated successfully!', 'success')
    return redirect(url_for('quiz_dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        session['timer_mc'] = int(request.form.get('timer_mc', 180))
        session['timer_tf'] = int(request.form.get('timer_tf', 180))
        session['timer_oe'] = int(request.form.get('timer_oe', 180))
        flash('Timer settings updated!', 'success')
        return redirect(url_for('settings'))
    return render_template(
        'settings.html',
        title='Settings',
        timer_mc=session.get('timer_mc', 180),
        timer_tf=session.get('timer_tf', 180),
        timer_oe=session.get('timer_oe', 180)
    )

# Create database tables and add default teams
with app.app_context():
    db.create_all()
    
    # Create default teams if they don't exist
    if Team.query.count() == 0:
        team1 = Team(id='Team1', name='Team 1')
        team2 = Team(id='Team2', name='Team 2')
        db.session.add(team1)
        db.session.add(team2)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True) 