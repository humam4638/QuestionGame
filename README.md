# Quiz Competition App

A simple web-based quiz system where two teams compete by answering questions. The app features a moderator interface for managing questions and controlling the quiz flow.

## Features

- Question Management (True/False, Multiple Choice, Open-ended)
- Team-based scoring
- Real-time scoreboard
- Fuzzy matching for open-ended answers
- Moderator controls

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with:
```
SECRET_KEY=your-secret-key-here
```

3. Run the application:
```bash
python app.py
```

4. Create a moderator user:
```bash
python
>>> from app import db, User
>>> user = User(username='admin', email='admin@example.com', is_moderator=True)
>>> user.set_password('your-password')
>>> db.session.add(user)
>>> db.session.commit()
>>> exit()
```

The application will be available at `http://localhost:5000`

## Usage

1. Log in as a moderator
2. Add questions through the admin interface
3. Start the quiz
4. Control the quiz flow and confirm answers
5. View results at the end 