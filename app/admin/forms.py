from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

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