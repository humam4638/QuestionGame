from app import create_app, db
from app.models import User, Question, Team, AnswerLog

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Question': Question,
        'Team': Team,
        'AnswerLog': AnswerLog
    }

if __name__ == '__main__':
    app.run(debug=True) 