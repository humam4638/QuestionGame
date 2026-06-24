from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_moderator = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    type = db.Column(db.Enum('TrueFalse', 'MultipleChoice', 'OpenEnded'), nullable=False)
    options = db.Column(db.JSON)  # for MultipleChoice
    correct = db.Column(db.JSON, nullable=False)
    assigned_to = db.Column(db.Enum('Team1', 'Team2'), nullable=False)
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